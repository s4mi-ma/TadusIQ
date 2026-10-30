# Signed manifest V1

All fields below are required and covered by the detached Ed25519 signature. This is a synthetic local prototype format, not a general JSON canonicalization standard.

| Field | Constraint |
|---|---|
| schema_version | Strict integer 1 |
| laboratory_id | 1–64 ASCII letters, digits, hyphen or underscore; registered sender |
| key_id | Same identifier syntax; active key bound to sender |
| file_name | 1–120 ASCII letters, digits, dot, hyphen or underscore; begins with letter/digit; no path separators or consecutive dots |
| file_sha256 | 64 lowercase hexadecimal characters |
| file_size_bytes | Strict integer from 1 through 2,097,152 |
| signed_at | Valid UTC calendar timestamp YYYY-MM-DDTHH:mm:ssZ |
| metadata.sample_id | Same bounded identifier syntax |
| metadata.collected_at | Same timestamp syntax; not later than signed_at |
| metadata.data_type | csv, json or txt; matches file extension |
| metadata.synthetic | Boolean true; numeric 1 and string true are rejected |

Canonical JSON recursively sorts keys, uses comma/colon without spaces, UTF-8, no BOM or trailing newline, no nonfinite values and no floating-point fields. Unknown and duplicate keys are rejected. The verifier compares the incoming bytes to the canonical encoding, then verifies the signature against those **original bytes**. It does not normalize dates or silently rewrite signed metadata.

The signature is exactly 64 bytes, encoded as canonical padded standard base64 (88 ASCII bytes). The public registry contains a 32-byte raw Ed25519 public key. The verifier never trusts a public key carried by the uploaded package.

Failure precedence: transport/JSON/base64 validity → schema and canonical representation → active trusted key → sender binding → Ed25519 signature → uploaded filename → file size → SHA-256 digest. Each later check is marked skipped if an earlier check fails. Metadata is only authenticated after successful signature verification. Byte size/digest mismatch can quarantine a package even when its manifest signature is valid.

Known lab identities and synthetic keys express local demo trust, not real institutional identity. Timestamps are signed claims, not trusted timestamp evidence. Replay protection and scientific-content validation are not implemented. MIME type is not trusted as proof of file content.
