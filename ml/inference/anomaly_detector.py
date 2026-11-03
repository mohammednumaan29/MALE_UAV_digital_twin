from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np

from ml.training.common import MODEL_DIR, load_artifact


def detect_anomaly(features: dict | list[float]) -> tuple[bool, float]:
    artifact = load_artifact(MODEL_DIR / "anomaly_model.pkl")
    model = artifact["model"]
    feature_columns = artifact.get("feature_columns", [])
    if isinstance(features, dict):
        row = [float(features.get(name, 0.0)) for name in feature_columns]
    else:
        row = [float(v) for v in features]
    prediction = model.predict(np.asarray([row], dtype=float))[0]
    score = float(model.score_samples(np.asarray([row], dtype=float))[0])
    return bool(prediction == -1), score
