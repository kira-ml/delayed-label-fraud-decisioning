"""H1 — Capacity-constrained decisioning diagnostic.

Tests whether the V1 policy advantage (>5% relative cost reduction vs
the strongest baseline) is preserved when review is constrained to a
finite per-window capacity.

This test reruns the decision step on frozen V1 artifacts. No classifier
is retrained. No test-window score is recomputed. The frozen
`scored_test.parquet` scores are re-ranked and re-routed under a
capacity cap.

Reads:  data/processed/scored_test.parquet
        configs/costs.yaml
Writes: reports/v2/intermediate/h1_capacity.json

Run: python -m src.v2.capacity

See docs/v2/falsification_plan.md §3 H1 (as amended 2026-10-03) and
    docs/v2/evaluation_framework.md §5.1 and §6.1.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.common import DATA_PROCESSED, load_costs
from src.policy.decide import choose_actions
from src.evaluation.backtest import realized_cost
from src.policy.decide_capacity import apply_capacity

IN_PATH = DATA_PROCESSED / "scored_test.parquet"
OUT_DIR = Path("reports/v2/intermediate")
OUT_PATH = OUT_DIR / "h1_capacity.json"

# Pre-registered capacity levels from falsification_plan.md §3 H1.
CAPACITY_FRACTIONS = [0.01, 0.02, 0.05, 0.10, 0.20]
# Kill zone: tested capacities at or above 2% of test volume.
MIN_CAPACITY_FOR_KILL = 0.02
# Kill threshold: advantage must stay >= 5% in the kill zone.
ADVANTAGE_THRESHOLD = 0.05


def _baseline_actions(p_lr, p_rf, p_lgbm):
    """V1's canonical baseline set on the test window."""
    n = len(p_lr)
    rng = np.random.default_rng(42)
    return {
        "Random":      rng.choice(["approve", "review", "block"], size=n),
        "Approve-all": np.full(n, "approve", dtype=object),
        "Block-all":   np.full(n, "block", dtype=object),
        "LR+0.5":      np.where(p_lr >= 0.5, "block", "approve").astype(object),
        "RF+0.5":      np.where(p_rf >= 0.5, "block", "approve").astype(object),
        "LGBM+0.5":    np.where(p_lgbm >= 0.5, "block", "approve").astype(object),
    }




def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    costs = load_costs()
    df = pd.read_parquet(IN_PATH)
    required = {
        "transaction_id", "fraud_bool", "amount_proxy",
        "p_fraud", "p_fraud_rf", "p_fraud_lgbm",
    }
    missing = required - set(df.columns)
    if missing:
        raise RuntimeError(f"scored_test.parquet missing columns: {missing}")

    n = len(df)
    y = df["fraud_bool"].to_numpy()
    amount = df["amount_proxy"].to_numpy()
    p = df["p_fraud"].to_numpy()

    print(f"[capacity] Loaded {n:,} test-window rows")
    print(f"[capacity] Cost matrix: {costs}")
    print()

    # Frozen V1 scores; recompute expected costs and unconstrained actions.
    unconstrained_actions, _, (c_app, c_rev, c_blk) = choose_actions(
        p, costs, amount
    )
    unconstrained_cost = realized_cost(
        unconstrained_actions, y, costs, amounts=amount
    )
    unconstrained_mean = float(unconstrained_cost.mean())
    review_band_size = int((unconstrained_actions == "review").sum())

    print(f"[capacity] Unconstrained policy cost/txn: "
          f"{unconstrained_mean:.6f}")
    print(f"[capacity] Review band size: {review_band_size:,} "
          f"({100 * review_band_size / n:.2f}% of test rows)")
    print()

    # Canonical baselines, recomputed from frozen scores.
    baselines = _baseline_actions(
        df["p_fraud"].to_numpy(),
        df["p_fraud_rf"].to_numpy(),
        df["p_fraud_lgbm"].to_numpy(),
    )
    baseline_costs = {
        name: float(realized_cost(acts, y, costs, amounts=amount).mean())
        for name, acts in baselines.items()
    }
    strongest_name = min(baseline_costs, key=baseline_costs.get)
    strongest_cost = baseline_costs[strongest_name]

    print("[capacity] Baseline cost/txn:")
    for name, c in sorted(baseline_costs.items(), key=lambda kv: kv[1]):
        marker = "  <-- strongest" if name == strongest_name else ""
        print(f"  {name:<14} {c:.6f}{marker}")
    print()

    K_min_for_kill = int(np.ceil(MIN_CAPACITY_FOR_KILL * n))
    print(f"[capacity] Kill criterion: advantage < "
          f"{ADVANTAGE_THRESHOLD:.0%} at any K >= {K_min_for_kill:,} "
          f"({MIN_CAPACITY_FOR_KILL:.0%} of test volume)")
    print()

    results = {
        "hypothesis": "H1",
        "kill_criterion": (
            f"advantage < {ADVANTAGE_THRESHOLD:.0%} at any K >= "
            f"{K_min_for_kill} ({MIN_CAPACITY_FOR_KILL:.0%} of test volume)"
        ),
        "advantage_threshold": ADVANTAGE_THRESHOLD,
        "min_capacity_for_kill": K_min_for_kill,
        "test_rows": n,
        "cost_matrix": costs,
        "unconstrained_policy_cost_per_txn": unconstrained_mean,
        "review_band_size": review_band_size,
        "strongest_baseline": strongest_name,
        "strongest_baseline_cost_per_txn": strongest_cost,
        "baselines": baseline_costs,
        "capacity_levels": [],
    }

    print(f"{'K':>10}{'K_frac':>9}{'policy':>12}"
          f"{'baseline':>12}{'advantage':>12}{'verdict':>18}")
    print("-" * 73)

    kill_triggered = False
    for frac in CAPACITY_FRACTIONS:
        K = int(np.ceil(frac * n))
        actions = apply_capacity(c_app, c_rev, c_blk, K)
        cost = realized_cost(actions, y, costs, amounts=amount)
        mean_cost = float(cost.mean())
        adv = (strongest_cost - mean_cost) / strongest_cost
        in_kill_zone = K >= K_min_for_kill

        if in_kill_zone and adv < ADVANTAGE_THRESHOLD:
            verdict = "KILL"
            kill_triggered = True
        elif adv < ADVANTAGE_THRESHOLD:
            verdict = "below threshold"
        else:
            verdict = "pass"

        action_counts = {
            "approve": int((actions == "approve").sum()),
            "review":  int((actions == "review").sum()),
            "block":   int((actions == "block").sum()),
        }

        results["capacity_levels"].append({
            "K": K,
            "K_frac": frac,
            "in_kill_zone": in_kill_zone,
            "policy_cost_per_txn": mean_cost,
            "advantage_vs_strongest": adv,
            "action_counts": action_counts,
            "verdict": verdict,
        })

        print(f"{K:>10,}{frac:>9.0%}{mean_cost:>12.6f}"
              f"{strongest_cost:>12.6f}{adv:>11.2%}  {verdict:>16}")

    results["verdict"] = "killed" if kill_triggered else "survived"

    print()
    print(f"[capacity] Overall verdict: {results['verdict']}")

    OUT_PATH.write_text(
        json.dumps(results, indent=2, default=str),
        encoding="utf-8",
    )
    print(f"[capacity] Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()