"""Health scoring engine for digital twin engine assessment."""

from __future__ import annotations

from typing import Any, Dict, Mapping, Optional

from app.config.settings import settings


class HealthEngine:
    """Compute a configurable health index from residuals and model outputs."""

    DEFAULT_THRESHOLDS = {
        "HEALTHY": 90.0,
        "NORMAL": 70.0,
        "DEGRADED": 40.0,
        "CRITICAL": 0.0,
    }

    DEFAULT_WEIGHTS = {
        "anomaly_score": 25.0,
        "fault_probability": 30.0,
        "severity": 20.0,
        "thermal_residual": 12.0,
        "vibration": 8.0,
        "lubrication": 5.0,
    }

    def __init__(
        self,
        thresholds: Optional[Mapping[str, float]] = None,
        weights: Optional[Mapping[str, float]] = None,
    ) -> None:
        self.thresholds = {
            "HEALTHY": float(getattr(settings, "HEALTHY_THRESHOLD", self.DEFAULT_THRESHOLDS["HEALTHY"])),
            "NORMAL": float(getattr(settings, "NORMAL_THRESHOLD", self.DEFAULT_THRESHOLDS["NORMAL"])),
            "DEGRADED": float(getattr(settings, "DEGRADED_THRESHOLD", self.DEFAULT_THRESHOLDS["DEGRADED"])),
            "CRITICAL": float(self.DEFAULT_THRESHOLDS["CRITICAL"]),
        }
        if thresholds:
            self.thresholds.update(thresholds)
        self.weights = dict(getattr(settings, "HEALTH_SCORE_WEIGHTS", self.DEFAULT_WEIGHTS))
        if weights:
            self.weights.update(weights)

    def status_for(self, health_index: float) -> str:
        """Convert a health index into one of the mission-safe health states."""
        if health_index >= self.thresholds["HEALTHY"]:
            return "HEALTHY"
        if health_index >= self.thresholds["NORMAL"]:
            return "NORMAL"
        if health_index >= self.thresholds["DEGRADED"]:
            return "DEGRADED"
        return "CRITICAL"

    def compute(
        self,
        *,
        anomaly_score: float = 0.0,
        fault_probability: float = 0.0,
        severity: float = 0.0,
        residuals: Optional[Mapping[str, float]] = None,
        vibration_g: float = 0.0,
        oil_pressure_bar: float = 0.0,
        oil_temperature_c: float = 0.0,
        egt_c: float = 0.0,
        cht_c: float = 0.0,
        expected_egt_c: float = 0.0,
        expected_cht_c: float = 0.0,
        expected_oil_temperature_c: float = 0.0,
    ) -> Dict[str, Any]:
        """Calculate a health score from system-level degradation indicators."""
        residuals = dict(residuals or {})

        egt_residual = float(residuals.get("egt_residual", egt_c - expected_egt_c))
        cht_residual = float(residuals.get("cht_residual", cht_c - expected_cht_c))
        oil_temp_residual = float(
            residuals.get("oil_temperature_residual", oil_temperature_c - expected_oil_temperature_c)
        )
        pressure_residual = float(residuals.get("oil_pressure_residual", 0.0))
        vibration_residual = float(residuals.get("vibration_residual", 0.0))

        thermal_penalty = min(
            100.0,
            (abs(egt_residual) / 80.0) * 35.0
            + (abs(cht_residual) / 50.0) * 40.0
            + (abs(oil_temp_residual) / 35.0) * 25.0,
        )
        vibration_penalty = min(100.0, max(0.0, (vibration_g / 0.8) * 100.0))
        lubrication_penalty = min(
            100.0,
            max(0.0, (3.5 - max(0.0, oil_pressure_bar)) / 3.5) * 100.0 + max(0.0, abs(pressure_residual) / 1.5) * 35.0,
        )

        health_score = 100.0
        health_score -= min(100.0, float(anomaly_score) * self.weights["anomaly_score"])
        health_score -= min(100.0, float(fault_probability) * self.weights["fault_probability"] / 100.0)
        health_score -= min(100.0, float(severity) * self.weights["severity"])
        health_score -= min(100.0, thermal_penalty * (self.weights["thermal_residual"] / 100.0))
        health_score -= min(100.0, vibration_penalty * (self.weights["vibration"] / 100.0))
        health_score -= min(100.0, lubrication_penalty * (self.weights["lubrication"] / 100.0))
        health_score = max(0.0, min(100.0, health_score))

        return {
            "health_index": round(float(health_score), 2),
            "status": self.status_for(health_score),
            "breakdown": {
                "anomaly_score": round(float(anomaly_score), 4),
                "fault_probability": round(float(fault_probability), 2),
                "severity": round(float(severity), 4),
                "thermal_penalty": round(float(thermal_penalty), 2),
                "vibration_penalty": round(float(vibration_penalty), 2),
                "lubrication_penalty": round(float(lubrication_penalty), 2),
            },
        }


health_engine = HealthEngine()
