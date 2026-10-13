"""Boundary tests for src/policy/decide_capacity.py.

See docs/v2/protocols/decision_policy_capacity.md §5.
"""
from __future__ import annotations

import numpy as np
import pytest

from src.policy.decide_capacity import apply_capacity


def _costs(n, c_app=0.5, c_rev=0.1, c_blk=0.5):
    """Synthetic per-row costs, all identical, for deterministic tests."""
    return (
        np.full(n, c_app, dtype=float),
        np.full(n, c_rev, dtype=float),
        np.full(n, c_blk, dtype=float),
    )


def test_no_review_band():
    """If review is never argmin, capacity has no effect."""
    c_app = np.array([0.1, 0.2, 0.3])
    c_rev = np.array([0.9, 0.9, 0.9])
    c_blk = np.array([0.5, 0.5, 0.5])
    actions = apply_capacity(c_app, c_rev, c_blk, K=0)
    assert list(actions) == ["approve", "approve", "approve"]


def test_capacity_above_band():
    """K >= band size preserves unconstrained review routing."""
    c_app = np.array([0.5, 0.5, 0.5])
    c_rev = np.array([0.1, 0.1, 0.1])
    c_blk = np.array([0.5, 0.5, 0.5])
    actions = apply_capacity(c_app, c_rev, c_blk, K=100)
    assert list(actions) == ["review", "review", "review"]


def test_capacity_zero():
    """K == 0: all review-band rows overflow to approve-vs-block argmin."""
    c_app = np.array([0.5, 0.5])
    c_rev = np.array([0.1, 0.1])
    c_blk = np.array([0.3, 0.7])   # row 0 -> block, row 1 -> approve
    actions = apply_capacity(c_app, c_rev, c_blk, K=0)
    assert list(actions) == ["block", "approve"]


def test_capacity_tight():
    """K < band: top-K by savings stay in review; rest overflow."""
    # 4 rows in review band, savings strictly descending by index.
    c_app = np.array([0.9, 0.8, 0.7, 0.6])
    c_rev = np.array([0.1, 0.1, 0.1, 0.1])
    c_blk = np.array([0.9, 0.9, 0.9, 0.9])
    # savings = min(c_app, c_blk) - c_rev = c_app - 0.1
    #         = [0.8, 0.7, 0.6, 0.5] -> keep top-2 = rows 0, 1
    actions = apply_capacity(c_app, c_rev, c_blk, K=2)
    assert list(actions) == ["review", "review", "approve", "approve"]


def test_ties_broken_by_index_ascending():
    """Equal savings keep the lower-index row when capacity binds."""
    # All four rows in review band with identical savings.
    c_app = np.array([0.5, 0.5, 0.5, 0.5])
    c_rev = np.array([0.1, 0.1, 0.1, 0.1])
    c_blk = np.array([0.5, 0.5, 0.5, 0.5])
    # savings identical -> keep first K = rows 0, 1
    actions = apply_capacity(c_app, c_rev, c_blk, K=2)
    assert list(actions) == ["review", "review", "approve", "approve"]