"""
Predictions Database Model.
Stores physics digital twin state predictions.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.models.database import Base


class PredictionRecordModel(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    engine_id = Column(String(64), ForeignKey("engines.id"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    anomaly_score = Column(Float, nullable=True)
    anomaly_status = Column(String(32), nullable=True)
    fault_type = Column(String(64), nullable=True)
    fault_probability = Column(Float, nullable=True)
    rul_hours = Column(Float, nullable=True)
    rul_lower = Column(Float, nullable=True)
    rul_upper = Column(Float, nullable=True)
    severity = Column(Float, nullable=True)
    evidence = Column(Text, nullable=True)
    affected_region = Column(Text, nullable=True)

    throttle = Column(Float, nullable=True)
    altitude_ft = Column(Float, nullable=True)
    ambient_temperature_c = Column(Float, nullable=True)

    predicted_rpm = Column(Float, nullable=True)
    predicted_egt_c = Column(Float, nullable=True)
    predicted_cht_c = Column(Float, nullable=True)
    predicted_oil_pressure_bar = Column(Float, nullable=True)
    predicted_oil_temperature_c = Column(Float, nullable=True)
    predicted_fuel_flow_lph = Column(Float, nullable=True)
    predicted_vibration_g = Column(Float, nullable=True)
    predicted_power_kw = Column(Float, nullable=True)

    engine = relationship("EngineModel", back_populates="prediction_records")
