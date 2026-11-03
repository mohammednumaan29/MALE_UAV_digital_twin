"""
Pydantic Schemas for Telemetry Data.
Covers primary telemetry fields, Digital Twin expected values, and API request/responses.
"""

from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class TelemetryBase(BaseModel):
    """Base fields present in measured/simulated telemetry."""
    model_config = ConfigDict(extra="ignore")

    rpm: float = Field(..., ge=0.0, description="Engine rotational speed (RPM)")
    egt_c: float = Field(..., description="Exhaust gas temperature (°C)")
    cht_c: float = Field(..., description="Cylinder head temperature (°C)")
    oil_pressure_bar: float = Field(..., ge=0.0, description="Engine oil pressure (bar)")
    oil_temperature_c: float = Field(..., description="Engine oil temperature (°C)")
    fuel_flow_lph: float = Field(..., ge=0.0, description="Fuel flow rate (L/h)")
    vibration_g: float = Field(..., ge=0.0, description="Mechanical vibration level (g RMS)")
    altitude_ft: float = Field(..., ge=0.0, description="Flight altitude (ft)")
    ambient_temperature_c: float = Field(..., description="Outside air temperature (°C)")
    throttle: float = Field(..., ge=0.0, le=100.0, description="Throttle position percentage (%)")
    engine_load: float = Field(..., ge=0.0, le=1.0, description="Normalized engine load fraction (0.0 to 1.0)")
    power_kw: float = Field(..., ge=0.0, description="Calculated engine brake power (kW)")

    # Digital Twin Expected Values (Optional upon ingestion, computed automatically if omitted)
    expected_rpm: Optional[float] = Field(None, description="Physics expected RPM")
    expected_egt_c: Optional[float] = Field(None, description="Physics expected EGT (°C)")
    expected_cht_c: Optional[float] = Field(None, description="Physics expected CHT (°C)")
    expected_oil_pressure_bar: Optional[float] = Field(None, description="Physics expected oil pressure (bar)")
    expected_oil_temperature_c: Optional[float] = Field(None, description="Physics expected oil temperature (°C)")
    expected_fuel_flow_lph: Optional[float] = Field(None, description="Physics expected fuel flow (L/h)")
    expected_vibration_g: Optional[float] = Field(None, description="Physics expected vibration (g RMS)")
    expected_power_kw: Optional[float] = Field(None, description="Physics expected power (kW)")

    # Active Fault Metadata
    active_fault: Optional[str] = Field("NORMAL", description="Active fault name")
    fault_severity: Optional[float] = Field(0.0, ge=0.0, le=1.0, description="Active fault severity (0.0 to 1.0)")


class TelemetryCreateRequest(TelemetryBase):
    """Payload for POST /api/telemetry."""

    engine_id: str = Field(default="rotax914-uav-01", description="Engine identifier")
    timestamp: Optional[str] = Field(None, description="ISO 8601 timestamp (auto-generated if omitted)")


class TelemetryResponse(TelemetryBase):
    """Response model for persisted telemetry records."""
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Unique telemetry record database ID")
    engine_id: str = Field(..., description="Engine identifier")
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp")


# Alias for backward compatibility with simulator frames
TelemetryData = TelemetryBase


class TelemetryHistoryResponse(BaseModel):
    """Response model for GET /api/telemetry/history."""

    engine_id: str
    total_records: int
    limit: int
    records: List[TelemetryResponse]
