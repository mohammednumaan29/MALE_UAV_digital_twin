"""
Telemetry Service Layer.
Coordinates simulation, database persistence, Digital Twin expected state evaluation,
and querying for telemetry history.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.telemetry import TelemetryModel
from app.models.engine import EngineModel
from app.schemas.telemetry import (
    TelemetryCreateRequest,
    TelemetryResponse,
    TelemetryHistoryResponse,
)
from app.physics.engine_model import physics_engine
from app.simulation.engine_simulator import EngineSimulator
from app.utils.logging import logger


class TelemetryService:
    """Service managing real-time engine telemetry and database persistence."""

    def __init__(self, dt_seconds: float = 1.0):
        self.simulator = EngineSimulator(dt_seconds=dt_seconds)
        self.latest_simulated_frame: Optional[Dict[str, Any]] = None

    def _ensure_engine_exists(self, db: Session, engine_id: str) -> None:
        """Ensure foreign-key engine entity exists in the database."""
        engine = db.query(EngineModel).filter_by(id=engine_id).first()
        if not engine:
            new_engine = EngineModel(
                id=engine_id,
                model_name="Rotax 914 F Turbocharged",
                serial_number=f"ROTAX-{engine_id}",
                displacement_cc=1211.2,
                max_continuous_power_kw=73.5,
                takeoff_power_kw=84.5,
                is_active=True
            )
            db.add(new_engine)
            db.commit()

    def insert_telemetry(self, db: Session, telemetry_in: TelemetryCreateRequest) -> TelemetryResponse:
        """
        Persist a telemetry record into PostgreSQL / SQLite.
        If Digital Twin expected values are missing, compute them from the physics model.
        """
        self._ensure_engine_exists(db, telemetry_in.engine_id)

        # Parse timestamp
        if telemetry_in.timestamp:
            try:
                ts = datetime.fromisoformat(telemetry_in.timestamp.replace("Z", "+00:00"))
            except ValueError:
                ts = datetime.now(timezone.utc)
        else:
            ts = datetime.now(timezone.utc)

        # Compute Digital Twin expected values if not provided
        exp_rpm = telemetry_in.expected_rpm
        exp_egt = telemetry_in.expected_egt_c
        exp_cht = telemetry_in.expected_cht_c
        exp_oil_p = telemetry_in.expected_oil_pressure_bar
        exp_oil_t = telemetry_in.expected_oil_temperature_c
        exp_ff = telemetry_in.expected_fuel_flow_lph
        exp_vib = telemetry_in.expected_vibration_g
        exp_pwr = telemetry_in.expected_power_kw

        if None in (exp_rpm, exp_egt, exp_cht, exp_oil_p, exp_oil_t, exp_ff, exp_vib, exp_pwr):
            expected = physics_engine.predict_state(
                throttle=telemetry_in.throttle,
                altitude_ft=telemetry_in.altitude_ft,
                ambient_temperature_c=telemetry_in.ambient_temperature_c
            )
            exp_rpm = exp_rpm if exp_rpm is not None else expected["expected_rpm"]
            exp_egt = exp_egt if exp_egt is not None else expected["expected_egt_c"]
            exp_cht = exp_cht if exp_cht is not None else expected["expected_cht_c"]
            exp_oil_p = exp_oil_p if exp_oil_p is not None else expected["expected_oil_pressure_bar"]
            exp_oil_t = exp_oil_t if exp_oil_t is not None else expected["expected_oil_temperature_c"]
            exp_ff = exp_ff if exp_ff is not None else expected["expected_fuel_flow_lph"]
            exp_vib = exp_vib if exp_vib is not None else expected["expected_vibration_g"]
            exp_pwr = exp_pwr if exp_pwr is not None else expected["expected_power_kw"]

        db_record = TelemetryModel(
            engine_id=telemetry_in.engine_id,
            timestamp=ts,
            rpm=telemetry_in.rpm,
            egt_c=telemetry_in.egt_c,
            cht_c=telemetry_in.cht_c,
            oil_pressure_bar=telemetry_in.oil_pressure_bar,
            oil_temperature_c=telemetry_in.oil_temperature_c,
            fuel_flow_lph=telemetry_in.fuel_flow_lph,
            vibration_g=telemetry_in.vibration_g,
            altitude_ft=telemetry_in.altitude_ft,
            ambient_temperature_c=telemetry_in.ambient_temperature_c,
            throttle=telemetry_in.throttle,
            engine_load=telemetry_in.engine_load,
            power_kw=telemetry_in.power_kw,
            expected_rpm=exp_rpm,
            expected_egt_c=exp_egt,
            expected_cht_c=exp_cht,
            expected_oil_pressure_bar=exp_oil_p,
            expected_oil_temperature_c=exp_oil_t,
            expected_fuel_flow_lph=exp_ff,
            expected_vibration_g=exp_vib,
            expected_power_kw=exp_pwr,
            active_fault=telemetry_in.active_fault or "NORMAL",
            fault_severity=telemetry_in.fault_severity or 0.0,
        )

        db.add(db_record)
        db.commit()
        db.refresh(db_record)

        return self._to_response(db_record)

    def get_latest_telemetry(self, db: Session, engine_id: str = "rotax914-uav-01") -> Optional[TelemetryResponse]:
        """Query the most recent persisted telemetry record for an engine."""
        db_record = (
            db.query(TelemetryModel)
            .filter_by(engine_id=engine_id)
            .order_by(desc(TelemetryModel.timestamp), desc(TelemetryModel.id))
            .first()
        )
        if not db_record:
            return None
        return self._to_response(db_record)

    def get_telemetry_history(
        self,
        db: Session,
        engine_id: str = "rotax914-uav-01",
        limit: int = 50,
        offset: int = 0
    ) -> TelemetryHistoryResponse:
        """Query historical telemetry records ordered chronologically descending."""
        query = db.query(TelemetryModel).filter_by(engine_id=engine_id)
        total = query.count()
        records = (
            query.order_by(desc(TelemetryModel.timestamp), desc(TelemetryModel.id))
            .offset(offset)
            .limit(limit)
            .all()
        )

        return TelemetryHistoryResponse(
            engine_id=engine_id,
            total_records=total,
            limit=limit,
            records=[self._to_response(r) for r in records]
        )

    def _to_response(self, record: TelemetryModel) -> TelemetryResponse:
        """Convert a database record into a Pydantic TelemetryResponse."""
        ts_str = record.timestamp.isoformat() if hasattr(record.timestamp, "isoformat") else str(record.timestamp)
        return TelemetryResponse(
            id=record.id,
            engine_id=record.engine_id,
            timestamp=ts_str,
            rpm=record.rpm,
            egt_c=record.egt_c,
            cht_c=record.cht_c,
            oil_pressure_bar=record.oil_pressure_bar,
            oil_temperature_c=record.oil_temperature_c,
            fuel_flow_lph=record.fuel_flow_lph,
            vibration_g=record.vibration_g,
            altitude_ft=record.altitude_ft,
            ambient_temperature_c=record.ambient_temperature_c,
            throttle=record.throttle,
            engine_load=record.engine_load,
            power_kw=record.power_kw,
            expected_rpm=record.expected_rpm,
            expected_egt_c=record.expected_egt_c,
            expected_cht_c=record.expected_cht_c,
            expected_oil_pressure_bar=record.expected_oil_pressure_bar,
            expected_oil_temperature_c=record.expected_oil_temperature_c,
            expected_fuel_flow_lph=record.expected_fuel_flow_lph,
            expected_vibration_g=record.expected_vibration_g,
            expected_power_kw=record.expected_power_kw,
            active_fault=record.active_fault,
            fault_severity=record.fault_severity,
        )


telemetry_service = TelemetryService()
