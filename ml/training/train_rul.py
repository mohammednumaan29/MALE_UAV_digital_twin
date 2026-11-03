from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupShuffleSplit

from ml.training.common import MODEL_DIR, build_rul_target, feature_columns_for_training, generate_training_dataset, save_artifact


def main() -> None:
    df = generate_training_dataset(samples_per_fault=180)
    feature_columns = feature_columns_for_training()
    X = df[feature_columns].copy()
    y = build_rul_target(df)
    splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    train_idx, test_idx = next(splitter.split(X, y, groups=df["run_id"]))
    X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
    y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

    model = RandomForestRegressor(
        n_estimators=250,
        random_state=42,
    )
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)

    metrics = {
        "dataset_size": int(len(df)),
        "features_used": feature_columns,
        "training_size": int(len(X_train)),
        "test_size": int(len(X_test)),
        "mae": round(float(mean_absolute_error(y_test, predictions)), 4),
        "rmse": round(float(np.sqrt(mean_squared_error(y_test, predictions))), 4),
        "r2": round(float(r2_score(y_test, predictions)), 4),
    }
    save_path = MODEL_DIR / "rul_model.pkl"
    save_artifact(save_path, {"model": model, "feature_columns": feature_columns, "metrics": metrics})
    print(f"Dataset size: {metrics['dataset_size']}")
    print(f"Features used: {len(feature_columns)}")
    print(f"Training size: {metrics['training_size']}")
    print(f"Test size: {metrics['test_size']}")
    print(f"MAE: {metrics['mae']}")
    print(f"RMSE: {metrics['rmse']}")
    print(f"R2: {metrics['r2']}")
    print(f"Model saved to: {save_path}")


if __name__ == "__main__":
    main()
