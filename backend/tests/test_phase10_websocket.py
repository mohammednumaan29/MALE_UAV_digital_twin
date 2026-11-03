"""Validation for Phase 10 WebSocket telemetry streaming."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_websocket_streams_telemetry_payload():
    """A websocket client should receive a structured telemetry snapshot with health and ML fields."""
    with client.websocket_connect("/ws/telemetry/rotax914-uav-01") as websocket:
        payload = websocket.receive_json()
        assert "timestamp" in payload
        assert payload["engine_id"] == "rotax914-uav-01"
        assert "telemetry" in payload
        assert "expected" in payload
        assert "residuals" in payload
        assert "health" in payload
        assert "fault" in payload
        assert "anomaly" in payload
        assert "rul" in payload
        assert "affected_region" in payload
        assert payload["telemetry"]["rpm"] > 0
        assert payload["health"]["status"] in {"HEALTHY", "NORMAL", "DEGRADED", "CRITICAL"}
