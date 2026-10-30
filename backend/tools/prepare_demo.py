"""Prepare synthetic Lab A packages. The private key exists only in this process."""

import argparse
import base64
import copy
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from app.canonical import canonical_bytes
from app.db import DEFAULT_DB, ROOT, Database
from app.schemas import Manifest

SCENARIOS = (
    ("valid", "Valid package", "An intact file with complete metadata and a trusted signature."),
    ("modified-file", "Modified file", "One file byte changes after the manifest is signed."),
    ("invalid-signature", "Invalid signature", "The detached signature is deliberately altered."),
    ("missing-metadata", "Missing metadata", "The mandatory synthetic sample ID is absent."),
)


def prepare_demo(database_path: Path, output_dir: Path, public_dir: Path):
    db = Database(database_path)
    db.initialize()
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    key_id = "demo-" + hashlib.sha256(public_key).hexdigest()[:16]
    db.register_key(key_id, "LAB-A", public_key)
    data = b"SYNTHETIC DEVELOPMENT DATA\nsample_id: SYN-001\nresult: demonstration-only\n"
    manifest = {
        "schema_version": 1, "laboratory_id": "LAB-A", "file_name": "synthetic-result.txt",
        "file_sha256": hashlib.sha256(data).hexdigest(), "file_size_bytes": len(data),
        "signed_at": "2026-10-26T12:00:00Z", "key_id": key_id,
        "metadata": {"sample_id": "SYN-001", "collected_at": "2026-10-26T11:00:00Z",
                     "data_type": "txt", "synthetic": True},
    }
    Manifest.model_validate(manifest)
    public_dir.mkdir(parents=True, exist_ok=True)
    catalog = []
    for scenario, label, description in SCENARIOS:
        value = copy.deepcopy(manifest)
        content = data
        if scenario == "missing-metadata":
            del value["metadata"]["sample_id"]
        raw = canonical_bytes(value)
        signature = private_key.sign(raw)
        if scenario == "modified-file":
            content = b"X" + data[1:]
        if scenario == "invalid-signature":
            signature = bytes([signature[0] ^ 1]) + signature[1:]
        encoded_signature = base64.b64encode(signature).decode("ascii")
        directory = output_dir / scenario
        directory.mkdir(parents=True, exist_ok=True)
        (directory / manifest["file_name"]).write_bytes(content)
        (directory / "manifest.json").write_bytes(raw)
        (directory / "signature.txt").write_bytes(encoded_signature.encode("ascii"))
        # These public artifacts contain synthetic data and detached signatures,
        # never private key bytes or an embedded key to trust on upload.
        bundle = {"file_name": manifest["file_name"], "file_base64": base64.b64encode(content).decode("ascii"),
                  "manifest": raw.decode("utf-8"), "signature": encoded_signature}
        (public_dir / (scenario + ".json")).write_text(json.dumps(bundle), encoding="utf-8")
        catalog.append({"id": scenario, "label": label, "description": description})
    (public_dir / "catalog.json").write_text(json.dumps(catalog), encoding="utf-8")
    return catalog


def main():
    parser = argparse.ArgumentParser(description="Prepare synthetic Lab A demo packages; private key stays in memory.")
    parser.add_argument("--database", type=Path, default=DEFAULT_DB)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "fixtures" / "generated")
    parser.add_argument("--public-dir", type=Path, default=ROOT / "frontend" / "public" / "demo")
    args = parser.parse_args()
    catalog = prepare_demo(args.database, args.output_dir, args.public_dir)
    print(f"Prepared {len(catalog)} synthetic Lab A scenarios. Only the public key was registered.")
    print(f"Public packages: {args.output_dir}")


if __name__ == "__main__":
    main()
