"""
Automated tests for configuration and engine constants.
Phase 0 Verification.
"""

from app.config.settings import settings
from app.config.constants import (
    SYSTEM_DISCLAIMER,
    ENGINE_DISPLACEMENT_L,
    MAX_CONTINUOUS_RPM,
    FaultCategory,
    EngineSubsystem,
    PRIMARY_TELEMETRY_FIELDS,
    RESIDUAL_FIELDS,
)


def test_settings_defaults():
    """Verify default application configuration values."""
    assert settings.APP_NAME == "Rotax 914 Aero-Piston Engine Digital Twin Backend"
    assert settings.APP_VERSION == "0.1.0"
    assert settings.SERVICE_NAME == "rotax914-digital-twin-backend"
    assert settings.ENVIRONMENT == "development"
    assert settings.PORT == 8000
    assert settings.LOG_LEVEL == "INFO"


def test_constants_definitions():
    """Verify physical engine constants and fault categories."""
    assert ENGINE_DISPLACEMENT_L == 1.2112
    assert MAX_CONTINUOUS_RPM == 5500.0
    assert "prototype" in SYSTEM_DISCLAIMER.lower()

    # Fault categories verification
    assert FaultCategory.NORMAL.value == "NORMAL"
    assert FaultCategory.FUEL_MIXTURE.value == "FUEL_MIXTURE"
    assert FaultCategory.OVERHEATING.value == "OVERHEATING"
    assert FaultCategory.LUBRICATION.value == "LUBRICATION"
    assert FaultCategory.VIBRATION.value == "VIBRATION"
    assert FaultCategory.SENSOR_ANOMALY.value == "SENSOR_ANOMALY"

    # Telemetry and residual fields verification
    assert "rpm" in PRIMARY_TELEMETRY_FIELDS
    assert "egt_residual" in RESIDUAL_FIELDS
    assert "cht_residual" in RESIDUAL_FIELDS
