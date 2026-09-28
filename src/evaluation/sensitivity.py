"""
Full cost sensitivity analysis.

Varies false_positive_cost, review_cost, residual_fraud_loss one at a time.
For each variation, recomputes decisions via argmin and realized cost for
the policy and all 5 baselines.

Does NOT retrain or rescore the model. Reads scored_test.parquet only.

Required by evaluation_protocol.md §14.

Run: python -m src.evaluation.sensitivity
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.common import DATA_PROCESSED, REPORTS, load_costs
from src.policy.decide import choose_actions
from src.evaluation.backtest import realized_cost

SEED = 42


def load_data() -> pd.DataFrame:
    """scored_test.parquet already contains fraud_bool and amount_proxy.
    No join required."""
    df = pd.read_parquet(DATA_PROCESSED / "scored_test.parquet")
    required = {
        "transaction_id", "fraud_bool", "amount_proxy",
        "p_fraud", "p_fraud_rf", "p_fraud_lgbm",
    }
    missing = required - set(df.columns)
    if missing:
        raise RuntimeError(f"scored_test.parquet missing columns: {missing}")
    return df








def baseline_actions(p_lr, p_rf, p_lgbm, rng):
    n = len(p_lr)
    return {
        "Random":         rng.choice(["approve", "review", "block"], size=n),
        "Approve-all":    np.full(n, "approve", dtype=object),
        "Block-all":      np.full(n, "block", dtype=object),
        "LR+0.5":         np.where(p_lr >= 0.5, "block", "approve").astype(object),
        "RF+0.5":         np.where(p_rf >= 0.5, "block", "approve").astype(object),
        "LGBM+0.5":       np.where(p_lgbm >= 0.5, "block", "approve").astype(object),
    }


def evaluate(df, costs, rng):
    p = df["p_fraud"].to_numpy()
    p_rf = df["p_fraud_rf"].to_numpy()
    p_lgbm = df["p_fraud_lgbm"].to_numpy()
    y = df["fraud_bool"].to_numpy()
    amount = df["amount_proxy"].to_numpy()

    results = {}
    for name, acts in baseline_actions(p, p_rf, p_lgbm, rng).items():
        results[name] = realized_cost(acts, y, costs, amounts=amount).mean()

    pol, _, _ = choose_actions(p, costs, amount)
    results["Policy"] = realized_cost(pol, y, costs, amounts=amount).mean()
    return results

def fmt_row(label, results):
    
    policy = results["Policy"]
    baselines = {k: v for k, v in results.items() if k != "Policy"}
    strongest = min(baselines, key=baselines.get)
    strongest_cost = baselines[strongest]
    adv = (strongest_cost - policy) / strongest_cost * 100.0
    return (
        f"| {label:<28} | {policy:.6f} | "
        f"{strongest:<14} | {strongest_cost:.6f} | {adv:>7.2f}% |"
    )


def main():
    base_costs = load_costs()
    df = load_data()
    rng = np.random.default_rng(SEED)

    print(f"[sensitivity] loaded {len(df):,} test rows")
    print(f"[sensitivity] base costs: {base_costs}")
    print()

    header = (
        f"| {'Config':<28} | {'Policy':>9} | "
        f"{'Strongest base':<14} | {'Cost':>9} | {'Adv':>8} |"
    )
    sep = "|" + "-" * 30 + "|" + "-" * 11 + "|" + "-" * 16 + "|" + "-" * 11 + "|" + "-" * 10 + "|"

    rows = []
    rows.append(("baseline", evaluate(df, base_costs, rng)))

    variations = [
        ("false_positive_cost", [0.05, 0.20]),
        ("review_cost",          [0.01, 0.04]),
        ("residual_fraud_loss",  [0.15, 0.60]),
    ]

    for param, values in variations:
        for v in values:
            costs = dict(base_costs)
            costs[param] = v
            rows.append((f"{param}={v}", evaluate(df, costs, rng)))

    print(header)
    print(sep)
    for label, res in rows:
        print(fmt_row(label, res))

    out = REPORTS / "sensitivity.md"
    lines = [
        "# Cost Sensitivity Analysis",
        "",
        "## Pre-registered stop criterion",
        "",
        "Success: the policy remains the lowest-cost action at every variation.",
        "Null: the policy's advantage over the strongest baseline drops below 5%",
        "relative at any variation.",
        "",
        f"Base config: `{base_costs}`",
        "",
        header,
        sep,
    ]
    for label, res in rows:
        lines.append(fmt_row(label, res))
    lines.append("")
    lines.append(
        "One-at-a-time variation. Amount scaling is held fixed at the "
        "train-calibrated rate. Decisions are recomputed at each setting; "
        "the model is not retrained."
    )
    out.write_text("\n".join(lines), encoding="utf-8")
    print()
    print(f"[sensitivity] wrote {out}")


if __name__ == "__main__":
    main()