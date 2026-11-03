"""Validation for Phase 9 API endpoints."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_fault_activation_and_engine_state():
    """Verify fault control endpoints and engine state snapshot."""
    response = client.post(
        "/api/fault/activate",
        json={"engine_id": "rotax914-uav-01", "fault_type": "OVERHEATING", "severity": 0.5},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["fault_type"] == "OVERHEATING"
    assert payload["severity"] == 0.5

    status_response = client.get("/api/fault/status")
    assert status_response.status_code == 200
    assert status_response.json()["fault_type"] == "OVERHEATING"

    state_response = client.get("/api/engine/rotax914-uav-01/state")
    assert state_response.status_code == 200, state_response.text
    state = state_response.json()
    assert state["engine_id"] == "rotax914-uav-01"
    assert "telemetry" in state
    assert "health" in state

    deactivate_response = client.post("/api/fault/deactivate", json={"engine_id": "rotax914-uav-01"})
    assert deactivate_response.status_code == 200
    assert deactivate_response.json()["fault_type"] == "NORMAL"


def test_telemetry_engine_endpoint_returns_history():
    """The engine-specific telemetry route should return a history payload."""
    response = client.get("/api/telemetry/rotax914-uav-01?limit=5")
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["engine_id"] == "rotax914-uav-01"
    assert payload["total_records"] >= 1
    assert len(payload["records"]) >= 1


def test_mission_simulation_and_replay_endpoints():
    """Mission simulate and replay should persist and expose mission metadata."""
    response = client.post(
        "/api/mission/simulate",
        json={
            "engine_id": "rotax914-uav-01",
            "duration_hours": 8,
            "altitude_ft": 12000,
            "ambient_temperature_c": 38,
            "throttle": 65,
            "mission_type": "SURVEILLANCE",
        },
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["engine_id"] == "rotax914-uav-01"
    assert payload["mission_risk"] in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}

    mission_id = payload["mission_id"]
    mission_response = client.get(f"/api/mission/{mission_id}")
    assert mission_response.status_code == 200, mission_response.text
    mission_payload = mission_response.json()
    assert mission_payload["mission_id"] == mission_id

    replay_response = client.get(f"/api/replay/{mission_id}")
    assert replay_response.status_code == 200, replay_response.text
    replay_payload = replay_response.json()
    assert replay_payload["mission_id"] == mission_id
    assert "telemetry" in replay_payload
    assert "health_trend" in replay_payload
    assert len(replay_payload["telemetry"]) >= 1
    assert len(replay_payload["health_trend"]) >= 1
