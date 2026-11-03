"""
Database Models Package.
Imports all models to ensure registration with Base.metadata.
"""

from app.models.database import Base, engine, SessionLocal, get_db, init_db
from app.models.engine import EngineModel
from app.models.telemetry import TelemetryModel
from app.models.health import HealthRecordModel
from app.models.fault import FaultRecordModel
from app.models.prediction import PredictionRecordModel
from app.models.physics_prediction import PhysicsPredictionModel
from app.models.mission import MissionModel
from app.models.mission_result import MissionResultModel
from app.models.maintenance import MaintenanceRecordModel

__all__ = [
    "Base",
    "engine",
    "SessionLocal",
    "get_db",
    "init_db",
    "EngineModel",
    "TelemetryModel",
    "HealthRecordModel",
    "FaultRecordModel",
    "PredictionRecordModel",
    "PhysicsPredictionModel",
    "MissionModel",
    "MissionResultModel",
    "MaintenanceRecordModel",
]
