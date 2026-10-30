import base64
import json

from fastapi.testclient import TestClient

from app.db import Database
from app.main import create_app
from tools.prepare_demo import prepare_demo


def test_sender_generated_scenarios_verify_and_export_no_keys(tmp_path):
    database = tmp_path / "demo.sqlite3"
    public = tmp_path / "public"
    output = tmp_path / "fixtures"
    catalog = prepare_demo(database, output, public)
    expected = {"valid": "VALID", "modified-file": "HASH_MISMATCH",
                "invalid-signature": "INVALID_SIGNATURE", "missing-metadata": "INVALID_METADATA"}
    with TestClient(create_app(Database(database))) as client:
        for item in catalog:
            bundle = json.loads((public / (item["id"] + ".json")).read_text())
            assert set(bundle) == {"file_name", "file_base64", "manifest", "signature"}
            response = client.post("/api/verify", data={"manifest": bundle["manifest"], "signature": bundle["signature"]},
                                   files={"file": (bundle["file_name"], base64.b64decode(bundle["file_base64"]))})
            assert response.status_code == 200
            assert response.json()["reason_code"] == expected[item["id"]]
        assert len(client.get("/api/verifications").json()) == 4
    for path in [*public.rglob("*"), *output.rglob("*")]:
        if path.is_file():
            assert b"PRIVATE KEY" not in path.read_bytes()
            assert path.suffix not in {".pem", ".key"}
