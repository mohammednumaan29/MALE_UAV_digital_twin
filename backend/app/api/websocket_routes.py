"""WebSocket routes for live telemetry streaming."""

from fastapi import APIRouter, WebSocket

from app.services.websocket_service import telemetry_ws_manager

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/telemetry/{engine_id}")
async def telemetry_stream(websocket: WebSocket, engine_id: str):
    """Stream the engine telemetry, expected values, residuals, and health snapshot on an open websocket connection."""
    await telemetry_ws_manager.stream(engine_id, websocket)
