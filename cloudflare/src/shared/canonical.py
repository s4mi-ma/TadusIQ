"""Strict transport decoding and the restricted V1 JSON representation."""

import base64
import binascii
import json

MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_MANIFEST_BYTES = 8192
MAX_REQUEST_BYTES = 3 * 1024 * 1024


class BadPackage(Exception):
    def __init__(self, message: str, status: int = 400, code: str = "BAD_REQUEST"):
        super().__init__(message)
        self.message, self.status, self.code = message, status, code


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def _unique_pairs(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise BadPackage("Duplicate JSON keys are not allowed.")
        value[key] = item
    return value


def _reject_constant(_value):
    raise BadPackage("Non-finite JSON values are not allowed.")


def decode_manifest(raw: bytes) -> object:
    if len(raw) > MAX_MANIFEST_BYTES:
        raise BadPackage("Manifest exceeds 8 KiB.", 413, "TOO_LARGE")
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_pairs,
                           parse_constant=_reject_constant)
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise BadPackage("Manifest must be valid UTF-8 JSON without a BOM.") from exc
    pending = [(value, 0)]
    while pending:
        item, depth = pending.pop()
        if depth > 4:
            raise BadPackage("Manifest nesting exceeds the V1 limit.")
        if isinstance(item, dict):
            pending.extend((child, depth + 1) for child in item.values())
        elif isinstance(item, list):
            pending.extend((child, depth + 1) for child in item)
    return value


def decode_signature(raw: bytes) -> bytes:
    try:
        decoded = base64.b64decode(raw, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise BadPackage("Signature must be canonical standard base64.") from exc
    if len(decoded) != 64 or base64.b64encode(decoded) != raw:
        raise BadPackage("Signature must encode exactly 64 bytes in canonical base64.")
    return decoded
