"""Mission simulation service for Phase 11."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from app.physics.engine_model import physics_engine
from app.simulation.mission_profile import MissionProfile


class MissionSimulationService:
    """Generate a deterministic mission timeline and risk assessment."""

    MISSION_FACTORS = {
        "SURVEILLANCE": 1.0,
        "RECON": 1.15,
        "TRANSPORT": 1.3,
        "SEARCH_AND_RESCUE": 1.4,
        "TRAINING": 0.9,
    }

    def _mission_risk(self, health_end: float) -> str:
        if health_end < 25.0:
            return "CRITICAL"
        if health_end < 45.0:
            return "HIGH"
        if health_end < 60.0:
            return "MEDIUM"
        return "LOW"

    def _recommendation(self, mission_risk: str, mission_type: str) -> str:
        base = {
            "LOW": "Continue mission as planned with routine thermal and lubrication checks.",
            "MEDIUM": "Monitor cooling and lubrication trend; plan a follow-up inspection before the next deployment.",
            "HIGH": "Reduce high-throttle exposure and inspect the cooling, lubrication, and combustion systems.",
            "CRITICAL": "Ground the aircraft for inspection of the cooling and lubrication systems and review engine health before flight.",
        }
        if mission_type.upper() in {"SEARCH_AND_RESCUE", "TRANSPORT"}:
            return base[mission_risk] + " Consider a conservative mission profile and operational risk briefing."
        return base[mission_risk]

    def simulate(
        self,
        *,
        engine_id: str,
        duration_hours: float,
        altitude_ft: float,
        ambient_temperature_c: float,
        throttle: float,
        mission_type: str,
    ) -> Dict[str, Any]:
        duration_hours = float(duration_hours)
        altitude_ft = float(altitude_ft)
        ambient_temperature_c = float(ambient_temperature_c)
        throttle = float(throttle)
        mission_type = (mission_type or "SURVEILLANCE").upper()

        mission_factor = self.MISSION_FACTORS.get(mission_type, 1.0)
        altitude_factor = min(1.6, altitude_ft / 12000.0)
        temp_factor = max(0.0, ambient_temperature_c - 15.0) / 35.0
        throttle_factor = throttle / 100.0

        degradation_penalty = (
            duration_hours
            * (0.65 + altitude_factor * 1.2 + temp_factor * 1.5 + throttle_factor * 1.3)
            * mission_factor
        )
        health_start = 92.0
        health_end = max(10.0, round(health_start - min(70.0, degradation_penalty), 2))
        predicted_degradation = round(health_start - health_end, 2)
        mission_risk = self._mission_risk(health_end)
        total_rul = max(0.0, health_end / 5.0)
        recommendations = self._recommendation(mission_risk, mission_type)

        points: List[Dict[str, Any]] = []
        profile = MissionProfile()
        steps = max(6, min(20, int(duration_hours * 4)))
        for idx in range(steps):
            progress = idx / max(1, steps - 1)
            time_hours = duration_hours * progress
            elapsed_s = time_hours * 3600.0
            flight_condition = profile.get_flight_condition(elapsed_s)
            effective_throttle = min(100.0, throttle * (0.5 + 0.9 * progress))
            effective_altitude = altitude_ft * (0.3 + 0.7 * progress)
            effective_temp = ambient_temperature_c + max(0.0, (flight_condition["altitude_ft"] / 3000.0) * 1.8)
            base = physics_engine.predict_state(
                throttle=effective_throttle,
                altitude_ft=effective_altitude,
                ambient_temperature_c=effective_temp,
            )
            thermal_degradation = degradation_penalty * progress
            egt = base["expected_egt_c"] + 12.0 + 9.0 * thermal_degradation / max(1.0, duration_hours)
            cht = base["expected_cht_c"] + 9.0 + 11.0 * thermal_degradation / max(1.0, duration_hours)
            oil_temp = base["expected_oil_temperature_c"] + 3.0 + 8.5 * thermal_degradation / max(1.0, duration_hours)
            oil_pressure = max(1.2, base["expected_oil_pressure_bar"] - 0.35 * thermal_degradation / max(1.0, duration_hours))
            vibration = max(0.08, base["expected_vibration_g"] + 0.11 * thermal_degradation / max(1.0, duration_hours))
            health_index = max(0.0, health_start - thermal_degradation)
            points.append(
                {
                    "timestamp": (datetime.now(timezone.utc) + timedelta(hours=time_hours)).isoformat(),
                    "rpm": round(base["expected_rpm"], 1),
                    "egt_c": round(egt, 2),
                    "cht_c": round(cht, 2),
                    "oil_pressure_bar": round(oil_pressure, 2),
                    "oil_temperature_c": round(oil_temp, 2),
                    "fuel_flow_lph": round(base["expected_fuel_flow_lph"], 2),
                    "vibration_g": round(vibration, 3),
                    "altitude_ft": round(effective_altitude, 1),
                    "ambient_temperature_c": round(effective_temp, 2),
                    "throttle": round(effective_throttle, 2),
                    "health_index": round(health_index, 2),
                    "phase": flight_condition.get("phase", "CRUISE"),
                }
            )

        trend = [
            {"timestamp": point["timestamp"], "health_index": point["health_index"], "rul_hours": round(max(0.0, total_rul * (1.0 - idx / max(1, len(points) - 1))), 2)}
            for idx, point in enumerate(points)
        ]

        return {
            "engine_id": engine_id,
            "mission_type": mission_type,
            "duration_hours": round(duration_hours, 2),
            "altitude_ft": round(altitude_ft, 1),
            "ambient_temperature_c": round(ambient_temperature_c, 2),
            "throttle": round(throttle, 2),
            "health_start": round(health_start, 2),
            "health_end": round(health_end, 2),
            "predicted_degradation": round(predicted_degradation, 2),
            "mission_risk": mission_risk,
            "estimated_rul": round(total_rul, 2),
            "recommendations": recommendations,
            "timeline": points,
            "health_trend": trend,
            "rul_trend": [
                {"timestamp": entry["timestamp"], "rul_hours": entry["rul_hours"]}
                for entry in trend
            ],
        }


mission_simulation_service = MissionSimulationService()
