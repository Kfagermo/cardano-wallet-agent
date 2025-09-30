import os
import json
import time
import importlib

# Ensure bypass in test to complete immediately
os.environ["MASUMI_BYPASS_PAYMENTS"] = "true"
os.environ.setdefault("NETWORK", "preprod")

from fastapi.testclient import TestClient  # noqa: E402
from src import main  # noqa: E402

# Reload in case env was read earlier in the interpreter
importlib.reload(main)


def test_availability_and_schema():
    with TestClient(main.app) as client:
        r1 = client.get("/availability")
        assert r1.status_code == 200
        body = r1.json()
        assert body.get("status") == "available"

        r2 = client.get("/input_schema")
        assert r2.status_code == 200
        schema = r2.json()
        assert "input_data" in schema
        keys = [x.get("key") for x in schema["input_data"]]
        assert "address" in keys and "network" in keys


def test_start_job_and_status_bypass_completes():
    with TestClient(main.app) as client:
        payload = {
            "input_data": [
                {"key": "address", "value": "addr1qxyzdemoaddress"},
                {"key": "network", "value": "preprod"},
            ]
        }
        r = client.post("/start_job", json=payload)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "job_id" in data and "payment_id" in data
        job_id = data["job_id"]

        # BYPASS=true => should be completed immediately
        r2 = client.get(f"/status?job_id={job_id}")
        assert r2.status_code == 200, r2.text
        status = r2.json()
        assert status["job_id"] == job_id
        assert status["status"] == "completed"
        assert isinstance(status.get("result"), str)

        # Result is a JSON string; parse it
        result_obj = json.loads(status["result"])
        for k in ["address", "network", "risk_score", "health"]:
            assert k in result_obj
        assert result_obj.get("report_path")  # human-view path existed
