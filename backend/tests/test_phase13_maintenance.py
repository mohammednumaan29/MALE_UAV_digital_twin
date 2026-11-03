"""Validation for phase 13 maintenance advisories."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_maintenance_advisory_endpoint_reports_fault_recommendation():
    """The maintenance endpoint should generate a fault-specific recommendation for the engine."""
    activate = client.post(
        "/api/fault/activate",
        json={"engine_id": "rotax914-uav-01", "fault_type": "LUBRICATION_DEGRADATION", "severity": 0.6},
    )
    assert activate.status_code == 200, activate.text

    response = client.get("/api/maintenance/rotax914-uav-01")
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["engine_id"] == "rotax914-uav-01"
    assert payload["fault"] == "LUBRICATION_DEGRADATION"
    assert payload["severity"] in {"Medium", "High", "Extreme"}
    assert "Inspection" in payload["recommendation"] or "lubrication" in payload["recommendation"].lower()

    deactivate = client.post("/api/fault/deactivate", json={"engine_id": "rotax914-uav-01"})
    assert deactivate.status_code == 200, deactivate.text
