"""Expected Calibration Error (ECE) on the validation set.

Diagnostic only — not part of the pipeline. Answers one question:
does the policy's p_fraud behave like a real probability?

Per decision_policy.md §9, if ECE is high, expected costs are wrong and
the thresholds derived from them are wrong. This is the check that
tells us whether calibration work is justified.

Reads:  data/processed/val.parquet, models/best_model.pkl,
        models/preprocessing.pkl, models/feature_columns.json
Writes: nothing (prints ECE and a reliability table)
"""
import json
import numpy as np
import pandas as pd
import joblib
from src.common import DATA_PROCESSED, MODELS

VAL = DATA_PROCESSED / "val.parquet"
MODEL = MODELS / "best_model.pkl"
PREPROC = MODELS / "preprocessing.pkl"
FEATURES = MODELS / "feature_columns.json"

N_BINS = 10


def score_val():
    """Score the validation set with the selected classifier and its
    saved preprocessing pipeline.

    The gate is a property of the classifier that feeds the policy, so
    it must run against the selected classifier, not any retired
    booster from the earlier pipeline.
    """
    model = joblib.load(MODEL)
    pre = joblib.load(PREPROC)
    feats = json.loads(FEATURES.read_text(encoding="utf-8"))

    val = pd.read_parquet(VAL)
    X = pre.transform(val[feats])
    if hasattr(X, "toarray"):
        X = X.toarray()
    val["p_fraud"] = model.predict_proba(X)[:, 1]
    return val[["p_fraud", "fraud_bool"]]


def ece(p, y, n_bins=N_BINS):
    """Expected Calibration Error using quantile bins.

    Quantile bins keep bin counts roughly equal, which matters at a
    ~1% base rate where fixed-width bins would be dominated by the
    lowest bin.

    Returns (ece_value, bin_table_dataframe).
    """
    p = np.asarray(p, dtype=float)
    y = np.asarray(y, dtype=float)

    # Quantile bin edges; last bin closed on both sides.
    edges = np.quantile(p, np.linspace(0.0, 1.0, n_bins + 1))
    edges[0] = -np.inf
    edges[-1] = np.inf
    # Collapse duplicate edges (can happen when many p values are identical).
    edges = np.unique(edges)

    rows = []
    total_weight = 0.0
    weighted_gap = 0.0
    for i in range(len(edges) - 1):
        lo, hi = edges[i], edges[i + 1]
        mask = (p > lo) & (p <= hi)
        n = int(mask.sum())
        if n == 0:
            continue
        mean_p = float(p[mask].mean())
        mean_y = float(y[mask].mean())
        gap = abs(mean_p - mean_y)
        weight = n / len(p)
        weighted_gap += gap * weight
        total_weight += weight
        rows.append({
            "bin": i,
            "n": n,
            "share": weight,
            "mean_p": mean_p,
            "mean_y": mean_y,
            "gap": gap,
        })

    table = pd.DataFrame(rows)
    return weighted_gap, table


def main():
    val = score_val()
    p = val["p_fraud"].to_numpy()
    y = val["fraud_bool"].to_numpy()

    brier = float(np.mean((p - y) ** 2))
    base_rate = float(y.mean())
    brier_trivial = float(np.mean((base_rate - y) ** 2))

    ece_value, table = ece(p, y)

    print()
    print("=== Calibration diagnostic (validation set) ===")
    print(f"  n              : {len(val):,}")
    print(f"  base rate      : {base_rate:.4%}")
    print(f"  p_fraud range  : [{p.min():.6f}, {p.max():.6f}]")
    print()
    print(f"  Brier (model)  : {brier:.6f}")
    print(f"  Brier (trivial): {brier_trivial:.6f}")
    improvement = (brier_trivial - brier) / brier_trivial
    print(f"  Brier gain     : {improvement:.2%} over trivial")
    print()
    print(f"  ECE            : {ece_value:.4f}  ({ece_value:.2%})")
    print()
    print("=== Reliability table (quantile bins) ===")
    with pd.option_context("display.float_format", lambda v: f"{v:.6f}"):
        print(table.to_string(index=False))
    print()

    # Stop-criterion readout from evaluation_protocol.md §17.1
    print("=== Stop-criterion check (evaluation_protocol.md §17.1) ===")
    if ece_value < 0.05:
        print(f"  ECE = {ece_value:.4f} < 0.05")
        print("  -> NULL STOP. Calibration is acceptable. Do not add a calibration step.")
    else:
        print(f"  ECE = {ece_value:.4f} >= 0.05")
        print("  -> MEASURED FAILURE. One calibration method (Platt or isotonic) is justified.")
        print("     Fit on validation only. Re-measure ECE and re-run the backtest.")
        print("     Adopt only if cost/txn improves by >= 5% relative; otherwise revert.")


if __name__ == "__main__":
    main()