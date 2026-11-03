"""
Pydantic Schemas for Fault and Degradation Models.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict
from app.config.constants import FaultCategory


class FaultStateSchema(BaseModel):
    """Schema representing active injected fault and degradation severity."""

    fault_type: FaultCategory = Field(
        default=FaultCategory.NORMAL,
        description="Active fault category"
    )
    severity: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Degradation severity fraction (0.0 to 1.0)"
    )
    severity_pct: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Degradation severity percentage (0% to 100%)"
    )
    timestamp: str = Field(
        ...,
        description="ISO 8601 UTC timestamp of last fault update"
    )
    description: str = Field(
        default="Normal healthy operation",
        description="Human-readable description of fault mechanism"
    )


class FaultActivationRequest(BaseModel):
    """Input payload for fault activation or adjustment."""

    engine_id: str = Field(default="rotax914-uav-01", description="Engine identifier")
    fault_type: FaultCategory | str = Field(default=FaultCategory.NORMAL, description="Fault category to activate")
    severity: float = Field(default=0.0, ge=0.0, le=1.0, description="Severity between 0.0 and 1.0")


class FaultActivationResponse(FaultStateSchema):
    """Response payload for fault activation."""

    model_config = ConfigDict(from_attributes=True)
    engine_id: str = Field(default="rotax914-uav-01", description="Engine identifier")
    active: bool = Field(default=True, description="Whether the fault is active")


class MissionSimulationRequest(BaseModel):
    """Request model for mission evaluation."""

    engine_id: str = Field(default="rotax914-uav-01", description="Engine identifier")
    duration_hours: float = Field(..., gt=0.0, le=24.0, description="Mission duration in hours")
    altitude_ft: float = Field(..., ge=0.0, le=40000.0, description="Planned mission altitude in feet")
    ambient_temperature_c: float = Field(..., ge=-60.0, le=65.0, description="Ambient flight temperature in Celsius")
    throttle: float = Field(..., ge=0.0, le=100.0, description="Average mission throttle percentage")
    mission_type: str = Field(default="SURVEILLANCE", description="Mission classification")


class MissionSimulationResponse(BaseModel):
    """Response model for mission simulation.Results."""

    mission_id: str
    engine_id: str
    status: str = Field(default="COMPLETED")
    duration_hours: float
    mission_type: str
    altitude_ft: float
    ambient_temperature_c: float
    throttle: float
    health_start: float
    health_end: float
    predicted_degradation: float
    mission_risk: str
    estimated_rul: float
    recommendations: str


class ReplayResponse(BaseModel):
    """Response model for mission replay."""

    mission_id: str
    engine_id: str
    mission_type: str
    telemetry: List[Dict[str, Any]] = Field(default_factory=list)
    health_trend: List[Dict[str, Any]] = Field(default_factory=list)
    fault_events: List[Dict[str, Any]] = Field(default_factory=list)
    rul_trend: List[Dict[str, Any]] = Field(default_factory=list)


class MaintenanceAdvisoryResponse(BaseModel):
    """Decision-support maintenance recommendation for an engine."""

    engine_id: str
    fault: str
    trend: str
    severity: str
    severity_value: float
    recommendation: str
    description: str
    timestamp: str
    maintenance_type: str = "ADVISORY"
    related_fault: Optional[str] = None


class EngineStateResponse(BaseModel):
    """Engine-wide state snapshot for dashboard use."""

    engine_id: str
    model_name: str
    engine_status: str
    telemetry: Optional[Dict[str, Any]] = None
    health: Optional[Dict[str, Any]] = None
    latest_fault: Optional[Dict[str, Any]] = None
    latest_prediction: Optional[Dict[str, Any]] = None
    active_fault: Optional[str] = None
    severity: Optional[float] = None
