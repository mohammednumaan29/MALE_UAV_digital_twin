"""
Pydantic Schemas for Digital Twin State Predictions.
"""

from pydantic import BaseModel, Field
from typing import Optional


class DigitalTwinPredictRequest(BaseModel):
    """Input operating conditions for the physics-based digital twin."""

    throttle: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Throttle setting percentage (0% to 100%)",
        examples=[65.0]
    )
    altitude_ft: float = Field(
        ...,
        ge=0.0,
        le=35000.0,
        description="Flight altitude in feet above sea level",
        examples=[10000.0]
    )
    ambient_temperature_c: float = Field(
        ...,
        ge=-60.0,
        le=65.0,
        description="Outside ambient air temperature in degrees Celsius",
        examples=[15.0]
    )
    rpm_override: Optional[float] = Field(
        None,
        ge=800.0,
        le=6500.0,
        description="Optional forced RPM for observer/comparison mode"
    )


class DigitalTwinPredictResponse(BaseModel):
    """Output expected engine state predicted by the physics-based digital twin."""

    expected_rpm: float = Field(..., description="Expected engine rotational speed (RPM)")
    expected_egt_c: float = Field(..., description="Expected exhaust gas temperature (°C)")
    expected_cht_c: float = Field(..., description="Expected cylinder head temperature (°C)")
    expected_oil_pressure_bar: float = Field(..., description="Expected lubricating oil pressure (bar)")
    expected_oil_temperature_c: float = Field(..., description="Expected lubricating oil temperature (°C)")
    expected_fuel_flow_lph: float = Field(..., description="Expected volumetric fuel flow (L/h)")
    expected_vibration_g: float = Field(..., description="Expected baseline mechanical vibration (g RMS)")
    expected_power_kw: float = Field(..., description="Expected brake power output (kW)")
    expected_torque_nm: float = Field(..., description="Expected engine shaft torque (N·m)")

    # Additional physics details
    engine_load: Optional[float] = Field(None, description="Calculated engine load fraction (0.0 to 1.0)")
    manifold_pressure_bar: Optional[float] = Field(None, description="Manifold absolute pressure (bar)")
    ambient_pressure_bar: Optional[float] = Field(None, description="Ambient static pressure (bar)")
    air_density_kgm3: Optional[float] = Field(None, description="Ambient air density (kg/m³)")
