"""Capacity-aware variant of the argmin decision policy.

Constrains the number of transactions routed to `review` in a window.
The argmin rule in src/policy/decide.py remains the source of truth;
capacity is an override on review routing only.

See docs/v2/protocols/decision_policy_capacity.md.
"""
from __future__ import annotations

import numpy as np

from src.policy.decide import choose_actions


def apply_capacity(
    c_approve: np.ndarray,
    c_review: np.ndarray,
    c_block: np.ndarray,
    K: int,
) -> np.ndarray:
    """Return actions under a capacity constraint of K reviews.

    Rows whose unconstrained argmin is `review` are ranked by
    `min(c_approve, c_block) - c_review` (descending). The top-K stay
    in review; the rest are routed by approve-vs-block argmin only.
    Rows not in the review band keep their unconstrained argmin action.

    Ties in savings are broken by transaction_id ascending, i.e. by
    position, because rows are assumed to be in transaction_id order.
    """
    n = len(c_approve)
    cost_matrix = np.column_stack([c_approve, c_review, c_block])
    idx = np.argmin(cost_matrix, axis=1)   # 0=approve, 1=review, 2=block

    actions = np.empty(n, dtype=object)
    actions[idx == 0] = "approve"
    actions[idx == 2] = "block"

    review_idx = np.where(idx == 1)[0]
    if len(review_idx) == 0:
        return actions

    best_non_review = np.minimum(c_approve, c_block)
    savings = best_non_review - c_review

    if len(review_idx) <= K:
        actions[review_idx] = "review"
        return actions

    # Stable sort: equal savings keep review_idx (ascending) order.
    order = review_idx[np.argsort(-savings[review_idx], kind="stable")]
    keep = order[:K]
    overflow = order[K:]

    actions[keep] = "review"
    overflow_actions = np.where(
        c_approve[overflow] <= c_block[overflow], "approve", "block"
    )
    actions[overflow] = overflow_actions
    return actions