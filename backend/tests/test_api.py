import asyncio
import base64
import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.canonical import MAX_FILE_BYTES, MAX_REQUEST_BYTES, canonical_bytes
from app.main import create_app
from test_verification import package


@pytest.fixture
def client(package):
    with TestClient(create_app(package[0]), raise_server_exceptions=False) as value:
        yield value


def request_parts(package):
    raw = canonical_bytes(package[3])
    return {"manifest": raw.decode(), "signature": base64.b64encode(package[1].sign(raw)).decode()}


@pytest.mark.parametrize("scenario,reason", [
    ("valid", "VALID"), ("tampered", "HASH_MISMATCH"),
    ("signature", "INVALID_SIGNATURE"), ("metadata", "INVALID_METADATA"),
])
def test_four_scenarios_through_real_endpoint(package, client, scenario, reason):
    if scenario == "metadata":
        del package[3]["metadata"]["sample_id"]
    fields = request_parts(package)
    data = package[2]
    if scenario == "tampered":
        data = b"X" + data[1:]
    if scenario == "signature":
        fields["signature"] = base64.b64encode(bytes(64)).decode()
    response = client.post("/api/verify", data=fields, files={"file": ("synthetic.txt", data, "text/plain")})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["reason_code"] == reason
    assert body["status"] == ("ACCEPTED" if scenario == "valid" else "QUARANTINED")
    assert client.get("/api/verifications/" + body["verification_id"]).json() == body
    assert len(client.get("/api/audit", params={"verification_id": body["verification_id"]}).json()) == 9


def test_registry_health_filters_and_no_private_material(client, package):
    assert client.get("/api/health").json()["status"] == "OK"
    assert len(client.get("/api/laboratories").json()) == 3
    assert client.get("/api/verifications?status=QUARANTINED").json() == []
    assert client.get("/api/verifications/missing").status_code == 404
    for url in ("/api/verifications?limit=999", "/api/audit?limit=-1", "/api/verifications?status=bogus"):
        assert client.get(url).status_code == 400
    response = client.post("/api/verify", data=request_parts(package), files={"file": ("synthetic.txt", package[2])})
    assert "private" not in response.text.lower()
    assert response.headers["cache-control"] == "no-store"
    assert client.post("/api/laboratories").status_code == 405


@pytest.mark.parametrize("change", ["json", "base64", "missing-file", "duplicate", "extra"])
def test_malformed_transport_never_accepted(client, package, change):
    fields = request_parts(package)
    files = [("file", ("synthetic.txt", package[2]))]
    if change == "json":
        fields["manifest"] = '{"a":1,"a":2}'
    elif change == "base64":
        fields["signature"] = "invalid!!"
    elif change == "missing-file":
        files = [("manifest", (None, fields.pop("manifest")))]
    elif change == "duplicate":
        files.append(("file", ("another.txt", b"text")))
    else:
        fields["extra"] = "unwanted"
    response = client.post("/api/verify", data=fields, files=files)
    assert response.status_code == 400 and "ACCEPTED" not in response.text
    assert client.get("/api/verifications").json() == []
    assert client.get("/api/audit").json()[0]["event_type"] == "BAD_REQUEST"


def test_oversized_parts(client, package):
    response = client.post("/api/verify", data=request_parts(package),
                           files={"file": ("synthetic.txt", b"x" * (MAX_FILE_BYTES + 1))})
    assert response.status_code == 413
    fields = request_parts(package)
    fields["manifest"] = " " * 8193
    assert client.post("/api/verify", data=fields, files={"file": ("a.txt", b"x")}).status_code == 413
    assert client.get("/api/verifications").json() == []


def test_truncated_multipart_is_rejected(client):
    raw = b'--b\r\nContent-Disposition: form-data; name="file"; filename="a.txt"\r\n\r\ndata'
    assert client.post("/api/verify", content=raw,
                       headers={"Content-Type": "multipart/form-data; boundary=b"}).status_code == 400


def test_multipart_header_limit(client):
    raw = b'--b\r\nX-Large: ' + b'x' * 5000 + b'\r\n\r\nbody\r\n--b--\r\n'
    response = client.post("/api/verify", content=raw,
                           headers={"Content-Type": "multipart/form-data; boundary=b"})
    assert response.status_code == 400


def test_unexpected_and_storage_errors_fail_closed(client, package, monkeypatch):
    import app.main as main
    def broken(*_args):
        raise RuntimeError("sensitive-detail-must-not-leak")
    monkeypatch.setattr(main, "verify_and_record", broken)
    response = client.post("/api/verify", data=request_parts(package), files={"file": ("synthetic.txt", package[2])})
    assert response.status_code == 500
    assert "sensitive-detail" not in response.text and "ACCEPTED" not in response.text
    assert client.get("/api/verifications").json() == []


def test_database_failure_never_returns_acceptance(client, package, monkeypatch):
    def broken(*_args):
        raise sqlite3.OperationalError("secret path")
    monkeypatch.setattr(package[0], "insert_audit", broken)
    response = client.post("/api/verify", data=request_parts(package), files={"file": ("synthetic.txt", package[2])})
    assert response.status_code == 503 and "ACCEPTED" not in response.text
    assert "secret path" not in response.text
    assert package[0].list_results() == []


def test_untrusted_browser_origin_is_rejected(client, package):
    response = client.post("/api/verify", data=request_parts(package),
                           files={"file": ("synthetic.txt", package[2])}, headers={"Origin": "https://attacker.invalid"})
    assert response.status_code == 403
    assert package[0].list_results() == []


@pytest.mark.parametrize("declared_length", [None, b"1"])
def test_stream_limit_without_trust_in_content_length(package, declared_length):
    app = create_app(package[0])
    output = []
    chunks = [b"x" * (MAX_REQUEST_BYTES + 1)]
    headers = [(b"host", b"testserver"), (b"content-type", b"multipart/form-data; boundary=b")]
    if declared_length:
        headers.append((b"content-length", declared_length))
    scope = {"type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1", "method": "POST",
             "scheme": "http", "path": "/api/verify", "raw_path": b"/api/verify", "query_string": b"",
             "root_path": "", "headers": headers, "server": ("testserver", 80), "client": ("127.0.0.1", 1)}
    async def receive():
        if chunks:
            return {"type": "http.request", "body": chunks.pop(), "more_body": False}
        return {"type": "http.disconnect"}
    async def send(message):
        output.append(message)
    asyncio.run(app(scope, receive, send))
    assert next(m["status"] for m in output if m["type"] == "http.response.start") == 413
