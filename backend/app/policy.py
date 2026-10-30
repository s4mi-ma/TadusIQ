"""Shared strict decision policy; crypto and persistence are runtime adapters."""
import hashlib
import re
from datetime import datetime, timezone
from uuid import uuid4
from pydantic import ValidationError
from .canonical import BadPackage, MAX_FILE_BYTES, canonical_bytes, decode_manifest, decode_signature
from .schemas import Check, Manifest, VerificationResult

CHECKS = ("metadata", "trusted_key", "sender", "signature", "file_name", "size", "sha256")
MESSAGES = {
    "VALID": "Signature, sender, metadata, file size and SHA-256 verified.",
    "INVALID_METADATA": "Required metadata is missing, inconsistent or not in the canonical V1 format.",
    "UNKNOWN_OR_REVOKED_KEY": "The signing key is unknown or inactive in the trust registry.",
    "SENDER_KEY_MISMATCH": "The signing key is not authorized for the claimed laboratory.",
    "INVALID_SIGNATURE": "The Ed25519 signature does not match the submitted manifest bytes.",
    "HASH_MISMATCH": "File bytes do not match the SHA-256 digest in the signed manifest.",
    "SIZE_MISMATCH": "File size does not match the signed manifest.",
}

def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")

class PreparedPackage:
    def __init__(self, data, filename, raw_manifest, signature_b64):
        if len(data) > MAX_FILE_BYTES:
            raise BadPackage("File exceeds 2 MiB.", 413, "TOO_LARGE")
        self.data, self.filename, self.raw_manifest = data, filename, raw_manifest
        self.value = decode_manifest(raw_manifest)
        self.signature = decode_signature(signature_b64)
        self.computed = hashlib.sha256(data).hexdigest()
        self.manifest = None
        try:
            self.manifest = Manifest.model_validate(self.value)
            self.valid_metadata = bool(data) and canonical_bytes(self.value) == raw_manifest
        except ValidationError:
            self.valid_metadata = False

    def can_verify(self, key):
        return (self.valid_metadata and key is not None and bool(key["active"])
                and key["laboratory_id"] == self.manifest.laboratory_id)

def _claim(value, field):
    candidate = value.get(field) if isinstance(value, dict) else None
    return candidate if isinstance(candidate, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,64}", candidate) else None

def decide(package, key, signature_valid):
    checks = {name: "SKIPPED" for name in CHECKS}
    manifest = package.manifest
    authenticated = False
    verified_lab = verified_key = None
    reason = "VALID"
    if not package.valid_metadata:
        reason, checks["metadata"] = "INVALID_METADATA", "FAIL"
    else:
        checks["metadata"] = "PASS"
        if key is None or not key["active"]:
            reason, checks["trusted_key"] = "UNKNOWN_OR_REVOKED_KEY", "FAIL"
        else:
            checks["trusted_key"] = "PASS"
            if key["laboratory_id"] != manifest.laboratory_id:
                reason, checks["sender"] = "SENDER_KEY_MISMATCH", "FAIL"
            else:
                checks["sender"] = "PASS"
                if not signature_valid:
                    reason, checks["signature"] = "INVALID_SIGNATURE", "FAIL"
                else:
                    checks["signature"] = "PASS"
                    authenticated = True
                    verified_lab, verified_key = manifest.laboratory_id, manifest.key_id
                    if package.filename != manifest.file_name:
                        reason, checks["file_name"] = "INVALID_METADATA", "FAIL"
                    else:
                        checks["file_name"] = "PASS"
                        if len(package.data) != manifest.file_size_bytes:
                            reason, checks["size"] = "SIZE_MISMATCH", "FAIL"
                        else:
                            checks["size"] = "PASS"
                            checks["sha256"] = "PASS" if package.computed == manifest.file_sha256 else "FAIL"
                            if checks["sha256"] == "FAIL":
                                reason = "HASH_MISMATCH"
    return VerificationResult(
        verification_id=str(uuid4()), received_at=utc_now(),
        status="ACCEPTED" if reason == "VALID" else "QUARANTINED", reason_code=reason,
        details=MESSAGES[reason], claimed_laboratory_id=_claim(package.value, "laboratory_id"),
        claimed_key_id=_claim(package.value, "key_id"), verified_laboratory_id=verified_lab,
        verified_key_id=verified_key, metadata_authenticated=authenticated,
        file_name=manifest.file_name if manifest else None, file_size_bytes=len(package.data),
        computed_sha256=package.computed, manifest=manifest,
        checks=[Check(name=name, status=state) for name, state in checks.items()],
    )
