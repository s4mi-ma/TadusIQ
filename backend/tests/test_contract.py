import base64
import json

import pytest
from pydantic import ValidationError

from app.canonical import BadPackage, canonical_bytes, decode_manifest, decode_signature
from app.schemas import Manifest


def sample_manifest():
    return {
        "schema_version": 1, "laboratory_id": "LAB-A", "file_name": "synthetic.txt",
        "file_sha256": "0" * 64, "file_size_bytes": 3,
        "signed_at": "2026-10-26T12:00:00Z", "key_id": "demo-key",
        "metadata": {"sample_id": "SYN-001", "collected_at": "2026-10-26T11:00:00Z",
                     "data_type": "txt", "synthetic": True},
    }


def test_canonical_contract_preserves_signed_values():
    value = sample_manifest()
    reverse = dict(reversed(list(value.items())))
    encoded = canonical_bytes(value)
    assert canonical_bytes(reverse) == encoded
    assert encoded.startswith(b'{"file_name":"synthetic.txt","file_sha256":')
    assert b' ' not in encoded and not encoded.endswith(b'\n')
    assert decode_manifest(encoded) == value
    assert Manifest.model_validate(value).model_dump() == value


@pytest.mark.parametrize("raw", [
    b'{"a":1,"a":2}', b'{"outer":{"a":1,"a":2}}', b'{"a":NaN}',
    b'{"a":Infinity}', b'{"a":-Infinity}', b'\xff', b'\xef\xbb\xbf{}', b'{',
])
def test_malformed_json_never_passes(raw):
    with pytest.raises(BadPackage):
        decode_manifest(raw)


@pytest.mark.parametrize("field,value", [
    ("schema_version", True), ("schema_version", 1.0), ("schema_version", "1"),
    ("schema_version", 2), ("file_size_bytes", True), ("file_size_bytes", "3"),
    ("file_size_bytes", 0), ("file_size_bytes", 2097153),
    ("file_name", "../test.txt"), ("file_name", "fake.csv"),
    ("signed_at", "2026-02-30T12:00:00Z"), ("signed_at", "2026-10-26T12:00:00+00:00"),
    ("signed_at", "2026-10-26T10:00:00Z"), ("file_sha256", "A" * 64),
])
def test_invalid_manifest_fields(field, value):
    manifest = sample_manifest()
    manifest[field] = value
    with pytest.raises(ValidationError):
        Manifest.model_validate(manifest)


@pytest.mark.parametrize("value", [False, 1, "true"])
def test_synthetic_requires_literal_boolean_true(value):
    manifest = sample_manifest()
    manifest["metadata"]["synthetic"] = value
    with pytest.raises(ValidationError):
        Manifest.model_validate(manifest)


def test_missing_and_unknown_metadata_rejected():
    manifest = sample_manifest()
    del manifest["metadata"]["sample_id"]
    with pytest.raises(ValidationError):
        Manifest.model_validate(manifest)
    manifest = sample_manifest()
    manifest["metadata"]["extra"] = "ignored?"
    with pytest.raises(ValidationError):
        Manifest.model_validate(manifest)


def test_signature_encoding_is_exact_and_canonical():
    raw = bytes(64)
    encoded = base64.b64encode(raw)
    assert decode_signature(encoded) == raw
    for bad in (b'!!!', encoded + b'\n', encoded[:-1], base64.b64encode(bytes(63)),
                encoded[:-3] + b'B=='):
        with pytest.raises(BadPackage):
            decode_signature(bad)


def test_deeply_nested_json_rejected_safely():
    with pytest.raises(BadPackage):
        decode_manifest(b'[' * 2000 + b'0' + b']' * 2000)
