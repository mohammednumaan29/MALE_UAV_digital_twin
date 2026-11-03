"""
Telemetry REST API Endpoints.
Phase 4: Telemetry Persistence and Query Endpoints.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.schemas.telemetry import (
    TelemetryCreateRequest,
    TelemetryResponse,
    TelemetryHistoryResponse,
)
from app.services.telemetry_service import telemetry_service

router = APIRouter(prefix="/telemetry", tags=["Telemetry"])


@router.post(
    "",
    response_model=TelemetryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest & Persist Telemetry",
    description="Ingest telemetry, evaluate Digital Twin expected values if missing, and persist to database."
)
async def create_telemetry(
    telemetry_in: TelemetryCreateRequest,
    db: Session = Depends(get_db)
) -> TelemetryResponse:
    """Insert and persist a new telemetry sample."""
    try:
        return telemetry_service.insert_telemetry(db, telemetry_in)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to persist telemetry: {str(e)}")


@router.get(
    "/latest",
    response_model=TelemetryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Latest Telemetry",
    description="Retrieve the most recent telemetry sample persisted for the engine."
)
async def get_latest_telemetry(
    engine_id: str = Query("rotax914-uav-01", description="Engine identifier"),
    db: Session = Depends(get_db)
) -> TelemetryResponse:
    """Retrieve the newest persisted telemetry frame."""
    latest = telemetry_service.get_latest_telemetry(db, engine_id)
    if not latest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No telemetry records found for engine '{engine_id}'."
        )
    return latest


@router.get(
    "/history",
    response_model=TelemetryHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Telemetry History",
    description="Query chronological telemetry history with limit and offset pagination."
)
async def get_telemetry_history(
    engine_id: str = Query("rotax914-uav-01", description="Engine identifier"),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of records to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db)
) -> TelemetryHistoryResponse:
    """Retrieve historical telemetry records."""
    return telemetry_service.get_telemetry_history(db, engine_id=engine_id, limit=limit, offset=offset)


@router.get(
    "/{engine_id}",
    response_model=TelemetryHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Engine Telemetry History by ID",
    description="Return all telemetry records associated with an engine ID."
)
async def get_engine_telemetry_by_id(
    engine_id: str,
    limit: int = Query(50, ge=1, le=500, description="Maximum number of records to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db)
) -> TelemetryHistoryResponse:
    """Retrieve the telemetry history for a specific engine_id over the path."""
    history = telemetry_service.get_telemetry_history(db, engine_id=engine_id, limit=limit, offset=offset)
    if history.total_records == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No telemetry records found for engine '{engine_id}'."
        )
    return history
