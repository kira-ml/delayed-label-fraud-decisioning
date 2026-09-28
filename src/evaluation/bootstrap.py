"""
Bootstrap confidence intervals on cost per transaction.

Resamples test rows with replacement (N=1000). Reports:
  - Policy cost/txn 95% CI
  - Strongest baseline cost/txn 95% CI
  - Difference (advantage) 95% CI

Required by evaluation_protocol.md §13.1.

Run: python -m src.evaluation.bootstrap
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.common import DATA_PROCESSED, REPORTS, load_costs
from src.policy.decide import choose_actions
from src.evaluation.backtest import realized_cost

SEED = 42
N_BOOT = 1000

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





def static_actions(p):
    return np.where(p >= 0.5, "block", "approve").astype(object)


def main():
    costs = load_costs()
    df = load_data()

    p = df["p_fraud"].to_numpy()
    y = df["fraud_bool"].to_numpy()
    amount = df["amount_proxy"].to_numpy()
    n = len(df)

    pol_actions, _, _ = choose_actions(p, costs, amount)
    pol_cost = realized_cost(pol_actions, y, costs, amounts=amount)

    rng_baselines = np.random.default_rng(SEED)
    baselines = {
        "Random":         rng_baselines.choice(["approve", "review", "block"], size=n),
        "Approve-all":    np.full(n, "approve", dtype=object),
        "Block-all":      np.full(n, "block", dtype=object),
        "LR+0.5":         static_actions(p),
        "RF+0.5":         static_actions(df["p_fraud_rf"].to_numpy()),
        "LGBM+0.5":       static_actions(df["p_fraud_lgbm"].to_numpy()),
    }
    bas_costs = {
        name: realized_cost(acts, y, costs, amounts=amount)
        for name, acts in baselines.items()
    }
    strongest_name = min(bas_costs, key=lambda k: bas_costs[k].mean())
    bas_cost = bas_costs[strongest_name]
    print(f"[bootstrap] strongest baseline: {strongest_name}")

    pol_point = pol_cost.mean()
    bas_point = bas_cost.mean()
    diff_point = bas_point - pol_point
    adv_point = diff_point / bas_point * 100.0

    print(f"[bootstrap] N={n:,}, iterations={N_BOOT}")
    print(f"[bootstrap] point estimates:")
    print(f"  Policy           : {pol_point:.6f}")
    print(f"  {strongest_name:<16} : {bas_point:.6f}")
    print(f"  Difference       : {diff_point:.6f}")
    print(f"  Advantage        : {adv_point:.2f}%")
    print()

    rng = np.random.default_rng(SEED)
    pol_boot = np.empty(N_BOOT)
    bas_boot = np.empty(N_BOOT)
    diff_boot = np.empty(N_BOOT)

    for i in range(N_BOOT):
        idx = rng.integers(0, n, size=n)
        pc = pol_cost[idx].mean()
        bc = bas_cost[idx].mean()
        pol_boot[i] = pc
        bas_boot[i] = bc
        diff_boot[i] = bc - pc

    def ci(a):
        return np.percentile(a, [2.5, 97.5])

    pol_lo, pol_hi = ci(pol_boot)
    bas_lo, bas_hi = ci(bas_boot)
    dif_lo, dif_hi = ci(diff_boot)

    print(f"[bootstrap] 95% CIs:")
    print(f"  Policy     : [{pol_lo:.6f}, {pol_hi:.6f}]")
    print(f"  Baseline   : [{bas_lo:.6f}, {bas_hi:.6f}]")
    print(f"  Difference : [{dif_lo:.6f}, {dif_hi:.6f}]")
    print()

    adv_lo = dif_lo / bas_point * 100.0
    adv_hi = dif_hi / bas_point * 100.0
    print(f"[bootstrap] Advantage 95% CI: [{adv_lo:.2f}%, {adv_hi:.2f}%]")

    excludes_zero = dif_lo > 0
    print(f"[bootstrap] Difference CI excludes zero: {excludes_zero}")

    out = REPORTS / "bootstrap.md"
    lines = [
        "# Bootstrap Confidence Intervals",
        "",
        "## Pre-registered stop criterion",
        "",
        "Success: the 95% CI on the difference (baseline − policy) excludes zero.",
        "Null: the CI includes zero.",
        "",
        f"Resampling: {N_BOOT} iterations, seed={SEED}, n={n:,}",
        "",
        "| Quantity | Point estimate | 95% CI |",
        "|---|---:|---|",
        f"| Policy cost/txn | {pol_point:.6f} | [{pol_lo:.6f}, {pol_hi:.6f}] |",
        f"| {strongest_name} cost/txn | {bas_point:.6f} | [{bas_lo:.6f}, {bas_hi:.6f}] |",
        f"| Difference (baseline − policy) | {diff_point:.6f} | [{dif_lo:.6f}, {dif_hi:.6f}] |",
        f"| Advantage (%) | {adv_point:.2f}% | [{adv_lo:.2f}%, {adv_hi:.2f}%] |",
        "",
        f"**Difference CI excludes zero:** {excludes_zero}",
        "",
    ]
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"[bootstrap] wrote {out}")


if __name__ == "__main__":
    main()