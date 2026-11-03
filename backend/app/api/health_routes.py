"""
Health, fault, mission, and engine-state API endpoints.
"""

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.config.constants import FaultCategory, SYSTEM_DISCLAIMER, canonical_fault_name
from app.config.settings import settings
from app.models.database import get_db, ensure_mission_result_columns
from app.models.engine import EngineModel
from app.models.fault import FaultRecordModel
from app.models.health import HealthRecordModel
from app.models.mission import MissionModel
from app.models.mission_result import MissionResultModel
from app.models.prediction import PredictionRecordModel
from app.models.telemetry import TelemetryModel
from app.schemas.fault import (
    EngineStateResponse,
    FaultActivationRequest,
    FaultActivationResponse,
    MaintenanceAdvisoryResponse,
    MissionSimulationRequest,
    MissionSimulationResponse,
    ReplayResponse,
    FaultStateSchema,
)
from app.services.maintenance_service import maintenance_advisory_service
from app.services.mission_service import mission_simulation_service
from app.simulation.fault_injector import SharedFaultState
from app.utils.logging import logger

router = APIRouter(tags=["System"])


def _decode_json_field(raw: Any) -> Any:
    """Convert persisted JSON text back into native Python structures for API responses."""
    if raw is None:
        return None
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw
    return raw


def _fault_description(fault_name: str) -> str:
    pairs = {
        "NORMAL": "Normal healthy operation.",
        "FUEL_MIXTURE_DEGRADATION": "Fuel/mixture delivery degradation affecting combustion efficiency and thermal balance.",
        "OVERHEATING": "Thermal overload in the cylinder and cooling region.",
        "LUBRICATION_DEGRADATION": "Reduced oil film strength and lubrication efficiency.",
        "ABNORMAL_VIBRATION": "Mechanical imbalance or mounting-related vibration growth.",
        "SENSOR_ANOMALY": "Sensor drift, spike, or stuck reading not directly caused by engine physics.",
    }
    return pairs.get(fault_name, "Fault state update.")


@router.get("/health", summary="Service Health Check")
async def get_health() -> Dict[str, str]:
    """Return operational status of the Rotax 914 Digital Twin backend service."""
    logger.debug("Health check requested")
    return {
        "status": "ok",
        "service": settings.SERVICE_NAME
    }


@router.get("/system/info", summary="System Metadata and Architecture Info")
async def get_system_info() -> Dict[str, Any]:
    """Return system metadata, physics model status, and ML pipeline configuration."""
    logger.debug("System info requested")
    return {
        "application": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "physics_model": settings.PHYSICS_MODEL_INFO,
        "ml_models": settings.ML_MODELS_INFO,
        "disclaimer": SYSTEM_DISCLAIMER
    }


@router.get("/health/{engine_id}", summary="Get latest engine health record")
async def get_engine_health(engine_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Retrieve the latest persisted health reading for an engine."""
    record = (
        db.query(HealthRecordModel)
        .filter(HealthRecordModel.engine_id == engine_id)
        .order_by(desc(HealthRecordModel.timestamp), desc(HealthRecordModel.id))
        .first()
    )
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No health records found for engine '{engine_id}'.")
    return {
        "engine_id": record.engine_id,
        "timestamp": record.timestamp.isoformat(),
        "health_index": record.health_index,
        "status": record.health_status or record.status,
        "degradation_trend": record.degradation_trend,
        "details": record.details,
    }


@router.get("/faults/{engine_id}", summary="Get fault history for engine")
async def get_engine_faults(engine_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Return all fault events for an engine ordered by timestamp."""
    faults = (
        db.query(FaultRecordModel)
        .filter(FaultRecordModel.engine_id == engine_id)
        .order_by(desc(FaultRecordModel.timestamp), desc(FaultRecordModel.id))
        .all()
    )
    return {
        "engine_id": engine_id,
        "faults": [
            {
                "id": f.id,
                "engine_id": f.engine_id,
                "timestamp": f.timestamp.isoformat(),
                "fault_type": f.fault_type,
                "severity": f.severity,
                "active": f.active,
                "status": f.status,
                "source": f.source,
            }
            for f in faults
        ],
    }


@router.get("/predictions/{engine_id}", summary="Get prediction history for engine")
async def get_engine_predictions(engine_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Return stored prediction records for the engine."""
    predictions = (
        db.query(PredictionRecordModel)
        .filter(PredictionRecordModel.engine_id == engine_id)
        .order_by(desc(PredictionRecordModel.timestamp), desc(PredictionRecordModel.id))
        .all()
    )
    return {
        "engine_id": engine_id,
        "predictions": [
            {
                "id": p.id,
                "timestamp": p.timestamp.isoformat(),
                "anomaly_score": p.anomaly_score,
                "anomaly_status": p.anomaly_status,
                "fault_type": p.fault_type,
                "fault_probability": p.fault_probability,
                "rul_hours": p.rul_hours,
                "rul_lower": p.rul_lower,
                "rul_upper": p.rul_upper,
                "severity": p.severity,
                "evidence": _decode_json_field(p.evidence) or {},
                "affected_region": _decode_json_field(p.affected_region) or [],
            }
            for p in predictions
        ],
    }


@router.get("/rul/{engine_id}", summary="Get latest RUL estimate for engine")
async def get_engine_rul(engine_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Return the latest remaining useful life estimate."""
    record = (
        db.query(PredictionRecordModel)
        .filter(PredictionRecordModel.engine_id == engine_id)
        .order_by(desc(PredictionRecordModel.timestamp), desc(PredictionRecordModel.id))
        .first()
    )
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No RUL predictions found for engine '{engine_id}'.")
    return {
        "engine_id": engine_id,
        "timestamp": record.timestamp.isoformat(),
        "rul_hours": record.rul_hours,
        "rul_lower": record.rul_lower,
        "rul_upper": record.rul_upper,
        "fault_type": record.fault_type,
        "severity": record.severity,
    }


@router.get("/fault/status", response_model=FaultStateSchema, summary="Get current fault state")
async def get_fault_status() -> FaultStateSchema:
    """Return the current shared fault state used by the simulator."""
    state = SharedFaultState().read_state()
    fault_name = canonical_fault_name(state.get("active_fault", FaultCategory.NORMAL.value))
    severity_value = float(state.get("target_severity", 0.0))
    severity_pct = float(state.get("target_severity_pct", severity_value * 100.0))
    return FaultStateSchema(
        fault_type=FaultCategory(fault_name),
        severity=severity_value,
        severity_pct=severity_pct,
        timestamp=state.get("timestamp", datetime.now(timezone.utc).isoformat()),
        description=_fault_description(fault_name),
    )


@router.post("/fault/activate", response_model=FaultActivationResponse, summary="Activate a fault")
async def activate_fault(payload: FaultActivationRequest, db: Session = Depends(get_db)) -> FaultActivationResponse:
    """Activate a fault in the shared state and record it as an API-originated fault event."""
    fault_name = canonical_fault_name(payload.fault_type)
    controller = SharedFaultState()
    state = controller.set_fault(fault_name, payload.severity * 100.0)

    fault_enum = FaultCategory(fault_name) if fault_name in {item.value for item in FaultCategory} else FaultCategory.NORMAL
    fault_record = FaultRecordModel(
        engine_id=payload.engine_id,
        timestamp=datetime.now(timezone.utc),
        fault_type=fault_name,
        severity=float(state.get("target_severity", payload.severity)),
        active="ACTIVE",
        status="ACTIVE",
        source="API",
    )
    db.add(fault_record)
    db.commit()

    return FaultActivationResponse(
        engine_id=payload.engine_id,
        fault_type=fault_enum,
        severity=float(state.get("target_severity", payload.severity)),
        severity_pct=float(state.get("target_severity_pct", payload.severity * 100.0)),
        timestamp=state.get("timestamp", datetime.now(timezone.utc).isoformat()),
        description=_fault_description(fault_name),
        active=True,
    )


@router.post("/fault/deactivate", response_model=FaultActivationResponse, summary="Clear active fault")
async def deactivate_fault(payload: FaultActivationRequest = FaultActivationRequest(engine_id="rotax914-uav-01", fault_type=FaultCategory.NORMAL, severity=0.0), db: Session = Depends(get_db)) -> FaultActivationResponse:
    """End all active fault injection by resetting the shared state to NORMAL."""
    controller = SharedFaultState()
    state = controller.clear()
    fault_record = FaultRecordModel(
        engine_id=payload.engine_id,
        timestamp=datetime.now(timezone.utc),
        fault_type=FaultCategory.NORMAL.value,
        severity=0.0,
        active="INACTIVE",
        status="RESOLVED",
        source="API",
    )
    db.add(fault_record)
    db.commit()

    return FaultActivationResponse(
        engine_id=payload.engine_id,
        fault_type=FaultCategory.NORMAL,
        severity=0.0,
        severity_pct=0.0,
        timestamp=state.get("timestamp", datetime.now(timezone.utc).isoformat()),
        description=_fault_description(FaultCategory.NORMAL.value),
        active=False,
    )


@router.get("/maintenance/{engine_id}", response_model=MaintenanceAdvisoryResponse, summary="Get engine maintenance advisory")
@router.get("/maintenance/advisory/{engine_id}", response_model=MaintenanceAdvisoryResponse, summary="Get engine maintenance advisory")
async def get_maintenance_advisory(engine_id: str, db: Session = Depends(get_db)) -> MaintenanceAdvisoryResponse:
    """Generate a decision-support maintenance recommendation from fault and health trends."""
    engine = db.query(EngineModel).filter(EngineModel.id == engine_id).first()
    if not engine:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Engine '{engine_id}' not found.")

    advisory = maintenance_advisory_service.generate_advisory(engine_id, db)
    return MaintenanceAdvisoryResponse(**advisory)


@router.get("/engine/{engine_id}/state", response_model=EngineStateResponse, summary="Get full engine state snapshot")
async def get_engine_state(engine_id: str, db: Session = Depends(get_db)) -> EngineStateResponse:
    """Return the engine metadata, latest telemetry, health, fault, and prediction in one record."""
    engine = db.query(EngineModel).filter(EngineModel.id == engine_id).first()
    if not engine:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Engine '{engine_id}' not found.")

    latest_telemetry = (
        db.query(TelemetryModel)
        .filter(TelemetryModel.engine_id == engine_id)
        .order_by(desc(TelemetryModel.timestamp), desc(TelemetryModel.id))
        .first()
    )
    latest_health = (
        db.query(HealthRecordModel)
        .filter(HealthRecordModel.engine_id == engine_id)
        .order_by(desc(HealthRecordModel.timestamp), desc(HealthRecordModel.id))
        .first()
    )
    latest_fault = (
        db.query(FaultRecordModel)
        .filter(FaultRecordModel.engine_id == engine_id)
        .order_by(desc(FaultRecordModel.timestamp), desc(FaultRecordModel.id))
        .first()
    )
    latest_prediction = (
        db.query(PredictionRecordModel)
        .filter(PredictionRecordModel.engine_id == engine_id)
        .order_by(desc(PredictionRecordModel.timestamp), desc(PredictionRecordModel.id))
        .first()
    )

    telemetry_data = None
    if latest_telemetry:
        telemetry_data = {
            "id": latest_telemetry.id,
            "timestamp": latest_telemetry.timestamp.isoformat(),
            "rpm": latest_telemetry.rpm,
            "egt_c": latest_telemetry.egt_c,
            "cht_c": latest_telemetry.cht_c,
            "oil_pressure_bar": latest_telemetry.oil_pressure_bar,
            "oil_temperature_c": latest_telemetry.oil_temperature_c,
            "fuel_flow_lph": latest_telemetry.fuel_flow_lph,
            "vibration_g": latest_telemetry.vibration_g,
            "altitude_ft": latest_telemetry.altitude_ft,
            "ambient_temperature_c": latest_telemetry.ambient_temperature_c,
            "throttle": latest_telemetry.throttle,
            "engine_load": latest_telemetry.engine_load,
            "power_kw": latest_telemetry.power_kw,
        }

    health_data = None
    if latest_health:
        health_data = {
            "timestamp": latest_health.timestamp.isoformat(),
            "health_index": latest_health.health_index,
            "status": latest_health.health_status or latest_health.status,
            "degradation_trend": latest_health.degradation_trend,
        }

    fault_data = None
    if latest_fault:
        fault_data = {
            "timestamp": latest_fault.timestamp.isoformat(),
            "fault_type": latest_fault.fault_type,
            "severity": latest_fault.severity,
            "active": latest_fault.active,
            "status": latest_fault.status,
            "source": latest_fault.source,
        }

    prediction_data = None
    if latest_prediction:
        prediction_data = {
            "timestamp": latest_prediction.timestamp.isoformat(),
            "anomaly_score": latest_prediction.anomaly_score,
            "anomaly_status": latest_prediction.anomaly_status,
            "fault_type": latest_prediction.fault_type,
            "fault_probability": latest_prediction.fault_probability,
            "rul_hours": latest_prediction.rul_hours,
            "rul_lower": latest_prediction.rul_lower,
            "rul_upper": latest_prediction.rul_upper,
            "evidence": _decode_json_field(latest_prediction.evidence) or {},
            "affected_region": _decode_json_field(latest_prediction.affected_region) or [],
        }

    return EngineStateResponse(
        engine_id=engine.id,
        model_name=engine.model_name,
        engine_status="ACTIVE" if engine.is_active else "INACTIVE",
        telemetry=telemetry_data,
        health=health_data,
        latest_fault=fault_data,
        latest_prediction=prediction_data,
        active_fault=fault_data["fault_type"] if fault_data else "NORMAL",
        severity=fault_data["severity"] if fault_data else 0.0,
    )


@router.post("/mission/simulate", response_model=MissionSimulationResponse, summary="Simulate a mission")
async def simulate_mission(payload: MissionSimulationRequest, db: Session = Depends(get_db)) -> MissionSimulationResponse:
    """Create a mission record and a degradation assessment using the existing mission profile architecture."""
    engine = db.query(EngineModel).filter(EngineModel.id == payload.engine_id).first()
    if not engine:
        engine = EngineModel(
            id=payload.engine_id,
            model_name="Rotax 914 F Turbocharged",
            serial_number=f"ROTAX-{payload.engine_id}",
            displacement_cc=1211.2,
            max_continuous_power_kw=73.5,
            takeoff_power_kw=84.5,
            is_active=True,
        )
        db.add(engine)
        db.commit()

    mission_summary = mission_simulation_service.simulate(
        engine_id=payload.engine_id,
        duration_hours=payload.duration_hours,
        altitude_ft=payload.altitude_ft,
        ambient_temperature_c=payload.ambient_temperature_c,
        throttle=payload.throttle,
        mission_type=payload.mission_type,
    )
    ensure_mission_result_columns()

    mission_id = str(uuid4())
    start_time = datetime.now(timezone.utc)
    end_time = start_time + timedelta(hours=float(payload.duration_hours))
    mission = MissionModel(
        id=mission_id,
        engine_id=payload.engine_id,
        mission_id=mission_id,
        mission_name=f"{payload.mission_type}-{payload.engine_id}",
        mission_type=payload.mission_type,
        start_time=start_time,
        end_time=end_time,
        duration=payload.duration_hours,
        altitude=payload.altitude_ft,
        ambient_temperature=payload.ambient_temperature_c,
        throttle=payload.throttle,
        status="COMPLETED",
    )
    db.add(mission)

    result = MissionResultModel(
        mission_id=mission_id,
        duration_hours=mission_summary["duration_hours"],
        health_start=mission_summary["health_start"],
        health_end=mission_summary["health_end"],
        initial_health=mission_summary["health_start"],
        final_health=mission_summary["health_end"],
        predicted_degradation=mission_summary["predicted_degradation"],
        mission_risk=mission_summary["mission_risk"],
        estimated_rul=mission_summary["estimated_rul"],
        recommendations=mission_summary["recommendations"],
        initial_rul=max(0.0, mission_summary["health_start"] / 5.0),
        final_rul=max(0.0, mission_summary["health_end"] / 5.0),
        recommendation=mission_summary["recommendations"],
        telemetry_snapshot=json.dumps(mission_summary.get("timeline", [])),
        health_trend_snapshot=json.dumps(mission_summary.get("health_trend", [])),
        rul_trend_snapshot=json.dumps(mission_summary.get("rul_trend", [])),
        fault_events_snapshot=json.dumps([]),
    )
    db.add(result)
    db.commit()
    return MissionSimulationResponse(
        mission_id=mission_id,
        engine_id=payload.engine_id,
        status="COMPLETED",
        duration_hours=mission_summary["duration_hours"],
        mission_type=mission_summary["mission_type"],
        altitude_ft=mission_summary["altitude_ft"],
        ambient_temperature_c=mission_summary["ambient_temperature_c"],
        throttle=mission_summary["throttle"],
        health_start=mission_summary["health_start"],
        health_end=mission_summary["health_end"],
        predicted_degradation=mission_summary["predicted_degradation"],
        mission_risk=mission_summary["mission_risk"],
        estimated_rul=mission_summary["estimated_rul"],
        recommendations=mission_summary["recommendations"],
    )


@router.get("/mission/{mission_id}", summary="Get mission metadata and results")
async def get_mission(mission_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Retrieve mission details and mission-result assessment."""
    mission = (
        db.query(MissionModel)
        .filter((MissionModel.id == mission_id) | (MissionModel.mission_id == mission_id))
        .first()
    )
    if not mission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Mission '{mission_id}' not found.")
    result = db.query(MissionResultModel).filter(MissionResultModel.mission_id == mission.id).first()
    return {
        "mission_id": mission.id,
        "engine_id": mission.engine_id,
        "status": mission.status,
        "duration_hours": mission.duration,
        "mission_type": mission.mission_type,
        "altitude_ft": mission.altitude,
        "ambient_temperature_c": mission.ambient_temperature,
        "throttle": mission.throttle,
        "result": {
            "health_start": result.health_start if result else None,
            "health_end": result.health_end if result else None,
            "predicted_degradation": result.predicted_degradation if result else None,
            "mission_risk": result.mission_risk if result else None,
            "estimated_rul": result.estimated_rul if result else None,
            "recommendations": result.recommendations if result else None,
            "telemetry_snapshot_count": len(json.loads(result.telemetry_snapshot)) if result and result.telemetry_snapshot else 0,
        } if result else None,
    }


@router.get("/replay/{mission_id}", response_model=ReplayResponse, summary="Replay mission telemetry")
async def replay_mission(mission_id: str, db: Session = Depends(get_db)) -> ReplayResponse:
    """Return a replay-ready summary for the mission timeline."""
    mission = (
        db.query(MissionModel)
        .filter((MissionModel.id == mission_id) | (MissionModel.mission_id == mission_id))
        .first()
    )
    if not mission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Mission '{mission_id}' not found.")

    mission_result = db.query(MissionResultModel).filter(MissionResultModel.mission_id == mission.id).first()

    telemetry_records = (
        db.query(TelemetryModel)
        .filter(TelemetryModel.engine_id == mission.engine_id)
        .order_by(desc(TelemetryModel.timestamp), desc(TelemetryModel.id))
        .limit(50)
        .all()
    )
    health_records = (
        db.query(HealthRecordModel)
        .filter(HealthRecordModel.engine_id == mission.engine_id)
        .order_by(desc(HealthRecordModel.timestamp), desc(HealthRecordModel.id))
        .limit(50)
        .all()
    )
    fault_records = (
        db.query(FaultRecordModel)
        .filter(FaultRecordModel.engine_id == mission.engine_id)
        .order_by(desc(FaultRecordModel.timestamp), desc(FaultRecordModel.id))
        .limit(50)
        .all()
    )
    predictions = (
        db.query(PredictionRecordModel)
        .filter(PredictionRecordModel.engine_id == mission.engine_id)
        .order_by(desc(PredictionRecordModel.timestamp), desc(PredictionRecordModel.id))
        .limit(50)
        .all()
    )

    replay_telemetry = []
    if mission_result and mission_result.telemetry_snapshot:
        try:
            replay_telemetry = json.loads(mission_result.telemetry_snapshot)
        except json.JSONDecodeError:
            replay_telemetry = []
    if not replay_telemetry:
        replay_telemetry = [
            {
                "timestamp": item.timestamp.isoformat(),
                "rpm": item.rpm,
                "egt_c": item.egt_c,
                "cht_c": item.cht_c,
                "oil_pressure_bar": item.oil_pressure_bar,
                "oil_temperature_c": item.oil_temperature_c,
                "fuel_flow_lph": item.fuel_flow_lph,
                "vibration_g": item.vibration_g,
                "altitude_ft": item.altitude_ft,
                "throttle": item.throttle,
            }
            for item in telemetry_records
        ]

    replay_health = []
    if mission_result and mission_result.health_trend_snapshot:
        try:
            replay_health = json.loads(mission_result.health_trend_snapshot)
        except json.JSONDecodeError:
            replay_health = []
    if not replay_health:
        replay_health = [
            {"timestamp": item.timestamp.isoformat(), "health_index": item.health_index, "status": item.health_status or item.status}
            for item in health_records
        ]

    replay_faults = []
    if mission_result and mission_result.fault_events_snapshot:
        try:
            replay_faults = json.loads(mission_result.fault_events_snapshot)
        except json.JSONDecodeError:
            replay_faults = []
    if not replay_faults:
        replay_faults = [
            {"timestamp": item.timestamp.isoformat(), "fault_type": item.fault_type, "severity": item.severity, "status": item.status}
            for item in fault_records
        ]

    replay_rul = []
    if mission_result and mission_result.rul_trend_snapshot:
        try:
            replay_rul = json.loads(mission_result.rul_trend_snapshot)
        except json.JSONDecodeError:
            replay_rul = []
    if not replay_rul:
        replay_rul = [
            {"timestamp": item.timestamp.isoformat(), "rul_hours": item.rul_hours, "rul_lower": item.rul_lower, "rul_upper": item.rul_upper}
            for item in predictions
        ]

    return ReplayResponse(
        mission_id=mission.id,
        engine_id=mission.engine_id,
        mission_type=mission.mission_type,
        telemetry=replay_telemetry,
        health_trend=replay_health,
        fault_events=replay_faults,
        rul_trend=replay_rul,
    )
