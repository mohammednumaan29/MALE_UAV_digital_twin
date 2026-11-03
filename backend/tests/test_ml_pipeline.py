import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ml.training.common import MODEL_DIR, feature_columns_for_training, generate_training_dataset
from ml.training.train_anomaly import main as train_anomaly
from ml.training.train_fault import main as train_fault
from ml.training.train_rul import main as train_rul


def test_synthetic_ml_dataset_has_required_features_and_fault_labels():
    df = generate_training_dataset(samples_per_fault=20)
    assert len(df) > 0
    assert "fault_type" in df.columns
    assert "fault_severity" in df.columns
    feature_columns = feature_columns_for_training()
    assert feature_columns
    missing = [column for column in ["rpm", "egt_c", "cht_c", "rpm_residual", "fault_type"] if column not in df.columns]
    assert not missing
    assert set(df["fault_type"].unique()) <= {"NORMAL", "FUEL_MIXTURE_DEGRADATION", "OVERHEATING", "LUBRICATION_DEGRADATION", "ABNORMAL_VIBRATION", "SENSOR_ANOMALY"}


def test_training_scripts_create_model_artifacts():
    train_anomaly()
    train_fault()
    train_rul()

    for artifact_name in ["anomaly_model.pkl", "fault_model.pkl", "rul_model.pkl"]:
        path = MODEL_DIR / artifact_name
        assert path.exists(), f"Expected artifact was not created: {path}"
        assert path.stat().st_size > 0
