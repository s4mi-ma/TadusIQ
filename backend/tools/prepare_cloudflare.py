"""Prepare public deployment assets; signing remains in this sender process."""
import json
import shutil
from app.db import ROOT, Database
from tools.prepare_demo import prepare_demo

def main():
    deployment = ROOT / "cloudflare"
    shared = deployment / "src" / "shared"
    shared.mkdir(parents=True, exist_ok=True)
    for name in ("__init__.py", "canonical.py", "schemas.py", "multipart.py", "policy.py"):
        shutil.copyfile(ROOT / "backend" / "app" / name, shared / name)
    migrations = deployment / "migrations"
    migrations.mkdir(exist_ok=True)
    source = (ROOT / "backend" / "migrations" / "001_initial.sql").read_text(encoding="utf-8")
    source = "\n".join(line for line in source.splitlines()
                       if line not in ("BEGIN IMMEDIATE;", "COMMIT;", "PRAGMA user_version = 1;"))
    (migrations / "0001_initial.sql").write_text(source + "\n", encoding="utf-8")
    sender_db = ROOT / "var" / "cloudflare-sender.sqlite3"
    prepare_demo(sender_db, ROOT / "var" / "cloudflare-fixtures", ROOT / "frontend" / "public" / "demo")
    bundle = json.loads((ROOT / "frontend" / "public" / "demo" / "valid.json").read_text(encoding="utf-8"))
    key_id = json.loads(bundle["manifest"])["key_id"]
    db = Database(sender_db)
    with db.connection() as connection:
        row = db.lookup_key(connection, key_id)
        public_key = bytes(row["public_key"])
        seed = ("INSERT OR IGNORE INTO trusted_keys VALUES ('" + key_id + "','LAB-A',X'"
                + public_key.hex() + "',1);\n")
    # Keep the existing localhost dashboard compatible with the public fixture
    # files this command refreshes. Only a public development key is copied.
    local = Database()
    local.initialize()
    local.register_key(key_id, "LAB-A", public_key)
    (deployment / "seed.sql").write_text(seed, encoding="ascii")
    print("Prepared shared receiver modules, D1 schema, synthetic packages and PUBLIC-key-only seed.")

if __name__ == "__main__":
    main()
