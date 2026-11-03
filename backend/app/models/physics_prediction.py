"""Physics prediction storage model for Phase 5 database pipeline."""

from datetime import datetime, timezone
from sqlalchemy import Column, Float, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from app.models.database import Base


class PhysicsPredictionModel(Base):
    __tablename__ = "physics_predictions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    engine_id = Column(String(64), ForeignKey("engines.id"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    expected_egt = Column(Float, nullable=True)
    expected_cht = Column(Float, nullable=True)
    expected_oil_pressure = Column(Float, nullable=True)
    expected_oil_temperature = Column(Float, nullable=True)
    expected_fuel_flow = Column(Float, nullable=True)
    expected_vibration = Column(Float, nullable=True)
    expected_rpm = Column(Float, nullable=True)

    rpm_residual = Column(Float, nullable=True)
    egt_residual = Column(Float, nullable=True)
    cht_residual = Column(Float, nullable=True)
    oil_pressure_residual = Column(Float, nullable=True)
    oil_temperature_residual = Column(Float, nullable=True)
    fuel_flow_residual = Column(Float, nullable=True)
    vibration_residual = Column(Float, nullable=True)

    engine = relationship("EngineModel", back_populates="physics_predictions")
