"""Validation for Phase 15 3D engine region support."""

from app.config.constants import EngineRegion, FaultCategory, FAULT_REGION_MAP
from app.services.live_inference_service import live_inference_service


def test_fault_region_map_uses_standardized_3d_region_names():
    """The backend should expose a single standardized region vocabulary for the 3D model."""
    assert FAULT_REGION_MAP[FaultCategory.OVERHEATING.value] == [
        EngineRegion.CYLINDER_REGION.value,
        EngineRegion.COOLING_REGION.value,
    ]
    assert FAULT_REGION_MAP[FaultCategory.LUBRICATION_DEGRADATION.value] == [
        EngineRegion.LUBRICATION_REGION.value,
        EngineRegion.BEARING_REGION.value,
        EngineRegion.CRANKSHAFT_REGION.value,
    ]
    assert FAULT_REGION_MAP[FaultCategory.ABNORMAL_VIBRATION.value] == [
        EngineRegion.CRANKSHAFT_REGION.value,
        EngineRegion.BEARING_REGION.value,
        EngineRegion.GEARBOX_REGION.value,
        EngineRegion.ENGINE_MOUNT_REGION.value,
    ]


def test_live_inference_payload_exposes_standardized_regions():
    """Runtime payloads should include affected regions in the canonical 3D labels."""
    telemetry = {
        "rpm": 5800,
        "egt_c": 710,
        "cht_c": 150,
        "oil_pressure_bar": 4.0,
        "oil_temperature_c": 96,
        "fuel_flow_lph": 18.2,
        "vibration_g": 0.31,
        "altitude_ft": 10000,
        "ambient_temperature_c": 30,
        "throttle": 65,
        "engine_load": 0.72,
        "power_kw": 52,
    }
    payload = live_inference_service.build_dashboard_payload(telemetry)
    assert "affected_region" in payload
    assert isinstance(payload["affected_region"], list)
    assert payload["affected_region"]
    assert all(region in {item.value for item in EngineRegion} for region in payload["affected_region"])
