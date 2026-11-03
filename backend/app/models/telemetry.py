"""
Telemetry Database Model.
Stores raw simulated/measured telemetry, Digital Twin expected values, and fault states.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.models.database import Base


class TelemetryModel(Base):
    __tablename__ = "telemetry"

    id = Column(Integer, primary_key=True, autoincrement=True)
    engine_id = Column(String(64), ForeignKey("engines.id"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    # Primary Measured / Simulated Telemetry
    rpm = Column(Float, nullable=False)
    egt_c = Column(Float, nullable=False)
    cht_c = Column(Float, nullable=False)
    oil_pressure_bar = Column(Float, nullable=False)
    oil_temperature_c = Column(Float, nullable=False)
    fuel_flow_lph = Column(Float, nullable=False)
    vibration_g = Column(Float, nullable=False)
    altitude_ft = Column(Float, nullable=False)
    ambient_temperature_c = Column(Float, nullable=False)
    throttle = Column(Float, nullable=False)
    engine_load = Column(Float, nullable=False)
    power_kw = Column(Float, nullable=False)

    # Digital Twin Expected Values (Section 4 Requirement)
    expected_rpm = Column(Float, nullable=True)
    expected_egt_c = Column(Float, nullable=True)
    expected_cht_c = Column(Float, nullable=True)
    expected_oil_pressure_bar = Column(Float, nullable=True)
    expected_oil_temperature_c = Column(Float, nullable=True)
    expected_fuel_flow_lph = Column(Float, nullable=True)
    expected_vibration_g = Column(Float, nullable=True)
    expected_power_kw = Column(Float, nullable=True)

    # Fault Metadata
    active_fault = Column(String(32), default="NORMAL")
    fault_severity = Column(Float, default=0.0)

    # Relationship
    engine = relationship("EngineModel", back_populates="telemetry_records")

    __table_args__ = (
        Index("idx_telemetry_engine_time", "engine_id", "timestamp"),
    )
