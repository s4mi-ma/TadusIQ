"""Bounded streaming multipart parsing with the established parser library."""

from python_multipart import MultipartParser
from python_multipart.exceptions import MultipartParseError
from python_multipart.multipart import parse_options_header
from starlette.requests import ClientDisconnect, Request

from .canonical import BadPackage, MAX_FILE_BYTES, MAX_MANIFEST_BYTES, MAX_REQUEST_BYTES


class PackageParts:
    def __init__(self):
        self.parts = {}
        self.count = 0
        self.finished = False
        self.filename = ""
        self.headers = {}
        self.field = bytearray()
        self.value = bytearray()
        self.body = bytearray()
        self.name = b""

    def on_part_begin(self):
        self.count += 1
        if self.count > 3:
            raise BadPackage("Exactly file, manifest and signature parts are required.")
        self.headers, self.field, self.value, self.body = {}, bytearray(), bytearray(), bytearray()
        self.name = b""

    def on_header_field(self, data, start, end):
        self.field.extend(data[start:end])

    def on_header_value(self, data, start, end):
        self.value.extend(data[start:end])

    def on_header_end(self):
        name = bytes(self.field).lower()
        if name in self.headers:
            raise BadPackage("Duplicate multipart headers are not allowed.")
        self.headers[name] = bytes(self.value)
        self.field, self.value = bytearray(), bytearray()

    def on_headers_finished(self):
        disposition, options = parse_options_header(self.headers.get(b"content-disposition"))
        self.name = options.get(b"name", b"")
        if disposition != b"form-data" or self.name not in (b"file", b"manifest", b"signature"):
            raise BadPackage("Unexpected multipart field.")
        if self.name in self.parts or b"content-transfer-encoding" in self.headers:
            raise BadPackage("Duplicate fields and transfer encodings are not supported.")
        if self.name == b"file":
            raw_name = options.get(b"filename", b"")
            try:
                self.filename = raw_name.decode("ascii")
            except UnicodeError as exc:
                raise BadPackage("The V1 filename must use ASCII characters.") from exc
            if not 1 <= len(self.filename) <= 120:
                raise BadPackage("A bounded filename is required for the file part.")
        elif b"filename" in options:
            raise BadPackage("Manifest and signature must be text form fields.")

    def on_part_data(self, data, start, end):
        limit = {b"file": MAX_FILE_BYTES, b"manifest": MAX_MANIFEST_BYTES, b"signature": 88}[self.name]
        if len(self.body) + end - start > limit:
            raise BadPackage("A package part exceeds its size limit.", 413, "TOO_LARGE")
        self.body.extend(data[start:end])

    def on_part_end(self):
        self.parts[self.name] = bytes(self.body)

    def on_end(self):
        self.finished = True


async def read_package(request: Request) -> tuple[bytes, str, bytes, bytes]:
    lengths = request.headers.getlist("content-length")
    if len(lengths) > 1:
        raise BadPackage("Multiple Content-Length headers are not supported.")
    if lengths:
        try:
            declared = int(lengths[0])
        except ValueError as exc:
            raise BadPackage("Invalid Content-Length.") from exc
        if declared < 0:
            raise BadPackage("Invalid Content-Length.")
        if declared > MAX_REQUEST_BYTES:
            raise BadPackage("Request exceeds 3 MiB.", 413, "TOO_LARGE")
    content_type = request.headers.get("content-type", "")
    if len(content_type) > 256:
        raise BadPackage("Content-Type header is too long.")
    media, options = parse_options_header(content_type)
    boundary = options.get(b"boundary", b"")
    if media.lower() != b"multipart/form-data" or not 1 <= len(boundary) <= 70:
        raise BadPackage("Expected multipart/form-data with a valid boundary.")
    if any(byte < 33 or byte > 126 for byte in boundary):
        raise BadPackage("Invalid multipart boundary.")
    state = PackageParts()
    names = ("on_part_begin", "on_header_field", "on_header_value", "on_header_end",
             "on_headers_finished", "on_part_data", "on_part_end", "on_end")
    parser = MultipartParser(boundary, {name: getattr(state, name) for name in names},
                             max_header_count=8, max_header_size=4096)
    total = 0
    try:
        async for chunk in request.stream():
            total += len(chunk)
            if total > MAX_REQUEST_BYTES:
                raise BadPackage("Request exceeds 3 MiB.", 413, "TOO_LARGE")
            parser.write(chunk)
        parser.finalize()
    except (MultipartParseError, ClientDisconnect) as exc:
        raise BadPackage("Malformed or interrupted multipart upload.") from exc
    # finalize() does not validate completeness in python-multipart 0.0.30.
    if not state.finished or set(state.parts) != {b"file", b"manifest", b"signature"}:
        raise BadPackage("The complete file, manifest and signature are required.")
    if lengths and total != declared:
        raise BadPackage("Content-Length does not match the received body.")
    return state.parts[b"file"], state.filename, state.parts[b"manifest"], state.parts[b"signature"]
