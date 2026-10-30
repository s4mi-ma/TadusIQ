"""Separate synthetic sender for TadusIQ's six shareable demonstration packages."""
import argparse
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from app.canonical import canonical_bytes
from app.db import DEFAULT_DB, ROOT, Database
from app.schemas import Manifest

CASES = (
    ('01-valid-human', 'Human health · TXT', 'txt', 'VALID'),
    ('02-valid-animal', 'Animal health · CSV', 'csv', 'VALID'),
    ('03-valid-environment', 'Environmental health · JSON', 'json', 'VALID'),
    ('04-modified-file', 'Modified file', 'txt', 'HASH_MISMATCH'),
    ('05-invalid-signature', 'Invalid signature', 'txt', 'INVALID_SIGNATURE'),
    ('06-missing-metadata', 'Missing metadata', 'txt', 'INVALID_METADATA'),
)


def prepare_shareable_demos(database_path: Path, output_dir: Path):
    if any((output_dir / case[0]).exists() for case in CASES) or any(
        (output_dir / name).exists() for name in ('catalog.json', 'public-key.json')
    ):
        raise FileExistsError('Choose a fresh output directory; existing demo packages are preserved.')
    db = Database(database_path)
    db.initialize()
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    key_id = 'tadusiq-demo-' + hashlib.sha256(public_key).hexdigest()[:16]
    db.register_key(key_id, 'LAB-A', public_key)
    output_dir.mkdir(parents=True, exist_ok=True)
    catalog = []
    for index, (case, label, extension, reason) in enumerate(CASES, 1):
        sample_id = f'SYN-DEMO-{index:03}'
        if extension == 'csv':
            data = f'sample_id,synthetic,result\n{sample_id},true,demonstration-only\n'.encode()
        elif extension == 'json':
            data = json.dumps({'sample_id': sample_id, 'synthetic': True, 'result': 'demonstration-only'}, indent=2).encode() + b'\n'
        else:
            data = f'SYNTHETIC DEVELOPMENT DATA ONLY\nsample_id: {sample_id}\nresult: demonstration-only\n'.encode()
        filename = f'{case}.{extension}'
        manifest = {'schema_version': 1, 'laboratory_id': 'LAB-A', 'file_name': filename,
                    'file_sha256': hashlib.sha256(data).hexdigest(), 'file_size_bytes': len(data),
                    'signed_at': '2026-10-30T12:00:00Z', 'key_id': key_id,
                    'metadata': {'sample_id': sample_id, 'collected_at': '2026-10-30T11:00:00Z',
                                 'data_type': extension, 'synthetic': True}}
        Manifest.model_validate(manifest)
        if reason == 'INVALID_METADATA':
            del manifest['metadata']['sample_id']
        raw = canonical_bytes(manifest)
        signature = private_key.sign(raw)
        if reason == 'HASH_MISMATCH':
            data = b'X' + data[1:]
        elif reason == 'INVALID_SIGNATURE':
            signature = bytes([signature[0] ^ 1]) + signature[1:]
        folder = output_dir / case
        # Fail instead of mixing newly signed files with an earlier export.
        folder.mkdir(exist_ok=False)
        (folder / filename).write_bytes(data)
        (folder / 'manifest.json').write_bytes(raw)
        (folder / 'signature.txt').write_bytes(base64.b64encode(signature))
        catalog.append({'id': case, 'label': label, 'file_name': filename,
                        'expected_status': 'ACCEPTED' if reason == 'VALID' else 'QUARANTINED',
                        'expected_reason': reason})
    (output_dir / 'catalog.json').write_text(json.dumps(catalog, indent=2), encoding='utf-8')
    (output_dir / 'public-key.json').write_text(json.dumps({'key_id': key_id, 'laboratory_id': 'LAB-A',
        'public_key_base64': base64.b64encode(public_key).decode()}, indent=2), encoding='utf-8')
    return catalog


def main():
    parser = argparse.ArgumentParser(description='Generate six synthetic packages; register only their public signing key locally.')
    parser.add_argument('--database', type=Path, default=DEFAULT_DB)
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'frontend' / 'public' / 'demo-kit')
    args = parser.parse_args()
    prepare_shareable_demos(args.database, args.output_dir)
    print('Prepared six synthetic packages. Private key remained in the sender process.')


if __name__ == '__main__':
    main()
