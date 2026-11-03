"""
Maintenance Records Database Model.
Stores maintenance recommendations and service logs.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from app.models.database import Base


class MaintenanceRecordModel(Base):
    __tablename__ = "maintenance_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    engine_id = Column(String(64), ForeignKey("engines.id"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    maintenance_type = Column(String(64), nullable=False)
    description = Column(Text, nullable=False)
    related_fault = Column(String(64), nullable=True)
    notes = Column(Text, nullable=True)
    severity_level = Column(String(32), default="INFO")
    technician = Column(String(64), nullable=True)
