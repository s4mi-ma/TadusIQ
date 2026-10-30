BEGIN IMMEDIATE;
CREATE TABLE IF NOT EXISTS laboratories (
    laboratory_id TEXT PRIMARY KEY, name TEXT NOT NULL, sector TEXT NOT NULL, role TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS trusted_keys (
    key_id TEXT PRIMARY KEY,
    laboratory_id TEXT NOT NULL REFERENCES laboratories(laboratory_id),
    public_key BLOB NOT NULL CHECK(length(public_key) = 32),
    active INTEGER NOT NULL CHECK(active IN (0, 1))
);
CREATE TABLE IF NOT EXISTS submissions (
    verification_id TEXT PRIMARY KEY, received_at TEXT NOT NULL,
    claimed_laboratory_id TEXT, claimed_key_id TEXT, file_name TEXT,
    file_size_bytes INTEGER NOT NULL CHECK(file_size_bytes >= 0), computed_sha256 TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS verification_results (
    verification_id TEXT PRIMARY KEY REFERENCES submissions(verification_id),
    status TEXT NOT NULL CHECK(status IN ('ACCEPTED', 'QUARANTINED')),
    reason_code TEXT NOT NULL, details TEXT NOT NULL,
    verified_laboratory_id TEXT REFERENCES laboratories(laboratory_id),
    verified_key_id TEXT REFERENCES trusted_keys(key_id),
    metadata_authenticated INTEGER NOT NULL CHECK(metadata_authenticated IN (0, 1)),
    manifest_json TEXT, checks_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS audit_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    verification_id TEXT REFERENCES submissions(verification_id),
    created_at TEXT NOT NULL,
    actor_laboratory_id TEXT NOT NULL REFERENCES laboratories(laboratory_id),
    event_type TEXT NOT NULL, details TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS audit_verification ON audit_events(verification_id, event_id);
CREATE INDEX IF NOT EXISTS submission_time ON submissions(received_at);
INSERT OR IGNORE INTO laboratories VALUES ('LAB-A', 'Laboratory A', 'Human health', 'Sender');
INSERT OR IGNORE INTO laboratories VALUES ('LAB-B', 'Laboratory B', 'Animal health', 'Verifier');
INSERT OR IGNORE INTO laboratories VALUES ('LAB-C', 'Laboratory C', 'Environmental health', 'Reviewer');
PRAGMA user_version = 1;
COMMIT;
