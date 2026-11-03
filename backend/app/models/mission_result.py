"""
Mission Results Database Model.
Stores post-mission health trajectory summaries and risk assessments.
"""

from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.models.database import Base


class MissionResultModel(Base):
    __tablename__ = "mission_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    mission_id = Column(String(64), ForeignKey("missions.id"), unique=True, nullable=False)

    duration_hours = Column(Float, nullable=True)
    health_start = Column(Float, nullable=True)
    health_end = Column(Float, nullable=True)
    initial_health = Column(Float, nullable=True)
    final_health = Column(Float, nullable=True)
    predicted_degradation = Column(Float, nullable=True)
    mission_risk = Column(String(32), default="LOW")  # LOW, MEDIUM, HIGH, CRITICAL
    estimated_rul = Column(Float, nullable=True)
    recommendations = Column(Text, nullable=True)
    initial_rul = Column(Float, nullable=True)
    final_rul = Column(Float, nullable=True)
    recommendation = Column(Text, nullable=True)
    telemetry_snapshot = Column(Text, nullable=True)
    health_trend_snapshot = Column(Text, nullable=True)
    rul_trend_snapshot = Column(Text, nullable=True)
    fault_events_snapshot = Column(Text, nullable=True)

    # Relationship
    mission = relationship("MissionModel", back_populates="results")
