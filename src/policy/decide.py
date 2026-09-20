import numpy as np
import pandas as pd
from src.common import DATA_PROCESSED, load_costs

IN = DATA_PROCESSED / "scored_test.parquet"
OUT = DATA_PROCESSED / "action_log.parquet"

ACTIONS = np.array(["approve", "review", "block"])


def run():
    costs = load_costs()
    fl = float(costs["fraud_loss"])
    fp = float(costs["false_positive_cost"])
    rc = float(costs["review_cost"])
    rfl = float(costs["residual_fraud_loss"])

    df = pd.read_parquet(IN)
    p = df["p_fraud"].to_numpy()

    c_app = p * fl
    c_rev = rc + p * rfl
    c_blk = (1.0 - p) * fp

    stacked = np.vstack([c_app, c_rev, c_blk])  # 3 x N
    idx = stacked.argmin(axis=0)
    actions = ACTIONS[idx]
    chosen = stacked.min(axis=0)

    out = pd.DataFrame({
        "transaction_id": df["transaction_id"].to_numpy(),
        "month": df["month"].to_numpy(),
        "p_fraud": p,
        "action": actions,
        "expected_cost_approve": c_app,
        "expected_cost_review": c_rev,
        "expected_cost_block": c_blk,
        "chosen_expected_cost": chosen,
        "reason": "argmin_expected_cost",
    })
    out.to_parquet(OUT, index=False)

    counts = out["action"].value_counts().to_dict()
    print(f"[decide] wrote {OUT.name}: {len(out):,} rows")
    print(f"[decide] actions: {counts}")

    # Derived thresholds (diagnostic only, argmin is source of truth)
    p_review = rc / (fl - rfl) if (fl - rfl) > 0 else float("nan")
    p_block = (fp - rc) / (fp + rfl) if (fp + rfl) > 0 else float("nan")
    print(f"[decide] derived thresholds: p_review={p_review:.4f}, p_block={p_block:.4f}")


if __name__ == "__main__":
    run()