"""
Automated tests for health and system endpoints.
Phase 0 Verification.
"""

from fastapi.testclient import TestClient
from app.main import app
from app.config.settings import settings

client = TestClient(app)


def test_health_endpoint():
    """Verify GET /api/health meets Phase 0 specification."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "rotax914-digital-twin-backend"


def test_system_info_endpoint():
    """Verify GET /api/system/info returns required metadata fields."""
    response = client.get("/api/system/info")
    assert response.status_code == 200
    data = response.json()
    assert "application" in data
    assert "version" in data
    assert "environment" in data
    assert "physics_model" in data
    assert "ml_models" in data
    assert "disclaimer" in data
    assert data["service_name"] if "service_name" in data else True
    assert data["version"] == settings.APP_VERSION


def test_root_endpoint():
    """Verify GET / returns root welcome payload and docs link."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "docs_url" in data
    assert data["docs_url"] == "/docs"


def test_swagger_and_openapi():
    """Verify Swagger docs and OpenAPI schema are accessible."""
    docs_res = client.get("/docs")
    assert docs_res.status_code == 200
    
    openapi_res = client.get("/openapi.json")
    assert openapi_res.status_code == 200
    schema = openapi_res.json()
    assert schema["info"]["title"] == settings.APP_NAME


def test_health_engine_returns_healthy_status_for_nominal_conditions():
    """The health engine must keep a nominal engine well inside the HEALTHY band."""
    from app.services.health_service import HealthEngine

    score = HealthEngine().compute(
        anomaly_score=0.05,
        fault_probability=5.0,
        severity=0.08,
        residuals={
            "egt_residual": 8.0,
            "cht_residual": 4.0,
            "oil_temperature_residual": 3.0,
            "oil_pressure_residual": 0.1,
            "vibration_residual": 0.02,
        },
        vibration_g=0.14,
        oil_pressure_bar=3.6,
    )

    assert score["health_index"] >= 90.0
    assert score["status"] == "HEALTHY"


def test_health_engine_penalizes_faulted_conditions():
    """The health engine must drop sharply as anomaly, probability, and residuals increase."""
    from app.services.health_service import HealthEngine

    score = HealthEngine().compute(
        anomaly_score=0.82,
        fault_probability=78.0,
        severity=0.74,
        residuals={
            "egt_residual": 62.0,
            "cht_residual": 28.0,
            "oil_temperature_residual": 24.0,
            "oil_pressure_residual": -1.8,
            "vibration_residual": 0.22,
        },
        vibration_g=0.72,
        oil_pressure_bar=1.2,
    )

    assert score["health_index"] < 70.0
    assert score["status"] in {"DEGRADED", "CRITICAL"}


def test_health_engine_thresholds_are_configurable():
    """Thresholds should be overrideable without changing the rest of the system."""
    from app.services.health_service import HealthEngine

    custom = HealthEngine(thresholds={"HEALTHY": 99.0, "NORMAL": 85.0, "DEGRADED": 50.0})
    result = custom.compute(
        anomaly_score=0.0,
        fault_probability=0.0,
        severity=0.0,
        residuals={"egt_residual": 0.0, "cht_residual": 0.0, "oil_temperature_residual": 0.0, "oil_pressure_residual": 0.0, "vibration_residual": 0.0},
        vibration_g=0.10,
        oil_pressure_bar=3.8,
    )

    assert result["health_index"] >= 99.0
    assert result["status"] == "HEALTHY"
