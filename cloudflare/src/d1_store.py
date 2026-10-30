"""D1 parameterized persistence with atomic decision/audit and trust guard."""
import json
from shared.policy import utc_now
from shared.schemas import VerificationResult

RESULT_SELECT = (
    "SELECT s.*, r.status, r.reason_code, r.details, r.verified_laboratory_id, r.verified_key_id, "
    "r.metadata_authenticated, r.manifest_json, r.checks_json FROM submissions s "
    "JOIN verification_results r USING(verification_id) "
)

def result_from_row(row):
    value = dict(row)
    value["metadata_authenticated"] = bool(value["metadata_authenticated"])
    raw = value.pop("manifest_json")
    value["manifest"] = json.loads(raw) if raw else None
    value["checks"] = json.loads(value.pop("checks_json"))
    return VerificationResult.model_validate(value)

class D1Store:
    def __init__(self, binding):
        self.db = binding.withSession("first-primary")

    def statement(self, sql, *values):
        return self.db.prepare(sql).bind(*values) if values else self.db.prepare(sql)

    async def rows(self, sql, *values):
        response = await self.statement(sql, *values).all()
        return response["results"]

    async def key(self, key_id):
        rows = await self.rows("SELECT key_id, laboratory_id, hex(public_key) AS public_key_hex, active "
                               "FROM trusted_keys WHERE key_id = ?", key_id)
        return rows[0] if rows else None

    async def ready(self):
        rows = await self.rows("SELECT (SELECT COUNT(*) FROM laboratories) AS labs, "
                               "(SELECT COUNT(*) FROM trusted_keys WHERE active=1) AS keys")
        return rows[0]["labs"] == 3 and rows[0]["keys"] > 0

    async def record_error(self, code, message):
        await self.statement("INSERT INTO audit_events (created_at,actor_laboratory_id,event_type,details) "
                             "VALUES (?,?,?,?)", utc_now(), "LAB-B", code, message[:300]).run()

    async def commit(self, result, package, key):
        guard, parameters = "1", []
        if package.valid_metadata:
            if key is None:
                guard = "NOT EXISTS (SELECT 1 FROM trusted_keys WHERE key_id=?)"
                parameters = [package.manifest.key_id]
            else:
                guard = ("EXISTS (SELECT 1 FROM trusted_keys WHERE key_id=? AND laboratory_id=? "
                         "AND hex(public_key)=? AND active=?)")
                parameters = [key["key_id"], key["laboratory_id"], key["public_key_hex"], key["active"]]
        # Changed trust makes this insert affect zero rows. The following result
        # foreign key then fails, rolling back the entire D1 batch.
        statements = [self.statement(
            "INSERT INTO submissions SELECT ?,?,?,?,?,?,? WHERE " + guard,
            result.verification_id, result.received_at, result.claimed_laboratory_id,
            result.claimed_key_id, result.file_name, result.file_size_bytes, result.computed_sha256,
            *parameters), self.statement(
            "INSERT INTO verification_results VALUES (?,?,?,?,?,?,?,?,?)",
            result.verification_id, result.status, result.reason_code, result.details,
            result.verified_laboratory_id, result.verified_key_id, int(result.metadata_authenticated),
            result.manifest.model_dump_json() if result.manifest else None,
            json.dumps([check.model_dump() for check in result.checks]))]
        events = [("PACKAGE_RECEIVED", "LAB-B received a synthetic package; sender claim requires verification.")]
        events += [("CHECK_" + check.name.upper(), check.status) for check in result.checks]
        events += [("VERIFICATION_DECIDED", result.status + ": " + result.reason_code)]
        for event_type, details in events:
            statements.append(self.statement(
                "INSERT INTO audit_events (verification_id,created_at,actor_laboratory_id,event_type,details) "
                "VALUES (?,?,?,?,?)", result.verification_id, utc_now(), "LAB-B", event_type, details))
        responses = await self.db.batch(statements)
        if any(not response["success"] for response in responses):
            raise RuntimeError("D1 batch did not succeed.")
