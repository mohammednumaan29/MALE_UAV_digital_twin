from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.model_selection import GroupShuffleSplit

from ml.training.common import MODEL_DIR, build_fault_target, feature_columns_for_training, generate_training_dataset, save_artifact


def main() -> None:
    df = generate_training_dataset(samples_per_fault=180)
    feature_columns = feature_columns_for_training()
    X = df[feature_columns].copy()
    y = build_fault_target(df)
    splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    train_idx, test_idx = next(splitter.split(X, y, groups=df["run_id"]))
    X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
    y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

    model = RandomForestClassifier(
        n_estimators=250,
        class_weight="balanced_subsample",
        random_state=42,
        max_depth=None,
    )
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)

    metrics = {
        "dataset_size": int(len(df)),
        "features_used": feature_columns,
        "training_size": int(len(X_train)),
        "test_size": int(len(X_test)),
        "accuracy": round(float(accuracy_score(y_test, predictions)), 4),
        "precision": round(float(precision_score(y_test, predictions, average="weighted", zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, predictions, average="weighted", zero_division=0)), 4),
        "f1": round(float(f1_score(y_test, predictions, average="weighted", zero_division=0)), 4),
        "confusion_matrix": confusion_matrix(y_test, predictions, labels=model.classes_).tolist(),
    }
    save_path = MODEL_DIR / "fault_model.pkl"
    save_artifact(save_path, {"model": model, "feature_columns": feature_columns, "classes": model.classes_.tolist(), "metrics": metrics})
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
