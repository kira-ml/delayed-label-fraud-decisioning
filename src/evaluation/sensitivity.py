"""
Full cost sensitivity analysis.

Varies false_positive_cost, review_cost, residual_fraud_loss one at a time.
For each variation, recomputes decisions via argmin and realized cost for
the policy and all 5 baselines.

Does NOT retrain or rescore the model. Reads scored_test.parquet only.

Required by evaluation_protocol.md §12.1.

Run: python -m src.evaluation.sensitivity
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import yaml

from src.common import DATA_PROCESSED, REPORTS, CONFIGS

SEED = 42


def load_costs() -> dict:
    with open(CONFIGS / "costs.yaml") as f:
        return yaml.safe_load(f)


def load_data() -> pd.DataFrame:
    """scored_test.parquet already contains fraud_bool and amount_proxy.
    No join required."""
    df = pd.read_parquet(DATA_PROCESSED / "scored_test.parquet")
    required = {"transaction_id", "fraud_bool", "amount_proxy", "p_fraud"}
    missing = required - set(df.columns)
    if missing:
        raise RuntimeError(f"scored_test.parquet missing columns: {missing}")
    return df


def per_row_fraud_loss(amount: np.ndarray, costs: dict) -> np.ndarray:
    if costs["amount_scaled"]:
        return amount * costs["fraud_loss_rate"]
    return np.full_like(amount, costs["fraud_loss"], dtype=float)


def expected_costs(p, amount, costs):
    fl = per_row_fraud_loss(amount, costs)
    c_app = p * fl
    c_rev = costs["review_cost"] + p * costs["residual_fraud_loss"]
    c_blk = (1.0 - p) * costs["false_positive_cost"]
    return c_app, c_rev, c_blk


def realized_cost(actions, y, amount, costs):
    """actions: 0=approve, 1=review, 2=block"""
    fl = per_row_fraud_loss(amount, costs)
    cost = np.zeros(len(actions), dtype=float)

    m = actions == 0
    cost[m] = y[m] * fl[m]

    m = actions == 1
    cost[m] = costs["review_cost"] + y[m] * costs["residual_fraud_loss"]

    m = actions == 2
    cost[m] = (1.0 - y[m]) * costs["false_positive_cost"]

    return cost


def baseline_actions(p, rng):
    n = len(p)
    return {
        "Random":         rng.integers(0, 3, size=n),
        "Approve-all":    np.zeros(n, dtype=int),
        "Block-all":      np.full(n, 2, dtype=int),
        "Classifier+0.5": np.where(p >= 0.5, 2, 0),
    }


def policy_actions(p, amount, costs):
    c_app, c_rev, c_blk = expected_costs(p, amount, costs)
    return np.argmin(np.stack([c_app, c_rev, c_blk], axis=1), axis=1)


def evaluate(df, costs, rng):
    p = df["p_fraud"].to_numpy()
    y = df["fraud_bool"].to_numpy()
    amount = df["amount_proxy"].to_numpy()

    results = {}
    for name, acts in baseline_actions(p, rng).items():
        results[name] = realized_cost(acts, y, amount, costs).mean()

    pol = policy_actions(p, amount, costs)
    results["Policy"] = realized_cost(pol, y, amount, costs).mean()
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