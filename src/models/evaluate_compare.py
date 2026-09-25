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

from src.common import SEED, MODELS, CATEGORICAL_COLS, load_costs
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
from src.policy.decide import choose_actions
from src.evaluation.backtest import realized_cost

TRAIN_PATH = Path("data/processed/train.parquet")
TEST_PATH = Path("data/processed/test.parquet")
MODEL_PATH = Path("models/best_model.pkl")
PREPROC_PATH = Path("models/preprocessing.pkl")
FEATURES_PATH = Path("models/feature_columns.json")
DEFAULTS_PATH = Path("models/feature_defaults.json")
FINAL_REPORT = Path("reports/model_comparison.md")

# Noise-band guard, per docs/evaluation_protocol.md v1.0 §17.1 and §13.2.
# A selection counts as a finding only if the top classifier wins every
# fold and the relative gap to the runner-up exceeds MIN_RELATIVE_EFFECT.
MIN_RELATIVE_EFFECT = 0.05
SIMPLICITY_ORDER = ["logistic_regression", "random_forest", "lightgbm"]


def select_best() -> tuple[str, bool]:
    """Pick the algorithm with the lowest mean CV realized cost.

    Applies the noise-band guard from docs/evaluation_protocol.md v1.0
    §17.1. A selection is a finding only if the top classifier wins
    every fold AND the relative gap to the runner-up exceeds
    MIN_RELATIVE_EFFECT. Otherwise it is reported as a non-finding and
    the tie is broken by SIMPLICITY_ORDER (most interpretable first),
    per §8.

    Returns (algorithm, is_finding).
    """
    data = json.loads(RESULTS_PATH.read_text())
    results = data["results"]

    means = {
        alg: float(np.mean([r["realized_cost"] for r in results[alg]]))
        for alg in ALGORITHMS
    }
    n_folds = len(results[ALGORITHMS[0]])

    per_fold_winners: list[str] = []
    for fi in range(n_folds):
        fold_costs = {alg: results[alg][fi]["realized_cost"]
                      for alg in ALGORITHMS}
        per_fold_winners.append(min(fold_costs, key=fold_costs.get))

    ranked = sorted(means.items(), key=lambda kv: kv[1])
    best_alg, best_mean = ranked[0]
    second_alg, second_mean = ranked[1]
    gap = second_mean - best_mean
    rel_gap = gap / best_mean if best_mean > 0 else 0.0
    consistent = all(w == best_alg for w in per_fold_winners)

    print("[evaluate_compare] CV realized cost means (lower is better):")
    for alg, m in ranked:
        print(f"  {alg:<22} {m:.6f}")
    print(f"[evaluate_compare] Per-fold winners: {per_fold_winners}")
    print(f"[evaluate_compare] Top gap: {gap:.6f} "
          f"({rel_gap:.2%} relative, threshold {MIN_RELATIVE_EFFECT:.0%})")
    print(f"[evaluate_compare] Consistent winner across folds: {consistent}")

    if consistent and rel_gap >= MIN_RELATIVE_EFFECT:
        print(f"[evaluate_compare] Finding: {best_alg} selected on cost")
        return best_alg, True

    candidates = [
        alg for alg in SIMPLICITY_ORDER
        if alg in means
        and (means[alg] - best_mean) / best_mean < MIN_RELATIVE_EFFECT
    ]
    tiebreak = candidates[0] if candidates else best_alg
    print(f"[evaluate_compare] Non-finding (within noise band). "
          f"Tiebreak by simplicity: {tiebreak}")
    return tiebreak, False


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

    best_alg, is_finding = select_best()
    _data = json.loads(RESULTS_PATH.read_text())
    best_params = _data["selected_params"][best_alg]
    print(f"\n[evaluate_compare] Selected: {best_alg}")
    print(f"[evaluate_compare] Configuration: {best_params}")

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

    # Evaluate ONCE on the untouched test window (months 5-6)
    X_test = test[features]
    y_test = test["fraud_bool"]
    amounts_test = test["amount_proxy"].to_numpy()
    X_test_t = _to_array(pre.transform(X_test))

    # Classifier probabilities (required for the policy)
    p_fraud = model.predict_proba(X_test_t)[:, 1]
    # 0.5-cut predictions, kept as supporting evidence only
    y_pred = (p_fraud >= 0.5).astype(int)

    # Primary: apply the decision policy (docs/decision_policy.md §5.4)
    costs = load_costs()
    actions, chosen_cost, (c_app, c_rev, c_blk) = choose_actions(
        p_fraud, costs, amounts_test
    )
    realized = realized_cost(actions, y_test, costs, amounts=amounts_test)

    # Operational recall and precision of the policy itself
    y_test_arr = np.asarray(y_test)
    fraud_mask = y_test_arr == 1
    policy_flag = (actions == "review") | (actions == "block")
    policy_recall = (
        float(policy_flag[fraud_mask].mean()) if fraud_mask.sum() else 0.0
    )
    policy_precision = (
        float(fraud_mask[policy_flag].mean()) if policy_flag.sum() else 0.0
    )

    # Budget metrics: precision and recall at top-1/5/10% by p_fraud
    n = len(p_fraud)
    fraud_total = int(fraud_mask.sum())
    order = np.argsort(-p_fraud)
    budget_metrics = {}
    for frac in (0.01, 0.05, 0.10):
        k = max(1, int(np.ceil(frac * n)))
        top = order[:k]
        tp = int(fraud_mask[top].sum())
        budget_metrics[f"precision_at_{int(frac * 100)}pct"] = float(tp / k)
        budget_metrics[f"recall_at_{int(frac * 100)}pct"] = (
            float(tp / fraud_total) if fraud_total else 0.0
        )

    primary = {
        "realized_cost_per_txn": float(realized.mean()),
        "total_realized_cost": float(realized.sum()),
        "action_approve": int((actions == "approve").sum()),
        "action_review":  int((actions == "review").sum()),
        "action_block":   int((actions == "block").sum()),
        "policy_recall": policy_recall,
        "policy_precision": policy_precision,
        **budget_metrics,
    }

    # Supporting: classification behavior at the default 0.5 cut
    metrics = {
        "algorithm": best_alg,
        "macro_f1": float(f1_score(y_test, y_pred, average="macro", zero_division=0)),
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision_fraud": float(precision_score(y_test, y_pred, pos_label=1, zero_division=0)),
        "recall_fraud": float(recall_score(y_test, y_pred, pos_label=1, zero_division=0)),
        "f1_fraud": float(f1_score(y_test, y_pred, pos_label=1, zero_division=0)),
        "precision_legit": float(precision_score(y_test, y_pred, pos_label=0, zero_division=0)),
        "recall_legit": float(recall_score(y_test, y_pred, pos_label=0, zero_division=0)),
        "f1_legit": float(f1_score(y_test, y_pred, pos_label=0, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_test, p_fraud)),
    }
    cm = confusion_matrix(y_test, y_pred).tolist()

    print("\n[evaluate_compare] Primary result (realized cost of the policy):")
    for k, v in primary.items():
        print(f"  {k:<26} {v}")
    print("\n[evaluate_compare] Supporting classification metrics (0.5 cut):")
    for k, v in metrics.items():
        print(f"  {k:<16} {v}")
    print(f"  confusion_matrix {cm}")



    # Save global feature importances for the app's explainability panel.
    # Tree-based models expose feature_importances_ directly. Linear models
    # expose coef_ whose absolute value ranks feature contributions the
    # same way; when the preprocessor one-hot expands categoricals, coef_
    # is longer than the raw feature list, so one-hot coefficients are
    # aggregated back to their original feature names. If a model exposes
    # neither, remove any stale file so the app does not display
    # importances for a model it no longer matches.
    def _aggregate_linear_importances(model, pre, features):
        coef = np.abs(model.coef_).ravel()
        names_out = list(pre.get_feature_names_out())
        agg = {f: 0.0 for f in features}
        for name, c in zip(names_out, coef):
            if name.startswith("num__"):
                feat = name[len("num__"):]
            elif name.startswith("cat__"):
                rest = name[len("cat__"):]
                feat = max(
                    (f for f in features
                     if rest == f or rest.startswith(f + "_")),
                    key=len, default=None,
                )
            else:
                feat = None
            if feat is not None and feat in agg:
                agg[feat] += float(c)
        return [agg[f] for f in features]

    importances = None
    if hasattr(model, "feature_importances_"):
        importances = list(map(float, model.feature_importances_))
    elif hasattr(model, "coef_"):
        try:
            importances = _aggregate_linear_importances(model, pre, features)
        except Exception as exc:
            print(f"[evaluate_compare] Could not aggregate linear "
                  f"importances: {type(exc).__name__}: {exc}")
            importances = None

    imp_path = MODELS / "feature_importances.json"
    if importances is not None and len(importances) == len(features):
        imp_path.write_text(
            json.dumps({"features": list(features), "importances": importances},
                       indent=2),
            encoding="utf-8",
        )
        print(f"[evaluate_compare] Wrote {imp_path}")
    elif imp_path.exists():
        imp_path.unlink()
        print(f"[evaluate_compare] Removed stale {imp_path} "
              f"(importances unavailable or length mismatch)")

    # Persist the model and preprocessing pipeline
    joblib.dump(model, MODEL_PATH)
    joblib.dump(pre, PREPROC_PATH)
    print(f"\n[evaluate_compare] Saved model -> {MODEL_PATH}")
    print(f"[evaluate_compare] Saved preprocessing -> {PREPROC_PATH}")

    # Write a final-test section to the report (idempotent on re-runs)
    marker = "\n\n## Final Test Results\n"
    text = FINAL_REPORT.read_text(encoding="utf-8")
    if marker in text:
        text = text.split(marker, 1)[0]
    tn, fp, fn, tp = cm[0][0], cm[0][1], cm[1][0], cm[1][1]
    dominant = "false negatives" if fn > fp else "false positives"
    dominant_count = fn if fn > fp else fp
    other_count = fp if fn > fp else fn

    body = ["\n\n## Final Test Results\n\n",
            f"Selected algorithm: **{best_alg}**\n\n",
            "### Primary: Realized cost of the policy\n\n",
            "| Metric | Value |\n|---|---|\n"]
    for k, v in primary.items():
        body.append(f"| {k} | {v} |\n")
    body.append("\n### Supporting: Classification behavior at the 0.5 cut\n\n")
    body.append("| Metric | Value |\n|---|---|\n")
    for k, v in metrics.items():
        body.append(f"| {k} | {v} |\n")
    body.append(f"\nConfusion matrix (rows=true, cols=pred): `{cm}`\n")
    body.append("\n## Selection Justification\n\n")
    if is_finding:
        body.append(
            f"**{best_alg}** achieved the lowest mean CV realized cost "
            "among the three classifiers, and the gap to the runner-up "
            "exceeded the pre-registered 5% effect-size threshold "
            "(see `docs/evaluation_protocol.md` v1.0 §13.2). The "
            "selection is reported as a finding.\n"
        )
    else:
        body.append(
            f"**{best_alg}** is the selection after the noise-band guard "
            "in `docs/evaluation_protocol.md` v1.0 §17.1. The top two "
            "classifiers were within the pre-registered 5% effect-size "
            "threshold, so the CV comparison is reported as a "
            "**non-finding** and the tie is broken by simplicity "
            "(LR > RF > LGBM), per §8. The test-window result for the "
            "selected classifier is reported once, below, as required "
            "by the evaluation protocol.\n"
        )
    body.append("\n## Failure Analysis\n\n")
    body.append(
        f"Test-window counts at the classifier's 0.5 cut: "
        f"TN={tn}, FP={fp}, FN={fn}, TP={tp}. The 0.5 cut is not the "
        "operating point of the deployed system. The primary system is "
        "the decision policy, which routes each transaction to "
        "approve / review / block by expected cost and is evaluated in "
        "the Primary table above. See `docs/decision_policy.md` §5 for "
        "the policy and `docs/evaluation_protocol.md` §10 for the metric "
        "definition.\n"
    )
    FINAL_REPORT.write_text(text + "".join(body), encoding="utf-8")


if __name__ == "__main__":
    main()