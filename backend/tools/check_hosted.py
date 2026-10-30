"""Exercise a hosted/local Worker through its real HTTP API with public fixtures."""
import argparse
import base64
import json
from pathlib import Path
import httpx
from app.canonical import canonical_bytes

ROOT = Path(__file__).resolve().parents[2]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    args = parser.parse_args()
    expected = {"valid": "VALID", "modified-file": "HASH_MISMATCH",
                "invalid-signature": "INVALID_SIGNATURE", "missing-metadata": "INVALID_METADATA"}
    with httpx.Client(base_url=args.url.rstrip("/"), timeout=40) as client:
        health = client.get("/api/health")
        assert health.status_code == 200, health.text
        assert health.json()["status"] == "OK"
        for scenario, reason in expected.items():
            bundle = json.loads((ROOT / "frontend" / "public" / "demo" / (scenario + ".json")).read_text())
            response = client.post("/api/verify", files={"file": (bundle["file_name"], base64.b64decode(bundle["file_base64"]), "text/plain")},
                                   data={"manifest": bundle["manifest"], "signature": bundle["signature"]})
            assert response.status_code == 200, response.text
            result = response.json()
            assert result["reason_code"] == reason, result
            assert result["status"] == ("ACCEPTED" if scenario == "valid" else "QUARANTINED")
            verification_id = result["verification_id"]
            detail = client.get("/api/verifications/" + verification_id)
            assert detail.json() == result
            events = client.get("/api/audit", params={"verification_id": verification_id}).json()
            assert len(events) == 9
            assert events[0]["event_type"] == "VERIFICATION_DECIDED"
            print(scenario, result["status"], reason, verification_id)
        assert len(client.get("/api/laboratories").json()) == 3
        assert all(r["status"] == "QUARANTINED" for r in client.get("/api/verifications", params={"status": "QUARANTINED"}).json())
        assert client.get("/api/verifications", params={"limit": 0}).status_code == 400
        bad = client.post("/api/verify", content=b"malformed", headers={"Content-Type": "application/json"})
        assert bad.status_code == 400 and bad.json()["error"]["audit_recorded"]
        assert client.post("/api/verify", headers={"Origin": "https://untrusted.invalid"}).status_code == 403
        valid = json.loads((ROOT / "frontend" / "public" / "demo" / "valid.json").read_text())
        for change, reason in (("unknown", "UNKNOWN_OR_REVOKED_KEY"), ("sender", "SENDER_KEY_MISMATCH"),
                               ("manifest", "INVALID_SIGNATURE")):
            manifest = json.loads(valid["manifest"])
            if change == "unknown":
                manifest["key_id"] = "unknown-development-key"
            elif change == "sender":
                manifest["laboratory_id"] = "LAB-C"
            else:
                manifest["metadata"]["sample_id"] = "SYN-ALTERED"
            response = client.post("/api/verify", files={"file": (valid["file_name"], base64.b64decode(valid["file_base64"]), "text/plain")},
                                   data={"manifest": canonical_bytes(manifest).decode(), "signature": valid["signature"]})
            assert response.status_code == 200, response.text
            assert response.json()["status"] == "QUARANTINED" and response.json()["reason_code"] == reason
            print(change, "QUARANTINED", reason)
        oversized = client.post("/api/verify", files={"file": (valid["file_name"], b"X" * 2097153, "text/plain")},
                                 data={"manifest": valid["manifest"], "signature": valid["signature"]})
        assert oversized.status_code == 413, oversized.text
        page = client.get("/")
        assert page.status_code == 200 and "TadusIQ" in page.text
        print("PASS: readiness, four scenarios, persistence/audit, unknown key, sender binding, signed-metadata tamper, 2 MiB limit, registry/filter, validation/errors/Origin and frontend.")

if __name__ == "__main__":
    main()
