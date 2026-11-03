"""
Missions Database Model.
Stores flight mission profiles and execution metadata.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from app.models.database import Base


class MissionModel(Base):
    __tablename__ = "missions"

    id = Column(String(64), primary_key=True, index=True)
    engine_id = Column(String(64), ForeignKey("engines.id"), nullable=False, index=True)
    mission_id = Column(String(64), nullable=True, index=True)
    mission_name = Column(String(128), nullable=False)
    mission_type = Column(String(64), default="STANDARD_SURVEILLANCE")
    start_time = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    end_time = Column(DateTime(timezone=True), nullable=True)
    duration = Column(Float, nullable=True)
    altitude = Column(Float, nullable=True)
    ambient_temperature = Column(Float, nullable=True)
    throttle = Column(Float, nullable=True)
    status = Column(String(32), default="PLANNED")  # PLANNED, IN_PROGRESS, COMPLETED, ABORTED

    # Relationship
    results = relationship("MissionResultModel", back_populates="mission", uselist=False)
