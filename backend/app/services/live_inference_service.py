"""Load-trained ML artifacts once and evaluate live telemetry in real time."""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Tuple

import joblib
import numpy as np
import pandas as pd

from app.config.constants import FAULT_REGION_MAP
from app.physics.engine_model import physics_engine
from app.services.health_service import health_engine

ROOT_DIR = Path(__file__).resolve().parents[3]
MODEL_DIR = ROOT_DIR / "ml" / "models"


class LiveInferenceService:
    """Singleton ML inference service that avoids reloading model artifacts each cycle."""

    def __init__(self) -> None:
        self._models: Dict[str, Dict[str, Any]] = {}
        self._feature_columns: Dict[str, List[str]] = {}
        self._lock = Lock()
        self._loaded = False

    def load_models(self) -> None:
        if self._loaded:
            return

        with self._lock:
            if self._loaded:
                return
            for name in ("anomaly_model.pkl", "fault_model.pkl", "rul_model.pkl"):
                path = MODEL_DIR / name
                if not path.exists():
                    continue
                artifact = joblib.load(path)
                self._models[name.replace("_model.pkl", "")] = artifact
                self._feature_columns[name.replace("_model.pkl", "")] = artifact.get("feature_columns", [])
            self._loaded = True

    def _expected_state_for(self, telemetry: Dict[str, Any]) -> Dict[str, Any]:
        if any(key in telemetry for key in [
            "expected_rpm",
            "expected_egt_c",
            "expected_cht_c",
            "expected_oil_pressure_bar",
            "expected_oil_temperature_c",
            "expected_fuel_flow_lph",
            "expected_vibration_g",
            "expected_power_kw",
        ]):
            return {
                "expected_rpm": float(telemetry.get("expected_rpm", telemetry.get("rpm", 0.0))),
                "expected_egt_c": float(telemetry.get("expected_egt_c", telemetry.get("egt_c", 0.0))),
                "expected_cht_c": float(telemetry.get("expected_cht_c", telemetry.get("cht_c", 0.0))),
                "expected_oil_pressure_bar": float(telemetry.get("expected_oil_pressure_bar", telemetry.get("oil_pressure_bar", 0.0))),
                "expected_oil_temperature_c": float(telemetry.get("expected_oil_temperature_c", telemetry.get("oil_temperature_c", 0.0))),
                "expected_fuel_flow_lph": float(telemetry.get("expected_fuel_flow_lph", telemetry.get("fuel_flow_lph", 0.0))),
                "expected_vibration_g": float(telemetry.get("expected_vibration_g", telemetry.get("vibration_g", 0.0))),
                "expected_power_kw": float(telemetry.get("expected_power_kw", telemetry.get("power_kw", 0.0))),
            }

        predicted = physics_engine.predict_state(
            throttle=float(telemetry.get("throttle", 50.0)),
            altitude_ft=float(telemetry.get("altitude_ft", 0.0)),
            ambient_temperature_c=float(telemetry.get("ambient_temperature_c", 15.0)),
        )
        return {
            "expected_rpm": float(predicted["expected_rpm"]),
            "expected_egt_c": float(predicted["expected_egt_c"]),
            "expected_cht_c": float(predicted["expected_cht_c"]),
            "expected_oil_pressure_bar": float(predicted["expected_oil_pressure_bar"]),
            "expected_oil_temperature_c": float(predicted["expected_oil_temperature_c"]),
            "expected_fuel_flow_lph": float(predicted["expected_fuel_flow_lph"]),
            "expected_vibration_g": float(predicted["expected_vibration_g"]),
            "expected_power_kw": float(predicted["expected_power_kw"]),
        }

    def _build_feature_vector(self, telemetry: Dict[str, Any]) -> Dict[str, float]:
        expected = self._expected_state_for(telemetry)
        residuals = {
            "egt_residual": float(telemetry.get("egt_c", 0.0)) - float(expected["expected_egt_c"]),
            "cht_residual": float(telemetry.get("cht_c", 0.0)) - float(expected["expected_cht_c"]),
            "oil_pressure_residual": float(telemetry.get("oil_pressure_bar", 0.0)) - float(expected["expected_oil_pressure_bar"]),
            "oil_temperature_residual": float(telemetry.get("oil_temperature_c", 0.0)) - float(expected["expected_oil_temperature_c"]),
            "fuel_flow_residual": float(telemetry.get("fuel_flow_lph", 0.0)) - float(expected["expected_fuel_flow_lph"]),
            "vibration_residual": float(telemetry.get("vibration_g", 0.0)) - float(expected["expected_vibration_g"]),
            "rpm_residual": float(telemetry.get("rpm", 0.0)) - float(expected["expected_rpm"]),
        }
        numeric = {
            "rpm": float(telemetry.get("rpm", 0.0)),
            "egt_c": float(telemetry.get("egt_c", 0.0)),
            "cht_c": float(telemetry.get("cht_c", 0.0)),
            "oil_pressure_bar": float(telemetry.get("oil_pressure_bar", 0.0)),
            "oil_temperature_c": float(telemetry.get("oil_temperature_c", 0.0)),
            "fuel_flow_lph": float(telemetry.get("fuel_flow_lph", 0.0)),
            "vibration_g": float(telemetry.get("vibration_g", 0.0)),
            "altitude_ft": float(telemetry.get("altitude_ft", 0.0)),
            "ambient_temperature_c": float(telemetry.get("ambient_temperature_c", 15.0)),
            "throttle": float(telemetry.get("throttle", 50.0)),
            "engine_load": float(telemetry.get("engine_load", 0.5)),
            "power_kw": float(telemetry.get("power_kw", 0.0)),
            "expected_rpm": float(expected["expected_rpm"]),
            "expected_egt_c": float(expected["expected_egt_c"]),
            "expected_cht_c": float(expected["expected_cht_c"]),
            "expected_oil_pressure_bar": float(expected["expected_oil_pressure_bar"]),
            "expected_oil_temperature_c": float(expected["expected_oil_temperature_c"]),
            "expected_fuel_flow_lph": float(expected["expected_fuel_flow_lph"]),
            "expected_vibration_g": float(expected["expected_vibration_g"]),
            "expected_power_kw": float(expected["expected_power_kw"]),
            "rpm_delta": 0.0,
            "egt_delta": 0.0,
            "cht_delta": 0.0,
            "oil_temperature_delta": 0.0,
            "vibration_delta": 0.0,
            "rpm_roll_mean": float(telemetry.get("rpm", 0.0)),
            "egt_roll_mean": float(telemetry.get("egt_c", 0.0)),
            "cht_roll_mean": float(telemetry.get("cht_c", 0.0)),
            "oil_temperature_roll_mean": float(telemetry.get("oil_temperature_c", 0.0)),
            "vibration_roll_std": 0.0,
        }
        numeric.update(residuals)
        return numeric

    def _get_model_payload(self, name: str) -> Dict[str, Any]:
        self.load_models()
        payload = self._models.get(name)
        if payload is None:
            raise FileNotFoundError(f"ML model '{name}' not found in {MODEL_DIR}")
        return payload

    def _normalise_anomaly_score(self, score: float) -> float:
        val = float(score)
        if math.isnan(val):
            return 0.0
        return max(0.0, min(1.0, 1.0 / (1.0 + math.exp(-val))))

    def _build_explainability_summary(
        self,
        telemetry: Dict[str, Any],
        residuals: Dict[str, float],
        probable_fault: str,
        fault_probability_pct: float,
        impacted_regions: List[str],
    ) -> Dict[str, Any]:
        """Package residual evidence with contextual operating-state indicators."""
        evidence = {
            key: round(float(value), 2)
            for key, value in sorted(
                residuals.items(),
                key=lambda item: abs(float(item[1])),
                reverse=True,
            )[:4]
        }
        ambient_temperature = float(telemetry.get("ambient_temperature_c", 15.0))
        altitude_ft = float(telemetry.get("altitude_ft", 0.0))
        if ambient_temperature >= 30.0:
            ambient_condition = "high"
        elif ambient_temperature <= 5.0:
            ambient_condition = "low"
        else:
            ambient_condition = "moderate"
        evidence["ambient_temperature_c"] = round(ambient_temperature, 2)
        evidence["ambient_condition"] = ambient_condition
        evidence["altitude_ft"] = round(altitude_ft, 2)
        evidence["fault_context"] = probable_fault
        evidence["confidence_pct"] = round(float(fault_probability_pct * 100.0), 2)
        evidence["affected_region"] = list(impacted_regions)
        return evidence

    def build_dashboard_payload(self, telemetry: Dict[str, Any]) -> Dict[str, Any]:
        """Build a websocket-ready payload including telemetry, expected values, residuals, and ML health state."""
        expected = self._expected_state_for(telemetry)
        residuals = {
            "rpm_residual": float(telemetry.get("rpm", 0.0)) - float(expected["expected_rpm"]),
            "egt_residual": float(telemetry.get("egt_c", 0.0)) - float(expected["expected_egt_c"]),
            "cht_residual": float(telemetry.get("cht_c", 0.0)) - float(expected["expected_cht_c"]),
            "oil_pressure_residual": float(telemetry.get("oil_pressure_bar", 0.0)) - float(expected["expected_oil_pressure_bar"]),
            "oil_temperature_residual": float(telemetry.get("oil_temperature_c", 0.0)) - float(expected["expected_oil_temperature_c"]),
            "fuel_flow_residual": float(telemetry.get("fuel_flow_lph", 0.0)) - float(expected["expected_fuel_flow_lph"]),
            "vibration_residual": float(telemetry.get("vibration_g", 0.0)) - float(expected["expected_vibration_g"]),
        }
        inference = self.evaluate_telemetry(telemetry)
        impacted_regions = inference.get("affected_region", ["ENGINE_MOUNT_REGION"])
        explainability = self._build_explainability_summary(
            telemetry=telemetry,
            residuals=residuals,
            probable_fault=inference.get("probable_fault", "NORMAL"),
            fault_probability_pct=float(inference.get("fault_probability", 0.0)) / 100.0,
            impacted_regions=impacted_regions,
        )
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "telemetry": {
                "rpm": float(telemetry.get("rpm", 0.0)),
                "egt_c": float(telemetry.get("egt_c", 0.0)),
                "cht_c": float(telemetry.get("cht_c", 0.0)),
                "oil_pressure_bar": float(telemetry.get("oil_pressure_bar", 0.0)),
                "oil_temperature_c": float(telemetry.get("oil_temperature_c", 0.0)),
                "fuel_flow_lph": float(telemetry.get("fuel_flow_lph", 0.0)),
                "vibration_g": float(telemetry.get("vibration_g", 0.0)),
                "altitude_ft": float(telemetry.get("altitude_ft", 0.0)),
                "ambient_temperature_c": float(telemetry.get("ambient_temperature_c", 15.0)),
                "throttle": float(telemetry.get("throttle", 50.0)),
                "engine_load": float(telemetry.get("engine_load", 0.5)),
                "power_kw": float(telemetry.get("power_kw", 0.0)),
            },
            "expected": expected,
            "residuals": {key: round(float(value), 4) for key, value in residuals.items()},
            "evidence": explainability,
            "health": {
                "health_index": float(inference.get("engine_health", 100.0)),
                "status": inference.get("status", "HEALTHY"),
            },
            "anomaly": bool(inference.get("anomaly", False)),
            "anomaly_score": float(inference.get("anomaly_score", 0.0)),
            "fault": inference.get("probable_fault", "NORMAL"),
            "fault_probability": float(inference.get("fault_probability", 0.0)),
            "confidence": float(inference.get("fault_probability", 0.0)),
            "severity": float(inference.get("severity", 0.0)),
            "rul": {
                "hours": float(inference.get("estimated_rul_hours", 999.0)),
                "lower": float(inference.get("confidence_range", {}).get("lower", 999.0)),
                "upper": float(inference.get("confidence_range", {}).get("upper", 999.0)),
            },
            "affected_region": impacted_regions,
        }

    def evaluate_telemetry(self, telemetry: Dict[str, Any]) -> Dict[str, Any]:
        """Run anomaly detection, fault classification, and RUL estimation on a live telemetry frame."""
        self.load_models()
        if not self._models:
            return {
                "engine_health": 100.0,
                "status": "HEALTHY",
                "anomaly": False,
                "anomaly_score": 0.0,
                "probable_fault": "NORMAL",
                "fault_probability": 0.0,
                "severity": 0.0,
                "estimated_rul_hours": 999.0,
                "confidence_range": {"lower": 999.0, "upper": 999.0},
                "evidence": {},
                "affected_region": ["ENGINE_MOUNT_REGION"],
            }

        features = self._build_feature_vector(telemetry)

        anomaly_payload = self._get_model_payload("anomaly")
        anomaly_model = anomaly_payload["model"]
        anomaly_columns = anomaly_payload.get("feature_columns", [])
        anomaly_row = pd.DataFrame([[features.get(column, 0.0) for column in anomaly_columns]], columns=anomaly_columns, dtype=float)
        anomaly_pred = anomaly_model.predict(anomaly_row)[0]
        if hasattr(anomaly_model, "score_samples"):
            anomaly_raw = float(anomaly_model.score_samples(anomaly_row)[0])
        else:
            anomaly_raw = float(anomaly_pred)
        anomaly_detected = bool(anomaly_pred == -1)
        anomaly_score = self._normalise_anomaly_score(-anomaly_raw)

        fault_payload = self._get_model_payload("fault")
        fault_model = fault_payload["model"]
        fault_columns = fault_payload.get("feature_columns", [])
        fault_row = pd.DataFrame([[features.get(column, 0.0) for column in fault_columns]], columns=fault_columns, dtype=float)
        fault_pred = str(fault_model.predict(fault_row)[0])
        probas = fault_model.predict_proba(fault_row)[0]
        fault_prob = float(np.max(probas))
        fault_probability_pct = max(0.0, min(1.0, fault_prob))

        rul_payload = self._get_model_payload("rul")
        rul_model = rul_payload["model"]
        rul_columns = rul_payload.get("feature_columns", [])
        rul_row = pd.DataFrame([[features.get(column, 0.0) for column in rul_columns]], columns=rul_columns, dtype=float)
        rul_estimate = float(rul_model.predict(rul_row)[0])
        rul_lower = max(0.0, rul_estimate * 0.85)
        rul_upper = rul_estimate * 1.15

        residual_metrics = {
            "egt_residual": abs(features.get("egt_residual", 0.0)),
            "cht_residual": abs(features.get("cht_residual", 0.0)),
            "oil_temperature_residual": abs(features.get("oil_temperature_residual", 0.0)),
            "vibration_residual": abs(features.get("vibration_residual", 0.0)),
            "oil_pressure_residual": abs(features.get("oil_pressure_residual", 0.0)),
        }
        evidence = {k: round(v, 2) for k, v in sorted(residual_metrics.items(), key=lambda item: item[1], reverse=True)[:3]}
        ambient_temperature = float(telemetry.get("ambient_temperature_c", 15.0))
        altitude_ft = float(telemetry.get("altitude_ft", 0.0))
        evidence["ambient_temperature_c"] = round(ambient_temperature, 2)
        evidence["altitude_ft"] = round(altitude_ft, 2)
        if ambient_temperature >= 30.0:
            evidence["ambient_condition"] = "high"
        elif ambient_temperature <= 5.0:
            evidence["ambient_condition"] = "low"
        else:
            evidence["ambient_condition"] = "moderate"

        if fault_pred == "NORMAL":
            severity = 0.0
            fault_probability_pct = 0.0
            probable_fault = "NORMAL"
        else:
            severity = min(1.0, max(0.0, fault_probability_pct * 0.75 + anomaly_score * 0.25))
            probable_fault = fault_pred
        evidence["fault_context"] = probable_fault

        health_state = health_engine.compute(
            anomaly_score=anomaly_score,
            fault_probability=fault_probability_pct * 100.0,
            severity=severity,
            residuals={
                "egt_residual": features.get("egt_residual", 0.0),
                "cht_residual": features.get("cht_residual", 0.0),
                "oil_temperature_residual": features.get("oil_temperature_residual", 0.0),
                "oil_pressure_residual": features.get("oil_pressure_residual", 0.0),
                "vibration_residual": features.get("vibration_residual", 0.0),
            },
            vibration_g=float(telemetry.get("vibration_g", 0.0)),
            oil_pressure_bar=float(telemetry.get("oil_pressure_bar", 0.0)),
            oil_temperature_c=float(telemetry.get("oil_temperature_c", 0.0)),
            egt_c=float(telemetry.get("egt_c", 0.0)),
            cht_c=float(telemetry.get("cht_c", 0.0)),
            expected_egt_c=float(self._expected_state_for(telemetry)["expected_egt_c"]),
            expected_cht_c=float(self._expected_state_for(telemetry)["expected_cht_c"]),
            expected_oil_temperature_c=float(self._expected_state_for(telemetry)["expected_oil_temperature_c"]),
        )

        health_score = health_state["health_index"]
        status = health_state["status"]

        impacted_regions = FAULT_REGION_MAP.get(probable_fault, ["ENGINE_MOUNT_REGION"])

        return {
            "engine_health": round(health_score, 2),
            "status": status,
            "anomaly": anomaly_detected,
            "anomaly_score": round(anomaly_score, 4),
            "probable_fault": probable_fault,
            "fault_probability": round(fault_probability_pct * 100.0, 1),
            "severity": round(float(severity), 4),
            "estimated_rul_hours": round(float(rul_estimate), 2),
            "confidence_range": {
                "lower": round(float(rul_lower), 2),
                "upper": round(float(rul_upper), 2),
            },
            "evidence": evidence,
            "affected_region": impacted_regions,
        }


live_inference_service = LiveInferenceService()
