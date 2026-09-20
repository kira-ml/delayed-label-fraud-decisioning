import numpy as np
import pandas as pd
from src.common import DATA_PROCESSED, load_costs

IN = DATA_PROCESSED / "scored_test.parquet"
OUT = DATA_PROCESSED / "action_log.parquet"

ACTIONS = np.array(["approve", "review", "block"])


def expected_costs(p, costs, amounts=None):
    """Return (c_approve, c_review, c_block) arrays for probabilities p.

    If costs['amount_scaled'] is true, fraud_loss becomes per-row:
        fraud_loss_i = amounts_i * fraud_loss_rate
    Otherwise fraud_loss is the constant from costs['fraud_loss'].

    residual_fraud_loss stays constant per decision_policy.md §7.
    """
    fp = float(costs["false_positive_cost"])
    rc = float(costs["review_cost"])
    rfl = float(costs["residual_fraud_loss"])
    p = np.asarray(p, dtype=float)

    if costs.get("amount_scaled", False):
        if amounts is None:
            raise ValueError("amount_scaled=true requires the amounts array")
        rate = float(costs["fraud_loss_rate"])
        fl = np.asarray(amounts, dtype=float) * rate
    else:
        fl = float(costs["fraud_loss"])

    c_app = p * fl
    c_rev = rc + p * rfl
    c_blk = (1.0 - p) * fp
    return c_app, c_rev, c_blk


def choose_actions(p, costs, amounts=None):
    """Argmin over {approve, review, block} of expected cost."""
    c_app, c_rev, c_blk = expected_costs(p, costs, amounts=amounts)
    stacked = np.vstack([c_app, c_rev, c_blk])
    idx = stacked.argmin(axis=0)
    return ACTIONS[idx], stacked.min(axis=0), (c_app, c_rev, c_blk)


def run():
    costs = load_costs()
    df = pd.read_parquet(IN)
    p = df["p_fraud"].to_numpy()
    amounts = df["amount_proxy"].to_numpy()

    actions, chosen, (c_app, c_rev, c_blk) = choose_actions(p, costs, amounts=amounts)

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

    if costs.get("amount_scaled", False):
        print("[decide] amount_scaled=true: thresholds are amount-dependent "
              "(see decision_policy.md §7)")
        print(f"[decide] fraud_loss_rate={costs['fraud_loss_rate']}")
    else:
        fl = float(costs["fraud_loss"])
        rc = float(costs["review_cost"])
        rfl = float(costs["residual_fraud_loss"])
        fp = float(costs["false_positive_cost"])
        p_review = rc / (fl - rfl) if (fl - rfl) > 0 else float("nan")
        p_block = (fp - rc) / (fp + rfl) if (fp + rfl) > 0 else float("nan")
        print(f"[decide] derived thresholds: p_review={p_review:.4f}, p_block={p_block:.4f}")


if __name__ == "__main__":
    run()