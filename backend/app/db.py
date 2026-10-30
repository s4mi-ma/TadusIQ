"""Local prototype persistence. This audit is not tamper-proof."""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from .schemas import AuditEvent, Laboratory, VerificationResult

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "var" / "rapidready.sqlite3"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


class Database:
    def __init__(self, path: Path = DEFAULT_DB):
        self.path = Path(path)

    @contextmanager
    def connection(self):
        connection = sqlite3.connect(self.path, timeout=5, isolation_level=None,
                                     autocommit=sqlite3.LEGACY_TRANSACTION_CONTROL)
        connection.row_factory = sqlite3.Row
        try:
            connection.execute("PRAGMA foreign_keys = ON")
            yield connection
        finally:
            connection.close()

    @contextmanager
    def transaction(self):
        with self.connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                yield connection
                connection.execute("COMMIT")
            except BaseException:
                if connection.in_transaction:
                    connection.execute("ROLLBACK")
                raise

    def initialize(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as connection:
            version = connection.execute("PRAGMA user_version").fetchone()[0]
            if version == 0:
                source = ROOT / "backend" / "migrations" / "001_initial.sql"
                connection.executescript(source.read_text(encoding="utf-8"))
            elif version != 1:
                raise RuntimeError("Unsupported database schema version.")

    def ready(self) -> bool:
        with self.connection() as connection:
            labs = connection.execute("SELECT COUNT(*) FROM laboratories").fetchone()[0]
            keys = connection.execute("SELECT COUNT(*) FROM trusted_keys WHERE active = 1").fetchone()[0]
            return labs == 3 and keys > 0

    def register_key(self, key_id: str, laboratory_id: str, public_key: bytes, active: bool = True):
        """Trusted local setup only; never exposed as an upload API."""
        with self.transaction() as connection:
            connection.execute(
                "INSERT INTO trusted_keys VALUES (?, ?, ?, ?) ON CONFLICT(key_id) DO UPDATE SET "
                "laboratory_id=excluded.laboratory_id, public_key=excluded.public_key, active=excluded.active",
                (key_id, laboratory_id, public_key, int(active)),
            )

    def lookup_key(self, connection, key_id: str):
        return connection.execute("SELECT * FROM trusted_keys WHERE key_id = ?", (key_id,)).fetchone()

    def insert_audit(self, connection, verification_id, event_type, details):
        connection.execute(
            "INSERT INTO audit_events (verification_id, created_at, actor_laboratory_id, event_type, details) "
            "VALUES (?, ?, ?, ?, ?)", (verification_id, utc_now(), "LAB-B", event_type, details),
        )

    def insert_result(self, connection, result: VerificationResult):
        connection.execute(
            "INSERT INTO submissions VALUES (?, ?, ?, ?, ?, ?, ?)",
            (result.verification_id, result.received_at, result.claimed_laboratory_id,
             result.claimed_key_id, result.file_name, result.file_size_bytes, result.computed_sha256),
        )
        connection.execute(
            "INSERT INTO verification_results VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (result.verification_id, result.status, result.reason_code, result.details,
             result.verified_laboratory_id, result.verified_key_id, int(result.metadata_authenticated),
             result.manifest.model_dump_json() if result.manifest else None,
             json.dumps([item.model_dump() for item in result.checks])),
        )
        self.insert_audit(connection, result.verification_id, "PACKAGE_RECEIVED",
                          "LAB-B received a synthetic package; sender claim requires verification.")
        for check in result.checks:
            self.insert_audit(connection, result.verification_id, "CHECK_" + check.name.upper(), check.status)
        self.insert_audit(connection, result.verification_id, "VERIFICATION_DECIDED",
                          result.status + ": " + result.reason_code)

    def record_transport_error(self, code: str, safe_message: str):
        with self.transaction() as connection:
            self.insert_audit(connection, None, code, safe_message[:300])

    @staticmethod
    def _result(row) -> VerificationResult:
        value = dict(row)
        value["metadata_authenticated"] = bool(value["metadata_authenticated"])
        raw_manifest = value.pop("manifest_json")
        value["manifest"] = json.loads(raw_manifest) if raw_manifest else None
        value["checks"] = json.loads(value.pop("checks_json"))
        return VerificationResult.model_validate(value)

    def get_result(self, verification_id: str) -> VerificationResult | None:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT s.*, r.status, r.reason_code, r.details, r.verified_laboratory_id, r.verified_key_id, "
                "r.metadata_authenticated, r.manifest_json, r.checks_json FROM submissions s "
                "JOIN verification_results r USING(verification_id) WHERE verification_id = ?",
                (verification_id,),
            ).fetchone()
            return self._result(row) if row else None

    def list_results(self, status: str | None = None, limit: int = 50) -> list[VerificationResult]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT s.*, r.status, r.reason_code, r.details, r.verified_laboratory_id, r.verified_key_id, "
                "r.metadata_authenticated, r.manifest_json, r.checks_json FROM submissions s "
                "JOIN verification_results r USING(verification_id) WHERE (? IS NULL OR r.status = ?) "
                "ORDER BY s.received_at DESC, s.verification_id DESC LIMIT ?", (status, status, limit),
            ).fetchall()
            return [self._result(row) for row in rows]

    def list_audit(self, verification_id: str | None = None, limit: int = 100) -> list[AuditEvent]:
        with self.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM audit_events WHERE (? IS NULL OR verification_id = ?) "
                "ORDER BY event_id DESC LIMIT ?", (verification_id, verification_id, limit),
            ).fetchall()
            return [AuditEvent.model_validate(dict(row)) for row in rows]

    def list_laboratories(self) -> list[Laboratory]:
        with self.connection() as connection:
            return [Laboratory.model_validate(dict(row)) for row in connection.execute(
                "SELECT * FROM laboratories ORDER BY laboratory_id")]
