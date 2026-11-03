"""
Engine Entity Database Model.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, Boolean
from sqlalchemy.orm import relationship
from app.models.database import Base


class EngineModel(Base):
    __tablename__ = "engines"

    id = Column(String(64), primary_key=True, index=True)
    model_name = Column(String(128), nullable=False, default="Rotax 914 F")
    serial_number = Column(String(64), nullable=False)
    displacement_cc = Column(Float, nullable=False, default=1211.2)
    max_continuous_power_kw = Column(Float, nullable=False, default=73.5)
    takeoff_power_kw = Column(Float, nullable=False, default=84.5)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True)

    # Relationships
    telemetry_records = relationship("TelemetryModel", back_populates="engine", cascade="all, delete-orphan")
    health_records = relationship("HealthRecordModel", back_populates="engine", cascade="all, delete-orphan")
    fault_records = relationship("FaultRecordModel", back_populates="engine", cascade="all, delete-orphan")
    prediction_records = relationship("PredictionRecordModel", back_populates="engine", cascade="all, delete-orphan")
    physics_predictions = relationship("PhysicsPredictionModel", back_populates="engine", cascade="all, delete-orphan")
