"""Score the test set with all three classifiers.

Produces three columns on scored_test.parquet:
  - p_fraud       — selected classifier (matches models/best_model.pkl)
  - p_fraud_rf    — Random Forest, refit on the full training window
  - p_fraud_lgbm  — LightGBM, refit on the full training window

Downstream (backtest, bootstrap, sensitivity) uses all three to compute
the three static-0.5 baselines required by docs/evaluation_protocol.md §12.
"""
from pathlib import Path
import json
import pandas as pd
import joblib

from src.common import MODELS
from src.models.preprocess import (
    build_preprocessor, get_feature_columns, get_numeric_categorical,
)
from src.models.train_compare import (
    ALGORITHMS, RESULTS_PATH, make_model,
)

TRAIN_PATH = Path("data/processed/train.parquet")
TEST_PATH = Path("data/processed/test.parquet")
MODEL_PATH = MODELS / "best_model.pkl"
PREPROC_PATH = MODELS / "preprocessing.pkl"
FEATURES_PATH = MODELS / "feature_columns.json"
OUT_PATH = Path("data/processed/scored_test.parquet")

SCORE_COLUMNS = {
    "logistic_regression": "p_fraud",
    "random_forest":       "p_fraud_rf",
    "lightgbm":            "p_fraud_lgbm",
}


def _to_array(X):
    if hasattr(X, "toarray"):
        return X.toarray()
    return X


def _infer_selected_algorithm(model) -> str:
    """Identify the algorithm from the saved model's class name."""
    name = type(model).__name__
    if "Logistic" in name:
        return "logistic_regression"
    if "Forest" in name:
        return "random_forest"
    if "LGBM" in name or "Booster" in name:
        return "lightgbm"
    raise RuntimeError(f"Cannot infer algorithm from model class {name!r}")


def main() -> None:
    train = pd.read_parquet(TRAIN_PATH)
    test = pd.read_parquet(TEST_PATH)
    features = json.loads(FEATURES_PATH.read_text(encoding="utf-8"))
    selected_params = json.loads(
        RESULTS_PATH.read_text(encoding="utf-8")
    )["selected_params"]

    saved = joblib.load(MODEL_PATH)
    selected_alg = _infer_selected_algorithm(saved)

    out = test.copy()

    for alg in ALGORITHMS:
        col = SCORE_COLUMNS[alg]
        if alg == selected_alg:
            model = saved
            pre = joblib.load(PREPROC_PATH)
        else:
            pre = build_preprocessor(
                alg, *get_numeric_categorical(train[features])
            )
            X_tr = _to_array(pre.fit_transform(train[features]))
            model = make_model(alg, selected_params[alg])
            model.fit(X_tr, train["fraud_bool"])
        X_te = _to_array(pre.transform(test[features]))
        p = model.predict_proba(X_te)[:, 1]
        assert ((p >= 0) & (p <= 1)).all(), f"{col} out of [0, 1]"
        out[col] = p

    out.to_parquet(OUT_PATH, index=False)
    print(f"[score] Wrote {len(out):,} scored rows to {OUT_PATH}")
    for alg, col in SCORE_COLUMNS.items():
        print(f"[score] {col:<14} mean={out[col].mean():.6f}")


if __name__ == "__main__":
    main()