"""Classifier comparison with time-series CV.

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

from src.common import SEED, load_costs
from src.models.preprocess import (
    build_preprocessor, get_feature_columns, get_numeric_categorical,
)
from src.policy.decide import choose_actions
from src.evaluation.backtest import realized_cost

warnings.filterwarnings("ignore")

TRAIN_PATH = Path("data/processed/train.parquet")
REPORT_PATH = Path("reports/model_comparison.md")
RESULTS_PATH = Path("reports/cv_results.json")

ALGORITHMS = ["logistic_regression", "random_forest", "lightgbm"]
MAX_SPLITS = 5

# Small, documented grids (see docs/evaluation_protocol.md §5 and §8).
# No class_weight is used: the decision policy assumes p_fraud is a
# calibrated probability, and class reweighting would break that
# assumption. Cost asymmetry is handled by the policy, not the training
# objective. See docs/decision_policy.md §1 and §9.
PARAM_GRIDS = {
    "logistic_regression": [
        {"C": 0.01, "max_iter": 1000},
        {"C": 0.1,  "max_iter": 1000},
        {"C": 1.0,  "max_iter": 1000},
        {"C": 10.0, "max_iter": 1000},
    ],
    "random_forest": [
        {"n_estimators": 100, "n_jobs": -1, "random_state": SEED},
        {"n_estimators": 200, "n_jobs": -1, "random_state": SEED},
        {"n_estimators": 400, "n_jobs": -1, "random_state": SEED},
    ],
    "lightgbm": [
        {"n_estimators": 100, "learning_rate": 0.10, "verbose": -1, "random_state": SEED},
        {"n_estimators": 300, "learning_rate": 0.10, "verbose": -1, "random_state": SEED},
        {"n_estimators": 300, "learning_rate": 0.05, "verbose": -1, "random_state": SEED},
        {"n_estimators": 500, "learning_rate": 0.05, "verbose": -1, "random_state": SEED},
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


def evaluate_fold(model, X_tr, y_tr, X_va, y_va, algorithm: str,
                  amounts_va=None, costs=None) -> dict:
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
        "precision_legit": precision_score(y_va, y_pred, pos_label=0, zero_division=0),
        "recall_legit": recall_score(y_va, y_pred, pos_label=0, zero_division=0),
        "f1_legit": f1_score(y_va, y_pred, pos_label=0, zero_division=0),
    }
    if hasattr(model, "predict_proba"):
        try:
            proba = model.predict_proba(X_va_t)[:, 1]
            out["roc_auc"] = roc_auc_score(y_va, proba)
            if costs is not None and amounts_va is not None:
                actions, _, _ = choose_actions(proba, costs, amounts_va)
                rc = realized_cost(actions, y_va, costs, amounts=amounts_va)
                out["realized_cost"] = float(rc.mean())
        except Exception:
            out["roc_auc"] = float("nan")
    return out


def main() -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    train = pd.read_parquet(TRAIN_PATH)
    features = get_feature_columns(train)
    costs = load_costs()

    months = sorted(train["month"].unique())
    n_folds = min(MAX_SPLITS, len(months) - 1)

    # grid_results[alg][config_idx] = list of per-fold metric dicts
    grid_results: dict[str, list[list[dict]]] = {
        alg: [[] for _ in PARAM_GRIDS[alg]] for alg in ALGORITHMS
    }

    for fold in range(n_folds):
        tr_months = months[:fold + 1]
        va_months = [months[fold + 1]]
        X_tr = train[train["month"].isin(tr_months)][features]
        y_tr = train[train["month"].isin(tr_months)]["fraud_bool"]
        X_va = train[train["month"].isin(va_months)][features]
        y_va = train[train["month"].isin(va_months)]["fraud_bool"]
        amounts_va = train[train["month"].isin(va_months)]["amount_proxy"].to_numpy()

        print(f"\n--- Fold {fold + 1}/{n_folds} "
              f"(train months {tr_months}, val month {va_months[0]}) "
              f"train={len(X_tr):,}, val={len(X_va):,} ---")
        for alg in ALGORITHMS:
            for ci, params in enumerate(PARAM_GRIDS[alg]):
                model = make_model(alg, params)
                m = evaluate_fold(model, X_tr, y_tr, X_va, y_va, alg,
                                  amounts_va=amounts_va, costs=costs)
                grid_results[alg][ci].append(m)
                print(f"  {alg:<22} cfg#{ci}  "
                      f"Macro F1 = {m['macro_f1']:.4f}  "
                      f"cost/txn = {m.get('realized_cost', float('nan')):.6f}")

    # Pick the best configuration per algorithm by mean realized cost.
    best_config_idx: dict[str, int] = {}
    for alg in ALGORITHMS:
        means = [
            float(np.nanmean([r.get("realized_cost", float("nan"))
                              for r in grid_results[alg][ci]]))
            for ci in range(len(PARAM_GRIDS[alg]))
        ]
        best_config_idx[alg] = int(np.nanargmin(means))
        print(f"[train_compare] {alg:<22} best cfg#{best_config_idx[alg]}  "
              f"mean cost/txn = {means[best_config_idx[alg]]:.6f}")

    # Flatten to the existing per-algorithm fold-list schema so downstream
    # consumers keep reading results[alg] unchanged.
    results: dict[str, list[dict]] = {
        alg: grid_results[alg][best_config_idx[alg]] for alg in ALGORITHMS
    }
    selected_params: dict[str, dict] = {
        alg: PARAM_GRIDS[alg][best_config_idx[alg]] for alg in ALGORITHMS
    }

    # Persist raw results for evaluate_compare.py
    RESULTS_PATH.write_text(
        json.dumps(
            {"results": results, "selected_params": selected_params},
            indent=2,
        ),
        encoding="utf-8",
    )

    # Markdown report
    lines = ["# Classifier Comparison (Policy Inputs)\n",
             f"- CV strategy: {n_folds}-fold expanding-window by month "
             "(train months 0..k, validate month k+1)",
             f"- Training rows: {len(train):,}",
             f"- Fraud rate: {train['fraud_bool'].mean():.4%}\n",
             "## Hyperparameters\n",
             "| Algorithm | Configuration |",
             "|---|---|"]
    for alg in ALGORITHMS:
        lines.append(f"| {alg} | `{selected_params[alg]}` |")
    lines.extend([
        "",
        "Each algorithm's configuration was selected by mean realized cost "
        "across the expanding-window folds. All configurations within an "
        "algorithm were evaluated on the same folds with the same "
        "preprocessing, so the selection is fair and reproducible "
        "(see `docs/evaluation_protocol.md` §5 and §8).",
        "",
        "## Selection Criterion: Realized Cost After the Policy\n",
        "| Algorithm | Realized cost/txn (mean ± SD) |",
        "|---|---|",
    ])
    for alg in ALGORITHMS:
        rcs = [r.get("realized_cost", float("nan")) for r in results[alg]]
        lines.append(
            f"| {alg} | {np.nanmean(rcs):.6f} ± {np.nanstd(rcs):.6f} |"
        )
    lines.extend([
        "",
        "Lowest mean realized cost wins. Classification metrics below are "
        "supporting evidence, not the criterion "
        "(see `docs/evaluation_protocol.md` §8 and §11).",
        "",
        "## Cross-Validation Results\n",
        "| Algorithm | Macro F1 (mean ± SD) | Accuracy | "
        "Precision (fraud) | Recall (fraud) | F1 (fraud) | "
        "Precision (legit) | Recall (legit) | F1 (legit) | ROC-AUC |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ])
    for alg in ALGORITHMS:
        f1s  = [r["macro_f1"] for r in results[alg]]
        accs = [r["accuracy"] for r in results[alg]]
        pf   = [r["precision_fraud"] for r in results[alg]]
        rf   = [r["recall_fraud"] for r in results[alg]]
        ff   = [r["f1_fraud"] for r in results[alg]]
        pl   = [r["precision_legit"] for r in results[alg]]
        rl   = [r["recall_legit"] for r in results[alg]]
        fl   = [r["f1_legit"] for r in results[alg]]
        aucs = [r.get("roc_auc", float("nan")) for r in results[alg]]
        lines.append(
            f"| {alg} | {np.mean(f1s):.4f} ± {np.std(f1s):.4f} | "
            f"{np.mean(accs):.4f} | {np.mean(pf):.4f} | "
            f"{np.mean(rf):.4f} | {np.mean(ff):.4f} | "
            f"{np.mean(pl):.4f} | {np.mean(rl):.4f} | {np.mean(fl):.4f} | "
            f"{np.nanmean(aucs):.4f} |"
        )
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n[train_compare] Wrote {REPORT_PATH}")
    print(f"[train_compare] Wrote {RESULTS_PATH}")


if __name__ == "__main__":
    main()