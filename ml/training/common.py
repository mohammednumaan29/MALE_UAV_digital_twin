from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import List, Sequence

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.config.constants import FaultCategory, canonical_fault_name
from app.physics.engine_model import physics_engine
from app.simulation.fault_effects import apply_fault_effects

FAULT_ORDER = [
    FaultCategory.NORMAL,
    FaultCategory.FUEL_MIXTURE,
    FaultCategory.OVERHEATING,
    FaultCategory.LUBRICATION,
    FaultCategory.VIBRATION,
    FaultCategory.SENSOR_ANOMALY,
]

SEVERITY_LEVELS = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
MODEL_DIR = ROOT / "ml" / "models"


def sanitize_feature_columns(columns: Sequence[str]) -> List[str]:
    return [str(c) for c in columns]


def _feature_names() -> List[str]:
    return [
        "rpm",
        "egt_c",
        "cht_c",
        "oil_pressure_bar",
        "oil_temperature_c",
        "fuel_flow_lph",
        "vibration_g",
        "altitude_ft",
        "ambient_temperature_c",
        "throttle",
        "engine_load",
        "power_kw",
        "expected_rpm",
        "expected_egt_c",
        "expected_cht_c",
        "expected_oil_pressure_bar",
        "expected_oil_temperature_c",
        "expected_fuel_flow_lph",
        "expected_vibration_g",
        "expected_power_kw",
        "egt_residual",
        "cht_residual",
        "oil_pressure_residual",
        "oil_temperature_residual",
        "fuel_flow_residual",
        "vibration_residual",
        "rpm_residual",
        "rpm_delta",
        "egt_delta",
        "cht_delta",
        "oil_temperature_delta",
        "vibration_delta",
        "rpm_roll_mean",
        "egt_roll_mean",
        "cht_roll_mean",
        "oil_temperature_roll_mean",
        "vibration_roll_std",
    ]


def _build_expected_state(throttle: float, altitude_ft: float, ambient_temperature_c: float) -> dict:
    return physics_engine.predict_state(
        throttle=float(throttle),
        altitude_ft=float(altitude_ft),
        ambient_temperature_c=float(ambient_temperature_c),
    )


def _add_realistic_noise(actual: dict, rng: np.random.Generator) -> dict:
    noise = {
        "rpm": rng.normal(0.0, 18.0),
        "egt_c": rng.normal(0.0, 4.0),
        "cht_c": rng.normal(0.0, 2.5),
        "oil_pressure_bar": rng.normal(0.0, 0.18),
        "oil_temperature_c": rng.normal(0.0, 2.3),
        "fuel_flow_lph": rng.normal(0.0, 0.45),
        "vibration_g": rng.normal(0.0, 0.04),
        "power_kw": rng.normal(0.0, 1.2),
    }
    for key, offset in noise.items():
        if key in actual:
            actual[key] = float(actual[key]) + float(offset)
    return actual


def generate_training_dataset(samples_per_fault: int = 180) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    records: list[dict] = []

    for run_id in range(samples_per_fault):
        for fault in FAULT_ORDER:
            for severity in SEVERITY_LEVELS:
                throttle = float(rng.uniform(25.0, 82.0))
                altitude_ft = float(rng.uniform(0.0, 12000.0))
                ambient_temperature_c = float(rng.uniform(0.0, 38.0))
                expected = _build_expected_state(throttle, altitude_ft, ambient_temperature_c)
                base_state = {
                    "rpm": expected["expected_rpm"],
                    "egt_c": expected["expected_egt_c"],
                    "cht_c": expected["expected_cht_c"],
                    "oil_pressure_bar": expected["expected_oil_pressure_bar"],
                    "oil_temperature_c": expected["expected_oil_temperature_c"],
                    "fuel_flow_lph": expected["expected_fuel_flow_lph"],
                    "vibration_g": expected["expected_vibration_g"],
                    "power_kw": expected["expected_power_kw"],
                    "engine_load": expected["engine_load"],
                }
                if fault == FaultCategory.NORMAL:
                    actual = dict(base_state)
                    fault_severity = 0.0
                    label = FaultCategory.NORMAL.value
                else:
                    actual = apply_fault_effects(base_state, fault.value, severity)
                    fault_severity = float(severity)
                    label = canonical_fault_name(fault)
                actual = _add_realistic_noise(actual, rng)
                actual["engine_load"] = max(0.15, min(1.0, float(actual.get("engine_load", expected["engine_load"])) + rng.normal(0.0, 0.04)))
                actual["power_kw"] = max(5.0, float(actual.get("power_kw", expected["expected_power_kw"])))
                actual["rpm"] = max(1000.0, min(6200.0, float(actual.get("rpm", expected["expected_rpm"]))))
                actual["egt_c"] = max(400.0, float(actual.get("egt_c", expected["expected_egt_c"])))
                actual["cht_c"] = max(50.0, float(actual.get("cht_c", expected["expected_cht_c"])))
                actual["oil_pressure_bar"] = max(0.5, float(actual.get("oil_pressure_bar", expected["expected_oil_pressure_bar"])))
                actual["oil_temperature_c"] = max(40.0, float(actual.get("oil_temperature_c", expected["expected_oil_temperature_c"])))
                actual["fuel_flow_lph"] = max(2.0, float(actual.get("fuel_flow_lph", expected["expected_fuel_flow_lph"])))
                actual["vibration_g"] = max(0.05, float(actual.get("vibration_g", expected["expected_vibration_g"])))

                row = {
                    "run_id": f"run-{run_id}-{fault.value}",
                    "sample_id": f"{run_id}-{fault.value}-{severity}",
                    "fault_type": label,
                    "fault_severity": fault_severity,
                    "rpm": actual["rpm"],
                    "egt_c": actual["egt_c"],
                    "cht_c": actual["cht_c"],
                    "oil_pressure_bar": actual["oil_pressure_bar"],
                    "oil_temperature_c": actual["oil_temperature_c"],
                    "fuel_flow_lph": actual["fuel_flow_lph"],
                    "vibration_g": actual["vibration_g"],
                    "altitude_ft": altitude_ft,
                    "ambient_temperature_c": ambient_temperature_c,
                    "throttle": throttle,
                    "engine_load": actual["engine_load"],
                    "power_kw": actual["power_kw"],
                    "expected_rpm": expected["expected_rpm"],
                    "expected_egt_c": expected["expected_egt_c"],
                    "expected_cht_c": expected["expected_cht_c"],
                    "expected_oil_pressure_bar": expected["expected_oil_pressure_bar"],
                    "expected_oil_temperature_c": expected["expected_oil_temperature_c"],
                    "expected_fuel_flow_lph": expected["expected_fuel_flow_lph"],
                    "expected_vibration_g": expected["expected_vibration_g"],
                    "expected_power_kw": expected["expected_power_kw"],
                }
                row["egt_residual"] = row["egt_c"] - row["expected_egt_c"]
                row["cht_residual"] = row["cht_c"] - row["expected_cht_c"]
                row["oil_pressure_residual"] = row["oil_pressure_bar"] - row["expected_oil_pressure_bar"]
                row["oil_temperature_residual"] = row["oil_temperature_c"] - row["expected_oil_temperature_c"]
                row["fuel_flow_residual"] = row["fuel_flow_lph"] - row["expected_fuel_flow_lph"]
                row["vibration_residual"] = row["vibration_g"] - row["expected_vibration_g"]
                row["rpm_residual"] = row["rpm"] - row["expected_rpm"]
                row["rpm_delta"] = 0.0
                row["egt_delta"] = 0.0
                row["cht_delta"] = 0.0
                row["oil_temperature_delta"] = 0.0
                row["vibration_delta"] = 0.0
                row["rpm_roll_mean"] = row["rpm"]
                row["egt_roll_mean"] = row["egt_c"]
                row["cht_roll_mean"] = row["cht_c"]
                row["oil_temperature_roll_mean"] = row["oil_temperature_c"]
                row["vibration_roll_std"] = 0.0
                records.append(row)

    df = pd.DataFrame(records)
    grouped = df.groupby("run_id", sort=False)
    for feature in ["rpm", "egt_c", "cht_c", "oil_temperature_c", "vibration_g"]:
        df[f"{feature}_roll_mean"] = grouped[feature].transform(lambda s: s.rolling(window=3, min_periods=1).mean())
        df[f"{feature}_roll_std"] = grouped[feature].transform(lambda s: s.rolling(window=3, min_periods=1).std().fillna(0.0))
        df[f"{feature}_delta"] = grouped[feature].diff().fillna(0.0)

    fixed_columns = _feature_names()
    for c in fixed_columns:
        if c not in df.columns:
            df[c] = 0.0
    df = df[fixed_columns + ["fault_type", "fault_severity", "run_id", "sample_id"]]
    return df


def save_artifact(model_path: Path, payload: dict) -> None:
    model_path.parent.mkdir(parents=True, exist_ok=True)
    import joblib

    joblib.dump(payload, model_path)


def load_artifact(model_path: Path) -> dict:
    import joblib

    artifact = joblib.load(model_path)
    if isinstance(artifact, dict):
        return artifact
    return {"model": artifact, "feature_columns": []}


def save_metadata_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)


def build_anomaly_labels(data: pd.DataFrame) -> pd.Series:
    return (data["fault_type"] != FaultCategory.NORMAL.value).astype(int)


def build_fault_target(data: pd.DataFrame) -> pd.Series:
    return data["fault_type"]


def build_rul_target(data: pd.DataFrame) -> pd.Series:
    severity = data["fault_severity"].fillna(0.0)
    health = np.clip(100.0 - severity * 48.0 - (data["vibration_residual"].abs() * 12.0), 0.0, 100.0)
    rul = np.clip((health / 10.0) + (1.0 - severity) * 18.0, 2.0, 80.0)
    return pd.Series(rul, index=data.index)


def feature_columns_for_training() -> List[str]:
    return sanitize_feature_columns(_feature_names())
