"""
Automated tests for Digital Twin Prediction API endpoint.
POST /api/digital-twin/predict
Phase 1 Verification.
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_predict_standard_cruise():
    """Verify POST /api/digital-twin/predict with standard cruise parameters."""
    payload = {
        "throttle": 65.0,
        "altitude_ft": 10000.0,
        "ambient_temperature_c": 15.0
    }
    response = client.post("/api/digital-twin/predict", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Core required fields
    required_fields = [
        "expected_rpm",
        "expected_egt_c",
        "expected_cht_c",
        "expected_oil_pressure_bar",
        "expected_oil_temperature_c",
        "expected_fuel_flow_lph",
        "expected_vibration_g",
        "expected_power_kw",
        "expected_torque_nm"
    ]
    for field in required_fields:
        assert field in data
        assert isinstance(data[field], (int, float))
        assert data[field] > 0

    # Sanity checks for 65% throttle @ 10k ft
    assert 4800 <= data["expected_rpm"] <= 5300
    assert 45.0 <= data["expected_power_kw"] <= 70.0
    assert 14.0 <= data["expected_fuel_flow_lph"] <= 22.0
    assert 650.0 <= data["expected_egt_c"] <= 780.0
    assert 100.0 <= data["expected_cht_c"] <= 135.0
    assert 3.0 <= data["expected_oil_pressure_bar"] <= 4.9
    assert 0.12 <= data["expected_vibration_g"] <= 0.22


def test_predict_idle():
    """Verify prediction at ground idle."""
    payload = {
        "throttle": 5.0,
        "altitude_ft": 0.0,
        "ambient_temperature_c": 20.0
    }
    response = client.post("/api/digital-twin/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["expected_rpm"] < 2000
    assert data["expected_power_kw"] < 15.0
    assert data["expected_fuel_flow_lph"] < 7.0


def test_predict_takeoff():
    """Verify prediction at takeoff power (full throttle)."""
    payload = {
        "throttle": 100.0,
        "altitude_ft": 0.0,
        "ambient_temperature_c": 15.0
    }
    response = client.post("/api/digital-twin/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["expected_rpm"] >= 5750.0
    assert data["expected_power_kw"] >= 80.0
    assert data["expected_fuel_flow_lph"] >= 25.0


def test_predict_validation_errors():
    """Verify invalid inputs are rejected with 422 Unprocessable Entity."""
    # Negative throttle
    res_neg_th = client.post("/api/digital-twin/predict", json={"throttle": -10, "altitude_ft": 1000, "ambient_temperature_c": 15})
    assert res_neg_th.status_code == 422

    # Excessive throttle
    res_exc_th = client.post("/api/digital-twin/predict", json={"throttle": 115, "altitude_ft": 1000, "ambient_temperature_c": 15})
    assert res_exc_th.status_code == 422

    # Negative altitude
    res_neg_alt = client.post("/api/digital-twin/predict", json={"throttle": 50, "altitude_ft": -500, "ambient_temperature_c": 15})
    assert res_neg_alt.status_code == 422

    # Extreme ambient temperature out of range
    res_ext_temp = client.post("/api/digital-twin/predict", json={"throttle": 50, "altitude_ft": 1000, "ambient_temperature_c": 95})
    assert res_ext_temp.status_code == 422
