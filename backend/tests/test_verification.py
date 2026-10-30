import base64
import hashlib
import sqlite3

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from app.canonical import canonical_bytes
from app.db import Database
from app.verification import verify_and_record
from test_contract import sample_manifest


@pytest.fixture
def package(tmp_path):
    db = Database(tmp_path / "audit.sqlite3")
    db.initialize()
    key = Ed25519PrivateKey.generate()
    db.register_key("demo-key", "LAB-A", key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw))
    data = b"Synthetic result only.\n"
    manifest = sample_manifest()
    manifest["file_sha256"] = hashlib.sha256(data).hexdigest()
    manifest["file_size_bytes"] = len(data)
    return db, key, data, manifest


def submit(package, *, data=None, manifest=None, signature=None, raw=None, filename=None):
    db, key, original_data, original_manifest = package
    manifest = original_manifest if manifest is None else manifest
    raw = canonical_bytes(manifest) if raw is None else raw
    signature = base64.b64encode(key.sign(raw)) if signature is None else signature
    return verify_and_record(db, original_data if data is None else data,
                             filename or manifest.get("file_name", "synthetic.txt"), raw, signature)


def test_valid_signature_and_persistence(package):
    result = submit(package)
    assert result.status == "ACCEPTED" and result.reason_code == "VALID"
    assert result.metadata_authenticated and result.verified_laboratory_id == "LAB-A"
    assert all(check.status == "PASS" for check in result.checks)
    reopened = Database(package[0].path)
    assert reopened.get_result(result.verification_id) == result
    events = reopened.list_audit(result.verification_id)
    assert len(events) == 9
    assert {e.event_type for e in events} >= {"PACKAGE_RECEIVED", "VERIFICATION_DECIDED"}


def test_tampered_file_with_valid_signature(package):
    result = submit(package, data=b"X" + package[2][1:])
    assert result.status == "QUARANTINED" and result.reason_code == "HASH_MISMATCH"
    assert result.metadata_authenticated


def test_bad_signature_is_not_authenticated(package):
    result = submit(package, signature=base64.b64encode(bytes(64)))
    assert result.reason_code == "INVALID_SIGNATURE"
    assert not result.metadata_authenticated and result.verified_key_id is None


def test_missing_metadata_quarantined(package):
    del package[3]["metadata"]["sample_id"]
    result = submit(package)
    assert result.reason_code == "INVALID_METADATA" and result.status == "QUARANTINED"
    assert package[0].get_result(result.verification_id) is not None


def test_manipulated_signed_manifest(package):
    original = base64.b64encode(package[1].sign(canonical_bytes(package[3])))
    package[3]["metadata"]["sample_id"] = "SYN-ALTERED"
    assert submit(package, signature=original).reason_code == "INVALID_SIGNATURE"


@pytest.mark.parametrize("kind", ["unknown", "revoked", "wrong-lab"])
def test_trust_failures(package, kind):
    db, key, _, manifest = package
    if kind == "unknown":
        manifest["key_id"] = "unknown-key"
    elif kind == "revoked":
        db.register_key("demo-key", "LAB-A", key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw), active=False)
    else:
        manifest["laboratory_id"] = "LAB-B"
    result = submit(package)
    expected = "SENDER_KEY_MISMATCH" if kind == "wrong-lab" else "UNKNOWN_OR_REVOKED_KEY"
    assert result.reason_code == expected and result.status == "QUARANTINED"
    assert result.verified_laboratory_id is None


def test_size_and_uploaded_filename_bound_to_manifest(package):
    assert submit(package, data=package[2] + b"extra").reason_code == "SIZE_MISMATCH"
    assert submit(package, filename="other.txt").reason_code == "INVALID_METADATA"


def test_noncanonical_bytes_not_normalized(package):
    assert submit(package, raw=canonical_bytes(package[3]) + b'\n').reason_code == "INVALID_METADATA"


def test_inconsistent_metadata_and_empty_upload(package):
    package[3]["metadata"]["collected_at"] = "2026-10-27T00:00:00Z"
    assert submit(package).reason_code == "INVALID_METADATA"
    assert submit(package, data=b"").status == "QUARANTINED"


def test_sql_like_input_cannot_modify_registry(package):
    package[3]["key_id"] = "'; DROP TABLE trusted_keys;--"
    assert submit(package).status == "QUARANTINED"
    assert len(package[0].list_laboratories()) == 3
    with package[0].connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM trusted_keys").fetchone()[0] == 1


def test_audit_failure_rolls_back_submission_and_result(package, monkeypatch):
    def fail(*_args):
        raise sqlite3.OperationalError("injected write failure")
    monkeypatch.setattr(package[0], "insert_audit", fail)
    with pytest.raises(sqlite3.OperationalError):
        submit(package)
    with package[0].connection() as connection:
        for table in ("submissions", "verification_results", "audit_events"):
            assert connection.execute("SELECT COUNT(*) FROM " + table).fetchone()[0] == 0


def test_parameter_binding_preserves_literal_audit_text(package):
    text = "'; DROP TABLE laboratories;--"
    package[0].record_transport_error("BAD_REQUEST", text)
    assert package[0].list_audit()[0].details == text
    assert len(package[0].list_laboratories()) == 3
