"""
Fault Records Database Model.
Stores active and historical fault injection events.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.models.database import Base


class FaultRecordModel(Base):
    __tablename__ = "faults"

    id = Column(Integer, primary_key=True, autoincrement=True)
    engine_id = Column(String(64), ForeignKey("engines.id"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    fault_type = Column(String(64), nullable=False)    # FUEL_MIXTURE_DEGRADATION, OVERHEATING, etc.
    severity = Column(Float, nullable=False)            # 0.0 to 1.0
    active = Column(String(16), default="ACTIVE")       # ACTIVE / INACTIVE
    status = Column(String(32), default="ACTIVE")       # INJECTED, ACTIVE, RESOLVED
    source = Column(String(64), default="SIMULATOR")    # SIMULATOR, FAULT_INJECTOR, ML, MANUAL

    # Relationship
    engine = relationship("EngineModel", back_populates="fault_records")
