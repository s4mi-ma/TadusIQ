"""Local Ed25519 verification and transactional persistence."""
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from .db import Database
from .policy import PreparedPackage, decide
from .schemas import VerificationResult

def verify_and_record(db: Database, data: bytes, filename: str, raw_manifest: bytes,
                      signature_b64: bytes) -> VerificationResult:
    package = PreparedPackage(data, filename, raw_manifest, signature_b64)
    with db.transaction() as connection:
        key = db.lookup_key(connection, package.manifest.key_id) if package.valid_metadata else None
        signature_valid = False
        if package.can_verify(key):
            try:
                Ed25519PublicKey.from_public_bytes(key["public_key"]).verify(package.signature, raw_manifest)
            except InvalidSignature:
                pass
            else:
                signature_valid = True
        result = decide(package, key, signature_valid)
        db.insert_result(connection, result)
    return result
