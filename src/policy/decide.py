"""Cost-sensitive decision policy: argmin of expected cost.

This is the source of truth. Derived thresholds in the report are a
diagnostic view only. See docs/decision_policy.md §5.4 and §6.5.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
import yaml

SCORED_PATH = Path("data/processed/scored_test.parquet")
COSTS_PATH = Path("configs/costs.yaml")
OUT_PATH = Path("data/processed/action_log.parquet")

ACTIONS = np.array(["approve", "review", "block"])


def load_costs(path: Path = COSTS_PATH) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def choose_actions(p: np.ndarray,
                   costs: dict,
                   amounts: np.ndarray | None = None):
    """Pure argmin-of-expected-cost function.

    Args:
        p:        fraud probabilities, shape (n,)
        costs:    dict with fraud_loss, false_positive_cost,
                  review_cost, residual_fraud_loss, amount_scaled
        amounts:  optional transaction amounts, shape (n,).
                  Used only when costs['amount_scaled'] is True.

    Returns:
        actions:    np.ndarray of shape (n,) with values in ACTIONS
        cost_matrix: np.ndarray of shape (n, 3) with [approve, review, block]
    """
    p = np.asarray(p, dtype=float)
    n = len(p)

    if costs.get("amount_scaled", False) and amounts is not None:
        amounts = np.asarray(amounts, dtype=float)
        fraud_loss = amounts * float(costs["fraud_loss_rate"])
    else:
        fraud_loss = np.full(n, float(costs["fraud_loss"]))

    c_approve = p * fraud_loss
    c_review = float(costs["review_cost"]) + p * float(costs["residual_fraud_loss"])
    c_block = (1.0 - p) * float(costs["false_positive_cost"])

    cost_matrix = np.column_stack([c_approve, c_review, c_block])
    idx = np.argmin(cost_matrix, axis=1)
    return ACTIONS[idx], cost_matrix


def main() -> None:
    scored = pd.read_parquet(SCORED_PATH)
    costs = load_costs()

    amounts = (scored["amount_proxy"].values
               if "amount_proxy" in scored.columns else None)
    actions, cost_matrix = choose_actions(scored["p_fraud"].values, costs, amounts)

    log = pd.DataFrame({
        "transaction_id": scored["transaction_id"].values,
        "month": scored["month"].values,
        "p_fraud": scored["p_fraud"].values,
        "action": actions,
        "expected_cost_approve": cost_matrix[:, 0],
        "expected_cost_review":  cost_matrix[:, 1],
        "expected_cost_block":   cost_matrix[:, 2],
        "chosen_expected_cost":  cost_matrix.min(axis=1),
        "reason": "argmin_expected_cost",
    })
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    log.to_parquet(OUT_PATH, index=False)

    print(f"[decide] Actions: {log['action'].value_counts().to_dict()}")
    print(f"[decide] Wrote action log to {OUT_PATH}")


if __name__ == "__main__":
    main()