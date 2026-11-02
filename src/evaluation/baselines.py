"""Fair baselines for the cost-sensitive decision policy.

The 0.5 cut-off baseline is a weak operating point at a ~1% base rate.
This module adds the baselines a competent team would actually deploy:

  - cost-optimal single threshold (approve vs block), tuned on validation
  - cost-optimal two-threshold policy (approve / review / block), tuned on
    validation
  - amount-blind policy (constant fraud loss)
  - no-review policy (approve vs block, amount-scaled)
  - test-tuned oracle threshold (diagnostic upper bound, not deployable)

All thresholds are tuned on realized cost on the validation window and
applied unchanged to the test window. The test-tuned oracle is labelled
as a diagnostic and is never used as a deployable baseline.

See reports/ablation.md and docs/evaluation_protocol.md.
"""
from __future__ import annotations

import json

import joblib
import numpy as np
import pandas as pd

from src.common import DATA_PROCESSED, MODELS


def _to_array(X):
    if hasattr(X, "toarray"):
        return X.toarray()
    return X


def score_validation() -> pd.DataFrame:
    """Score the validation window with the saved classifier.

    Returns a frame with p_fraud, fraud_bool, amount_proxy and month.
    """
    model = joblib.load(MODELS / "best_model.pkl")
    pre = joblib.load(MODELS / "preprocessing.pkl")
    feats = json.loads((MODELS / "feature_columns.json").read_text(encoding="utf-8"))

    val = pd.read_parquet(DATA_PROCESSED / "val.parquet")
    X = _to_array(pre.transform(val[feats]))
    out = val[["fraud_bool", "amount_proxy", "month"]].copy()
    out["p_fraud"] = model.predict_proba(X)[:, 1]
    return out


def realized_cost_components(y, costs: dict, amounts=None):
    """Per-row realized cost for each action under the frozen cost matrix.

    Mirrors src.evaluation.backtest.realized_cost, but returns the three
    action components so threshold grids can be evaluated with prefix sums.
    """
    y = np.asarray(y)
    fraud = y == 1

    if costs.get("amount_scaled", False):
        if amounts is None:
            raise ValueError("amount_scaled=true requires the amounts array")
        fraud_loss = np.asarray(amounts, dtype=float) * float(costs["fraud_loss_rate"])
    else:
        fraud_loss = np.full(len(y), float(costs["fraud_loss"]))

    rc = float(costs["review_cost"])
    rfl = float(costs["residual_fraud_loss"])
    fp = float(costs["false_positive_cost"])

    c_approve = np.where(fraud, fraud_loss, 0.0)
    c_review = np.where(fraud, rc + rfl, rc)
    c_block = np.where(fraud, 0.0, fp)
    return c_approve, c_review, c_block


def actions_single_threshold(p, t: float) -> np.ndarray:
    """Approve below t, block at or above t."""
    return np.where(np.asarray(p) >= t, "block", "approve").astype(object)


def actions_two_threshold(p, t_lo: float, t_hi: float) -> np.ndarray:
    """Approve below t_lo, review in [t_lo, t_hi), block at or above t_hi."""
    p = np.asarray(p)
    return np.where(
        p >= t_hi, "block",
        np.where(p >= t_lo, "review", "approve"),
    ).astype(object)


def _prefix_costs(c_approve, c_review, c_block):
    a = np.concatenate([[0.0], np.cumsum(c_approve)])
    r = np.concatenate([[0.0], np.cumsum(c_review)])
    b = np.concatenate([[0.0], np.cumsum(c_block)])
    return a, r, b


def _candidate_indices(n: int, n_grid: int) -> np.ndarray:
    """Sorted index positions spanning the whole score distribution.

    Quantile-spaced positions give resolution where the thresholds matter
    (the upper tail at a ~1% base rate) without scanning every unique score.
    `n` is included so the all-approve (single) and no-block (two-threshold)
    boundaries are reachable.
    """
    n_grid = max(2, min(n_grid, n))
    idx = np.unique(np.linspace(0, n - 1, n_grid).astype(int))
    return np.unique(np.append(idx, n))


def best_single_threshold(
    probs,
    y,
    costs: dict,
    amounts=None,
    n_grid: int = 600,
) -> tuple[float, float]:
    """Return (threshold, realized_cost_per_txn) minimizing validation cost.

    The threshold is the first score routed to block. Ties in cost keep the
    lower threshold (more blocking) only if it is strictly cheaper, so the
    result is deterministic.
    """
    probs = np.asarray(probs, dtype=float)
    c_app, c_rev, c_blk = realized_cost_components(y, costs, amounts)

    order = np.argsort(probs, kind="stable")
    ps = probs[order]
    a, _, b = _prefix_costs(c_app[order], c_rev[order], c_blk[order])
    n = len(ps)

    best_i, best_cost = n, float(b[n] / n)  # approve everything
    for i in _candidate_indices(n, n_grid):
        # [0, i) approve, [i, n) block
        total = a[i] + (b[n] - b[i])
        cost = float(total / n)
        if cost < best_cost:
            best_i, best_cost = int(i), cost

    threshold = float(ps[best_i]) if best_i < n else float("inf")
    return threshold, best_cost


def best_two_threshold(
    probs,
    y,
    costs: dict,
    amounts=None,
    n_grid: int = 400,
) -> tuple[float, float, float]:
    """Return (t_lo, t_hi, realized_cost_per_txn) minimizing validation cost.

    Approve below t_lo, review in [t_lo, t_hi), block at or above t_hi.
    The grid is evaluated with prefix sums, so the pair scan is O(n_grid^2)
    with O(1) work per pair.
    """
    probs = np.asarray(probs, dtype=float)
    c_app, c_rev, c_blk = realized_cost_components(y, costs, amounts)

    order = np.argsort(probs, kind="stable")
    ps = probs[order]
    a, r, b = _prefix_costs(c_app[order], c_rev[order], c_blk[order])
    n = len(ps)
    idx = _candidate_indices(n, n_grid)

    best = (float("inf"), 0, n)  # (cost, i_lo, i_hi)
    for i_lo in idx:
        # i_hi must be strictly greater; start at the next candidate.
        for i_hi in idx:
            if i_hi <= i_lo:
                continue
            total = a[i_lo] + (r[i_hi] - r[i_lo]) + (b[n] - b[i_hi])
            cost = float(total / n)
            if cost < best[0]:
                best = (cost, int(i_lo), int(i_hi))

    _, i_lo, i_hi = best
    t_lo = float(ps[i_lo]) if i_lo > 0 else float("-inf")
    t_hi = float(ps[i_hi]) if i_hi < n else float("inf")
    return t_lo, t_hi, best[0]


def amount_blind_actions(p, costs: dict, fraud_loss: float = 1.0) -> np.ndarray:
    """Actions from the same argmin rule with a constant fraud loss.

    Isolates the value of amount-conditioned fraud loss. The constant 1.0
    is the mean of the amount-scaled loss on the training window
    (fraud_loss_rate = 1 / mean(amount)), so the two rules are comparable
    on average and differ only in how they use the amount.
    """
    from src.policy.decide import choose_actions

    flat = dict(costs)
    flat["amount_scaled"] = False
    flat["fraud_loss"] = float(fraud_loss)
    actions, _, _ = choose_actions(np.asarray(p), flat, None)
    return actions


def no_review_actions(p, costs: dict, amounts) -> np.ndarray:
    """Amount-scaled approve-vs-block only; the review action is removed."""
    p = np.asarray(p, dtype=float)
    amounts = np.asarray(amounts, dtype=float)
    c_approve = p * amounts * float(costs["fraud_loss_rate"])
    c_block = (1.0 - p) * float(costs["false_positive_cost"])
    return np.where(c_block < c_approve, "block", "approve").astype(object)
