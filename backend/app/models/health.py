"""
Health Records Database Model.
Stores health indices, health statuses, and degradation trends.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.models.database import Base


class HealthRecordModel(Base):
    __tablename__ = "health_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    engine_id = Column(String(64), ForeignKey("engines.id"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    health_index = Column(Float, nullable=False)           # 0.0 to 100.0
    health_status = Column(String(32), nullable=False)     # HEALTHY, DEGRADED, CRITICAL
    status = Column(String(32), nullable=True)             # compatibility alias for the system's health outcome
    degradation_trend = Column(String(32), default="STABLE") # STABLE, SLOW_DEGRADATION, RAPID_DEGRADATION
    details = Column(Text, nullable=True)

    # Relationship
    engine = relationship("EngineModel", back_populates="health_records")
