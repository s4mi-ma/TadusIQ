"""Exercise the D1 adapter's actual SQL and batch rollback against SQLite."""
import asyncio
import base64
import importlib.util
import sqlite3
import sys
from pathlib import Path

import pytest
from app import policy, schemas
from app.policy import PreparedPackage, decide
from app.canonical import canonical_bytes
from test_verification import package

ROOT = Path(__file__).resolve().parents[2]

class Statement:
    def __init__(self, binding, sql, values=()):
        self.binding, self.sql, self.values = binding, sql, values
    def bind(self, *values):
        return Statement(self.binding, self.sql, values)
    async def run(self):
        with self.binding.database.transaction() as connection:
            connection.execute(self.sql, self.values)
        return {"success": True}
    async def all(self):
        with self.binding.database.connection() as connection:
            return {"results": [dict(row) for row in connection.execute(self.sql, self.values)]}

class Binding:
    def __init__(self, database):
        self.database = database
    def withSession(self, constraint):
        assert constraint == "first-primary"
        return self
    def prepare(self, sql):
        return Statement(self, sql)
    async def batch(self, statements):
        with self.database.transaction() as connection:
            for statement in statements:
                connection.execute(statement.sql, statement.values)
        return [{"success": True} for _ in statements]

@pytest.fixture
def store_class(monkeypatch):
    monkeypatch.setitem(sys.modules, "shared.policy", policy)
    monkeypatch.setitem(sys.modules, "shared.schemas", schemas)
    spec = importlib.util.spec_from_file_location("d1_store_under_test", ROOT / "cloudflare" / "src" / "d1_store.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.D1Store

def prepared(package):
    _, key, data, manifest = package
    raw = canonical_bytes(manifest)
    return PreparedPackage(data, manifest["file_name"], raw, base64.b64encode(key.sign(raw)))

def test_d1_commit_roundtrip_and_nine_events(package, store_class):
    async def exercise():
        store = store_class(Binding(package[0]))
        p = prepared(package)
        key = await store.key(p.manifest.key_id)
        result = decide(p, key, True)
        await store.commit(result, p, key)
        assert await store.ready()
        assert package[0].get_result(result.verification_id) == result
        assert len(package[0].list_audit(result.verification_id)) == 9
    asyncio.run(exercise())

@pytest.mark.parametrize("change", ["revoke", "replace", "wrong-lab"])
def test_d1_changed_trust_rolls_back_everything(package, store_class, change):
    async def exercise():
        store = store_class(Binding(package[0]))
        p = prepared(package)
        key = await store.key(p.manifest.key_id)
        result = decide(p, key, True)
        public = bytes.fromhex(key["public_key_hex"])
        package[0].register_key(p.manifest.key_id, "LAB-B" if change == "wrong-lab" else "LAB-A",
                                bytes(32) if change == "replace" else public, active=change != "revoke")
        with pytest.raises(sqlite3.IntegrityError):
            await store.commit(result, p, key)
        assert package[0].list_results() == []
        assert package[0].list_audit() == []
    asyncio.run(exercise())

def test_d1_audit_failure_rolls_back_acceptance(package, store_class):
    async def exercise():
        store = store_class(Binding(package[0]))
        p = prepared(package)
        key = await store.key(p.manifest.key_id)
        result = decide(p, key, True)
        with package[0].connection() as connection:
            connection.execute("CREATE TRIGGER fail_audit BEFORE INSERT ON audit_events BEGIN SELECT RAISE(ABORT,'test'); END")
        with pytest.raises(sqlite3.IntegrityError):
            await store.commit(result, p, key)
        assert package[0].list_results() == []
    asyncio.run(exercise())
