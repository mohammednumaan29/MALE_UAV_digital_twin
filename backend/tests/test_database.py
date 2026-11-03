"""
Automated tests for Database Models and Telemetry Persistence.
Phase 4 Verification:
- All 8 relational tables created
- Telemetry insertion and retrieval
- Digital Twin expected values storage
- REST endpoints: POST /api/telemetry, GET /api/telemetry/latest, GET /api/telemetry/history
- Data persistence across sessions
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.models.database import Base, get_db
from app.models.engine import EngineModel
from app.models.telemetry import TelemetryModel
from app.schemas.telemetry import TelemetryCreateRequest
from app.services.telemetry_service import telemetry_service

client = TestClient(app)


def test_database_table_metadata():
    """Verify all 8 required tables are registered in Base metadata."""
    expected_tables = {
        "engines",
        "telemetry",
        "health_records",
        "faults",
        "predictions",
        "physics_predictions",
        "missions",
        "mission_results",
        "maintenance_records",
    }
    actual_tables = set(Base.metadata.tables.keys())
    assert expected_tables.issubset(actual_tables), f"Missing tables: {expected_tables - actual_tables}"


def test_phase5_physics_prediction_table_metadata():
    """Verify Phase 5 includes the physics-prediction storage table with the required residual fields."""
    table = Base.metadata.tables["physics_predictions"]
    expected_columns = {
        "engine_id",
        "timestamp",
        "expected_egt",
        "expected_cht",
        "expected_oil_pressure",
        "expected_oil_temperature",
        "expected_fuel_flow",
        "expected_vibration",
        "expected_rpm",
        "egt_residual",
        "cht_residual",
        "oil_pressure_residual",
        "oil_temperature_residual",
        "fuel_flow_residual",
        "vibration_residual",
        "rpm_residual",
    }
    actual_columns = set(table.columns.keys())
    assert expected_columns.issubset(actual_columns)


def test_telemetry_crud_and_digital_twin_storage():
    """Verify inserting telemetry into DB computes and persists Digital Twin expected values."""
    from app.models.database import SessionLocal, init_db
    init_db()
    db = SessionLocal()

    try:
        sample_in = TelemetryCreateRequest(
            engine_id="rotax914-uav-01",
            rpm=5120.0,
            egt_c=745.0,
            cht_c=105.0,
            oil_pressure_bar=3.95,
            oil_temperature_c=89.0,
            fuel_flow_lph=19.2,
            vibration_g=0.21,
            altitude_ft=10000.0,
            ambient_temperature_c=15.0,
            throttle=65.0,
            engine_load=0.72,
            power_kw=53.0,
        )

        persisted = telemetry_service.insert_telemetry(db, sample_in)

        assert persisted.id is not None
        assert persisted.engine_id == "rotax914-uav-01"
        assert persisted.rpm == 5120.0

        # Verify Digital Twin expected values were computed and stored
        assert persisted.expected_rpm is not None
        assert persisted.expected_egt_c is not None
        assert persisted.expected_cht_c is not None
        assert persisted.expected_oil_pressure_bar is not None
        assert persisted.expected_oil_temperature_c is not None
        assert persisted.expected_fuel_flow_lph is not None
        assert persisted.expected_vibration_g is not None
        assert persisted.expected_power_kw is not None

        # Verify querying latest
        latest = telemetry_service.get_latest_telemetry(db, "rotax914-uav-01")
        assert latest is not None
        assert latest.id == persisted.id

        # Verify querying history
        history = telemetry_service.get_telemetry_history(db, "rotax914-uav-01", limit=10)
        assert history.total_records >= 1
        assert len(history.records) >= 1
        assert history.records[0].id == persisted.id

    finally:
        db.close()


def test_telemetry_api_endpoints():
    """Verify POST /api/telemetry, GET /api/telemetry/latest, and GET /api/telemetry/history."""
    payload = {
        "engine_id": "rotax914-uav-01",
        "rpm": 5050.0,
        "egt_c": 738.0,
        "cht_c": 102.0,
        "oil_pressure_bar": 4.02,
        "oil_temperature_c": 87.5,
        "fuel_flow_lph": 18.8,
        "vibration_g": 0.215,
        "altitude_ft": 9500.0,
        "ambient_temperature_c": 12.0,
        "throttle": 64.0,
        "engine_load": 0.70,
        "power_kw": 51.5,
        "active_fault": "NORMAL",
        "fault_severity": 0.0,
    }

    # 1. POST /api/telemetry
    post_res = client.post("/api/telemetry", json=payload)
    assert post_res.status_code == 201, post_res.text
    created = post_res.json()
    assert created["id"] > 0
    assert created["rpm"] == 5050.0
    assert created["expected_rpm"] > 0
    assert created["expected_egt_c"] > 0
    assert created["expected_oil_pressure_bar"] > 0

    record_id = created["id"]

    # 2. GET /api/telemetry/latest
    latest_res = client.get("/api/telemetry/latest?engine_id=rotax914-uav-01")
    assert latest_res.status_code == 200
    latest = latest_res.json()
    assert latest["id"] == record_id
    assert latest["engine_id"] == "rotax914-uav-01"
    assert latest["throttle"] == 64.0

    # 3. GET /api/telemetry/history
    history_res = client.get("/api/telemetry/history?engine_id=rotax914-uav-01&limit=5")
    assert history_res.status_code == 200
    history = history_res.json()
    assert history["total_records"] >= 1
    assert history["limit"] == 5
    assert len(history["records"]) >= 1
    assert history["records"][0]["id"] == record_id


def test_telemetry_not_found():
    """Verify GET /api/telemetry/latest returns 404 for unknown engine."""
    res = client.get("/api/telemetry/latest?engine_id=unknown-engine-999")
    assert res.status_code == 404
