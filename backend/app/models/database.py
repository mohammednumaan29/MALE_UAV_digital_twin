"""
Database Configuration & Session Management.
Supports PostgreSQL with SQLite fallback for seamless development/testing.
"""

import os
from pathlib import Path
from typing import Generator
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config.settings import settings
from app.utils.logging import logger


def _sqlite_path_from_url(candidate: str) -> str:
    """Normalize SQLite URLs to an absolute path relative to the project root."""
    relative_path = candidate.replace("sqlite:///", "", 1)
    if relative_path.startswith("./"):
        return f"sqlite:///{(Path(__file__).resolve().parents[2] / relative_path[2:]).resolve().as_posix()}"
    if not Path(relative_path).is_absolute():
        return f"sqlite:///{(Path(__file__).resolve().parents[2] / relative_path).resolve().as_posix()}"
    return candidate


def _postgres_available(candidate: str) -> bool:
    """Detect whether a configured PostgreSQL URL is reachable before binding to it."""
    if not candidate.startswith(("postgresql://", "postgresql+psycopg2://", "postgresql+asyncpg://")):
        return True
    try:
        test_engine = create_engine(candidate, pool_pre_ping=True)
        with test_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:  # pragma: no cover - runtime environment check
        logger.warning("PostgreSQL unavailable for %s; falling back to SQLite. Error: %s", candidate, exc)
        return False


def _resolve_database_url() -> str:
    """Prefer PostgreSQL when available, otherwise fall back to SQLite for local runs and tests."""
    if settings.DATABASE_URL and settings.DATABASE_URL.strip():
        candidate = settings.DATABASE_URL.strip()
        if candidate.startswith("sqlite"):
            return _sqlite_path_from_url(candidate)
        if candidate.startswith(("postgresql://", "postgresql+psycopg2://", "postgresql+asyncpg://")):
            if _postgres_available(candidate):
                return candidate
            return "sqlite:///./rotax914.db"
        return candidate

    postgres_host = os.getenv("POSTGRES_HOST", "localhost")
    postgres_port = os.getenv("POSTGRES_PORT", "5432")
    postgres_db = os.getenv("POSTGRES_DB", "rotax914_db")
    postgres_user = os.getenv("POSTGRES_USER", "rotax_user")
    postgres_password = os.getenv("POSTGRES_PASSWORD", "rotax_pass")
    postgres_url = f"postgresql+psycopg2://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_db}"
    if _postgres_available(postgres_url):
        return postgres_url
    return "sqlite:///./rotax914.db"


database_url = _resolve_database_url()

# SQLite thread safety configuration
connect_args = {}
if database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    database_url,
    connect_args=connect_args,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator:
    """FastAPI dependency for database session lifecycle."""
    try:
        _ensure_table_columns()
    except Exception as exc:  # pragma: no cover - defensive database compatibility guard
        logger.warning("Column compatibility check failed during request session setup: %s", exc)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_mission_result_columns() -> None:
    """Compatibility guard for mission replay tracking in older sqlite/postgres databases."""
    import app.models.mission_result

    table_name = app.models.mission_result.MissionResultModel.__table__.name
    inspector = inspect(engine)
    if not inspector.has_table(table_name):
        return
    existing_cols = {col["name"] for col in inspector.get_columns(table_name)}
    for column in app.models.mission_result.MissionResultModel.__table__.columns:
        if column.name in existing_cols:
            continue
        column_def = column.type.compile(dialect=engine.dialect)
        with engine.begin() as conn:
            conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column.name} {column_def}"))
        logger.info("Added mission replay column '%s' to '%s'", column.name, table_name)


def _ensure_table_columns() -> None:
    """Extend an existing database schema without replacing it. This preserves older local databases while adding Phase 5 fields."""
    import app.models.engine  # noqa: F401
    import app.models.telemetry  # noqa: F401
    import app.models.health  # noqa: F401
    import app.models.fault  # noqa: F401
    import app.models.prediction  # noqa: F401
    import app.models.physics_prediction  # noqa: F401
    import app.models.mission  # noqa: F401
    import app.models.mission_result  # noqa: F401
    import app.models.maintenance  # noqa: F401

    inspector = inspect(engine)
    for model in [
        app.models.fault.FaultRecordModel,
        app.models.health.HealthRecordModel,
        app.models.prediction.PredictionRecordModel,
        app.models.mission.MissionModel,
        app.models.mission_result.MissionResultModel,
        app.models.maintenance.MaintenanceRecordModel,
        app.models.physics_prediction.PhysicsPredictionModel,
    ]:
        table_name = model.__table__.name
        if not inspector.has_table(table_name):
            continue
        existing_cols = {col["name"] for col in inspector.get_columns(table_name)}
        for column in model.__table__.columns:
            if column.name not in existing_cols:
                column_def = column.type.compile(dialect=engine.dialect)
                with engine.begin() as conn:
                    conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column.name} {column_def}"))
                logger.info("Added column '%s' to '%s'", column.name, table_name)
    ensure_mission_result_columns()


def init_db() -> None:
    """Initialize database tables and seed baseline engine record."""
    # Import all models to ensure they are registered with Base.metadata
    import app.models.engine  # noqa: F401
    import app.models.telemetry  # noqa: F401
    import app.models.health  # noqa: F401
    import app.models.fault  # noqa: F401
    import app.models.prediction  # noqa: F401
    import app.models.physics_prediction  # noqa: F401
    import app.models.mission  # noqa: F401
    import app.models.mission_result  # noqa: F401
    import app.models.maintenance  # noqa: F401

    logger.info("Initializing database tables for %s...", database_url.split("@")[-1])
    Base.metadata.create_all(bind=engine)
    _ensure_table_columns()

    # Seed baseline engine if not existing
    from app.models.engine import EngineModel
    from app.models.telemetry import TelemetryModel
    from app.physics.engine_model import physics_engine
    from datetime import datetime, timezone

    db = SessionLocal()
    try:
        default_engine = db.query(EngineModel).filter_by(id="rotax914-uav-01").first()
        if not default_engine:
            default_engine = EngineModel(
                id="rotax914-uav-01",
                model_name="Rotax 914 F Turbocharged",
                serial_number="ROTAX-914-2026-001",
                displacement_cc=1211.2,
                max_continuous_power_kw=73.5,
                takeoff_power_kw=84.5,
                created_at=datetime.now(timezone.utc),
                is_active=True
            )
            db.add(default_engine)
            db.commit()
            logger.info("Seeded default engine 'rotax914-uav-01'")

        baseline = db.query(TelemetryModel).filter_by(engine_id="rotax914-uav-01").first()
        if not baseline:
            expected = physics_engine.predict_state(
                throttle=65.0,
                altitude_ft=10000.0,
                ambient_temperature_c=30.0,
            )
            baseline = TelemetryModel(
                engine_id="rotax914-uav-01",
                timestamp=datetime.now(timezone.utc),
                rpm=5120.0,
                egt_c=640.0,
                cht_c=185.0,
                oil_pressure_bar=4.2,
                oil_temperature_c=92.0,
                fuel_flow_lph=3.3,
                vibration_g=1.8,
                altitude_ft=10000.0,
                ambient_temperature_c=30.0,
                throttle=65.0,
                engine_load=0.76,
                power_kw=53.0,
                expected_rpm=expected["expected_rpm"],
                expected_egt_c=expected["expected_egt_c"],
                expected_cht_c=expected["expected_cht_c"],
                expected_oil_pressure_bar=expected["expected_oil_pressure_bar"],
                expected_oil_temperature_c=expected["expected_oil_temperature_c"],
                expected_fuel_flow_lph=expected["expected_fuel_flow_lph"],
                expected_vibration_g=expected["expected_vibration_g"],
                expected_power_kw=expected["expected_power_kw"],
                active_fault="NORMAL",
                fault_severity=0.0,
            )
            db.add(baseline)
            db.commit()
            logger.info("Seeded baseline telemetry for 'rotax914-uav-01'")
    except Exception as e:
        logger.warning("Engine seed skipped: %s", e)
        db.rollback()
    finally:
        db.close()
