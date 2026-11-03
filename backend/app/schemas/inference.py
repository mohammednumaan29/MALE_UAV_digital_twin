"""Pydantic schemas for live ML inference requests and responses."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class LiveInferenceRequest(BaseModel):
    engine_id: str = Field("rotax914-uav-01", description="Engine identifier")
    telemetry: Dict[str, Any] = Field(..., description="Telemetry frame to assess")
    expected: Optional[Dict[str, Any]] = Field(None, description="Optional expected-state override")


class LiveInferenceResponse(BaseModel):
    engine_health: float = Field(..., description="0-100 health score")
    status: str = Field(..., description="Healthy/Normal/Degraded/Critical status")
    anomaly: bool = Field(..., description="Whether the model flags a live anomaly")
    anomaly_score: float = Field(..., description="Scaled anomaly confidence")
    probable_fault: str = Field(..., description="Most likely fault class")
    fault_probability: float = Field(..., description="Confidence in the predicted fault, as a percent")
    severity: float = Field(..., description="0.0 to 1.0 fault severity")
    estimated_rul_hours: float = Field(..., description="Estimated remaining useful life in hours")
    confidence_range: Dict[str, float] = Field(..., description="RUL lower and upper bounds")
    evidence: Dict[str, Any] = Field(..., description="Residuals and contextual indicators used as evidence")
    affected_region: List[str] = Field(..., description="Affected subsystem region list")
