"""Select the best primary model, retrain on full train split, evaluate once
on the untouched test set, and save the model + preprocessing pipeline.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import joblib
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from src.common import SEED, MODELS, CATEGORICAL_COLS
from src.models.preprocess import (
    build_preprocessor,
    get_feature_columns,
    get_numeric_categorical,
)
from src.models.train_compare import (
    ALGORITHMS,
    PARAM_GRIDS,
    RESULTS_PATH,
    make_model,
)

TRAIN_PATH = Path("data/processed/primary_train.parquet")
TEST_PATH = Path("data/processed/primary_test.parquet")
MODEL_PATH = Path("models/best_model.pkl")
PREPROC_PATH = Path("models/preprocessing.pkl")
FEATURES_PATH = Path("models/feature_columns.json")
DEFAULTS_PATH = Path("models/feature_defaults.json")
FINAL_REPORT = Path("reports/model_comparison.md")


def select_best() -> str:
    """Pick the algorithm with the highest mean CV Macro F1."""
    results = json.loads(RESULTS_PATH.read_text())
    means = {
        alg: float(np.mean([r["macro_f1"] for r in results[alg]]))
        for alg in ALGORITHMS
    }
    print("[evaluate_compare] CV Macro F1 means:")
    for alg, m in means.items():
        print(f"  {alg:<22} {m:.4f}")
    return max(means, key=means.get)


def _to_array(X):
    if hasattr(X, "toarray"):
        return X.toarray()
    return X


def _save_feature_metadata(train: pd.DataFrame, features: list[str]) -> None:
    """Persist the training-time feature order and per-column defaults.

    The Streamlit app reads these to construct a fully-populated feature
    vector for manual input and to validate CSV uploads.
    """
    defaults: dict = {}
    for c in features:
        if c in CATEGORICAL_COLS:
            mode = train[c].mode()
            defaults[c] = str(mode.iloc[0]) if len(mode) else ""
        else:
            med = train[c].median()
            defaults[c] = float(med) if pd.notna(med) else 0.0

    FEATURES_PATH.write_text(
        json.dumps(list(features), indent=2), encoding="utf-8"
    )
    DEFAULTS_PATH.write_text(
        json.dumps(defaults, indent=2), encoding="utf-8"
    )
    print(f"[evaluate_compare] Wrote {FEATURES_PATH}")
    print(f"[evaluate_compare] Wrote {DEFAULTS_PATH}")


def main() -> None:
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)

    train = pd.read_parquet(TRAIN_PATH)
    test = pd.read_parquet(TEST_PATH)
    features = get_feature_columns(train)

    best_alg = select_best()
    best_params = PARAM_GRIDS[best_alg][0]
    print(f"\n[evaluate_compare] Selected: {best_alg}")

    # Fit preprocessing on the FULL training split
    X_train = train[features]
    y_train = train["fraud_bool"]
    pre = build_preprocessor(best_alg, *get_numeric_categorical(X_train))
    X_train_t = _to_array(pre.fit_transform(X_train))

    # Train final model on the full training split
    model = make_model(best_alg, best_params)
    model.fit(X_train_t, y_train)

    # Persist feature metadata now that training has succeeded
    _save_feature_metadata(train, features)

    # Evaluate ONCE on the untouched test set
    X_test = test[features]
    y_test = test["fraud_bool"]
    X_test_t = _to_array(pre.transform(X_test))
    y_pred = model.predict(X_test_t)

    metrics = {
        "algorithm": best_alg,
        "macro_f1": float(f1_score(y_test, y_pred, average="macro", zero_division=0)),
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision_fraud": float(precision_score(y_test, y_pred, pos_label=1, zero_division=0)),
        "recall_fraud": float(recall_score(y_test, y_pred, pos_label=1, zero_division=0)),
        "f1_fraud": float(f1_score(y_test, y_pred, pos_label=1, zero_division=0)),
    }
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(X_test_t)[:, 1]
        metrics["roc_auc"] = float(roc_auc_score(y_test, proba))
    cm = confusion_matrix(y_test, y_pred).tolist()

    print("\n[evaluate_compare] Final test results:")
    for k, v in metrics.items():
        print(f"  {k:<16} {v}")
    print(f"  confusion_matrix {cm}")



    # Save global feature importances for the app's explainability panel
    if hasattr(model, "feature_importances_"):
        importances = list(map(float, model.feature_importances_))
        imp_path = MODELS / "feature_importances.json"
        imp_path.write_text(
            json.dumps({"features": list(features), "importances": importances},
                       indent=2),
            encoding="utf-8",
        )
        print(f"[evaluate_compare] Wrote {imp_path}")


    # Persist the model and preprocessing pipeline
    joblib.dump(model, MODEL_PATH)
    joblib.dump(pre, PREPROC_PATH)
    print(f"\n[evaluate_compare] Saved model -> {MODEL_PATH}")
    print(f"[evaluate_compare] Saved preprocessing -> {PREPROC_PATH}")

    # Append a final-test section to the report
    with open(FINAL_REPORT, "a", encoding="utf-8") as f:
        f.write("\n\n## Final Test Results\n\n")
        f.write(f"Selected algorithm: **{best_alg}**\n\n")
        f.write("| Metric | Value |\n|---|---|\n")
        for k, v in metrics.items():
            f.write(f"| {k} | {v} |\n")
        f.write(f"\nConfusion matrix (rows=true, cols=pred): `{cm}`\n")


if __name__ == "__main__":
    main()