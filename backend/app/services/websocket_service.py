"""WebSocket connection manager and telemetry broadcaster."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, DefaultDict, Set

from fastapi import WebSocket, WebSocketDisconnect

from app.models.database import SessionLocal
from app.models.telemetry import TelemetryModel
from app.services.live_inference_service import live_inference_service


class TelemetryWebSocketManager:
    """Manage per-engine websocket subscriptions and broadcast snapshots."""

    def __init__(self) -> None:
        self.connections: DefaultDict[str, Set[WebSocket]] = defaultdict(set)

    def _read_latest_telemetry(self, engine_id: str) -> dict[str, Any]:
        db = SessionLocal()
        try:
            record = (
                db.query(TelemetryModel)
                .filter(TelemetryModel.engine_id == engine_id)
                .order_by(TelemetryModel.timestamp.desc(), TelemetryModel.id.desc())
                .first()
            )
            if record is None:
                return {
                    "rpm": 5200.0,
                    "egt_c": 740.0,
                    "cht_c": 118.0,
                    "oil_pressure_bar": 4.0,
                    "oil_temperature_c": 92.0,
                    "fuel_flow_lph": 18.5,
                    "vibration_g": 0.22,
                    "altitude_ft": 12000.0,
                    "ambient_temperature_c": 30.0,
                    "throttle": 65.0,
                    "engine_load": 0.72,
                    "power_kw": 53.0,
                }
            return {
                "rpm": float(record.rpm),
                "egt_c": float(record.egt_c),
                "cht_c": float(record.cht_c),
                "oil_pressure_bar": float(record.oil_pressure_bar),
                "oil_temperature_c": float(record.oil_temperature_c),
                "fuel_flow_lph": float(record.fuel_flow_lph),
                "vibration_g": float(record.vibration_g),
                "altitude_ft": float(record.altitude_ft),
                "ambient_temperature_c": float(record.ambient_temperature_c),
                "throttle": float(record.throttle),
                "engine_load": float(record.engine_load),
                "power_kw": float(record.power_kw),
            }
        finally:
            db.close()

    async def connect(self, engine_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self.connections[engine_id].add(websocket)

    def disconnect(self, engine_id: str, websocket: WebSocket) -> None:
        self.connections[engine_id].discard(websocket)
        if not self.connections[engine_id]:
            self.connections.pop(engine_id, None)

    async def send_snapshot(self, engine_id: str) -> None:
        snapshot = self._build_snapshot(engine_id)
        stale: set[WebSocket] = set()
        for socket in list(self.connections.get(engine_id, set())):
            try:
                await socket.send_json(snapshot)
            except (RuntimeError, WebSocketDisconnect):
                stale.add(socket)
        for socket in stale:
            self.disconnect(engine_id, socket)

    def _build_snapshot(self, engine_id: str) -> dict[str, Any]:
        telemetry = self._read_latest_telemetry(engine_id)
        telemetry["engine_id"] = engine_id
        payload = live_inference_service.build_dashboard_payload(telemetry)
        payload["engine_id"] = engine_id
        return payload

    async def stream(self, engine_id: str, websocket: WebSocket) -> None:
        await self.connect(engine_id, websocket)
        try:
            while True:
                await self.send_snapshot(engine_id)
                await asyncio.sleep(1.0)
        except WebSocketDisconnect:
            self.disconnect(engine_id, websocket)
        except RuntimeError:
            self.disconnect(engine_id, websocket)
        except asyncio.CancelledError:
            self.disconnect(engine_id, websocket)
            raise


telemetry_ws_manager = TelemetryWebSocketManager()
