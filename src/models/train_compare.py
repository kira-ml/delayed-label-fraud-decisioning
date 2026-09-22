"""Primary 3-algorithm training with 5-fold time-series CV.

Trains Logistic Regression, Random Forest, and LightGBM under identical
folds and preprocessing. Writes reports/model_comparison.md and
reports/cv_results.json.
"""
from __future__ import annotations
import json
import warnings
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, f1_score, precision_score, recall_score, roc_auc_score,
)
from sklearn.model_selection import TimeSeriesSplit
import lightgbm as lgb

from src.common import SEED
from src.models.preprocess import (
    build_preprocessor, get_feature_columns, get_numeric_categorical,
)

warnings.filterwarnings("ignore")

TRAIN_PATH = Path("data/processed/primary_train.parquet")
REPORT_PATH = Path("reports/model_comparison.md")
RESULTS_PATH = Path("reports/cv_results.json")

ALGORITHMS = ["logistic_regression", "random_forest", "lightgbm"]
N_SPLITS = 5

# Small, documented grids (see docs/evaluation_protocol.md §4.4)
PARAM_GRIDS = {
    "logistic_regression": [
        {"C": 1.0, "class_weight": "balanced", "max_iter": 1000},
    ],
    "random_forest": [
        {"n_estimators": 200, "class_weight": "balanced_subsample",
         "n_jobs": -1, "random_state": SEED},
    ],
    "lightgbm": [
        {"n_estimators": 300, "verbose": -1, "random_state": SEED},
    ],
}


def make_model(algorithm: str, params: dict):
    if algorithm == "logistic_regression":
        return LogisticRegression(**params)
    if algorithm == "random_forest":
        return RandomForestClassifier(**params)
    if algorithm == "lightgbm":
        return lgb.LGBMClassifier(**params)
    raise ValueError(algorithm)


def _to_array(X):
    """Convert a transformed matrix to a numpy array when needed."""
    if hasattr(X, "toarray"):
        return X.toarray()
    return X


def evaluate_fold(model, X_tr, y_tr, X_va, y_va, algorithm: str) -> dict:
    pre = build_preprocessor(algorithm, *get_numeric_categorical(X_tr))
    X_tr_t = pre.fit_transform(X_tr)
    X_va_t = pre.transform(X_va)
    X_tr_t = _to_array(X_tr_t)
    X_va_t = _to_array(X_va_t)

    model.fit(X_tr_t, y_tr)
    y_pred = model.predict(X_va_t)

    out = {
        "macro_f1": f1_score(y_va, y_pred, average="macro", zero_division=0),
        "accuracy": accuracy_score(y_va, y_pred),
        "precision_fraud": precision_score(y_va, y_pred, pos_label=1, zero_division=0),
        "recall_fraud": recall_score(y_va, y_pred, pos_label=1, zero_division=0),
        "f1_fraud": f1_score(y_va, y_pred, pos_label=1, zero_division=0),
    }
    if hasattr(model, "predict_proba"):
        try:
            proba = model.predict_proba(X_va_t)[:, 1]
            out["roc_auc"] = roc_auc_score(y_va, proba)
        except Exception:
            out["roc_auc"] = float("nan")
    return out


def main() -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    train = pd.read_parquet(TRAIN_PATH)
    features = get_feature_columns(train)

    tscv = TimeSeriesSplit(n_splits=N_SPLITS)
    results: dict[str, list[dict]] = {alg: [] for alg in ALGORITHMS}

    for fold, (tr_idx, va_idx) in enumerate(tscv.split(train), 1):
        X_tr = train.iloc[tr_idx][features]
        y_tr = train.iloc[tr_idx]["fraud_bool"]
        X_va = train.iloc[va_idx][features]
        y_va = train.iloc[va_idx]["fraud_bool"]

        print(f"\n--- Fold {fold}/{N_SPLITS} "
              f"(train={len(X_tr):,}, val={len(X_va):,}) ---")
        for alg in ALGORITHMS:
            params = PARAM_GRIDS[alg][0]
            model = make_model(alg, params)
            m = evaluate_fold(model, X_tr, y_tr, X_va, y_va, alg)
            results[alg].append(m)
            print(f"  {alg:<22} Macro F1 = {m['macro_f1']:.4f}")

    # Persist raw results for evaluate_compare.py
    RESULTS_PATH.write_text(json.dumps(results, indent=2))

    # Markdown report
    lines = ["# Model Comparison: Primary 3-Algorithm Study\n",
             f"- CV strategy: {N_SPLITS}-fold `TimeSeriesSplit`",
             f"- Training rows: {len(train):,}",
             f"- Fraud rate: {train['fraud_bool'].mean():.4%}\n",
             "## Cross-Validation Results\n",
             "| Algorithm | Macro F1 (mean ± SD) | Accuracy | Precision (fraud) | Recall (fraud) | ROC-AUC |",
             "|---|---|---|---|---|---|"]
    for alg in ALGORITHMS:
        f1s   = [r["macro_f1"] for r in results[alg]]
        accs  = [r["accuracy"] for r in results[alg]]
        precs = [r["precision_fraud"] for r in results[alg]]
        recs  = [r["recall_fraud"] for r in results[alg]]
        aucs  = [r.get("roc_auc", float("nan")) for r in results[alg]]
        lines.append(
            f"| {alg} | {np.mean(f1s):.4f} ± {np.std(f1s):.4f} | "
            f"{np.mean(accs):.4f} | {np.mean(precs):.4f} | "
            f"{np.mean(recs):.4f} | {np.nanmean(aucs):.4f} |"
        )
    REPORT_PATH.write_text("\n".join(lines))
    print(f"\n[train_compare] Wrote {REPORT_PATH}")
    print(f"[train_compare] Wrote {RESULTS_PATH}")


if __name__ == "__main__":
    main()