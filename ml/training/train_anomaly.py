from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sklearn.ensemble import IsolationForest
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.model_selection import GroupShuffleSplit

from ml.training.common import MODEL_DIR, build_anomaly_labels, feature_columns_for_training, generate_training_dataset, save_artifact


def main() -> None:
    df = generate_training_dataset(samples_per_fault=180)
    feature_columns = feature_columns_for_training()
    healthy_df = df[df["fault_type"] == "NORMAL"].copy()
    fault_df = df[df["fault_type"] != "NORMAL"].copy()
    splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    train_idx, _ = next(splitter.split(healthy_df[feature_columns], healthy_df["fault_type"], groups=healthy_df["run_id"]))
    X_train = healthy_df[feature_columns].iloc[train_idx]
    X_test = pd.concat([healthy_df[feature_columns].drop(healthy_df[feature_columns].index[train_idx]), fault_df[feature_columns]], axis=0)
    y_test = pd.concat([
        pd.Series(0, index=healthy_df[feature_columns].drop(healthy_df[feature_columns].index[train_idx]).index),
        pd.Series(1, index=fault_df[feature_columns].index),
    ]).sort_index()

    model = IsolationForest(
        contamination=0.08,
        n_estimators=300,
        random_state=42,
    )
    model.fit(X_train)
    predictions = (model.predict(X_test) == -1).astype(int)

    metrics = {
        "dataset_size": int(len(df)),
        "features_used": feature_columns,
        "training_size": int(len(X_train)),
        "test_size": int(len(X_test)),
        "accuracy": round(float(accuracy_score(y_test, predictions)), 4),
        "precision": round(float(precision_score(y_test, predictions, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, predictions, zero_division=0)), 4),
        "f1": round(float(f1_score(y_test, predictions, zero_division=0)), 4),
        "confusion_matrix": confusion_matrix(y_test, predictions).tolist(),
    }
    save_path = MODEL_DIR / "anomaly_model.pkl"
    save_artifact(save_path, {"model": model, "feature_columns": feature_columns, "metrics": metrics})
    print(f"Dataset size: {metrics['dataset_size']}")
    print(f"Features used: {len(feature_columns)}")
    print(f"Training size: {metrics['training_size']}")
    print(f"Test size: {metrics['test_size']}")
    print(f"Accuracy: {metrics['accuracy']}")
    print(f"Precision: {metrics['precision']}")
    print(f"Recall: {metrics['recall']}")
    print(f"F1: {metrics['f1']}")
    print(f"Confusion matrix: {metrics['confusion_matrix']}")
    print(f"Model saved to: {save_path}")


if __name__ == "__main__":
    main()
