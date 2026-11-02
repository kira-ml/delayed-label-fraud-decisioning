"""Unit tests for the fair baselines and threshold oracles."""
import numpy as np
import pytest

from src.evaluation.backtest import realized_cost
from src.evaluation.baselines import (
    actions_single_threshold,
    actions_two_threshold,
    amount_blind_actions,
    best_single_threshold,
    best_two_threshold,
    no_review_actions,
    realized_cost_components,
)

COSTS = {
    "fraud_loss": 1.0,
    "false_positive_cost": 0.1,
    "review_cost": 0.02,
    "residual_fraud_loss": 0.3,
    "amount_scaled": True,
    "fraud_loss_rate": 0.01,
}


def _synthetic(n=60, seed=7):
    rng = np.random.default_rng(seed)
    p = rng.beta(0.35, 12.0, size=n)  # skewed toward 0, like fraud scores
    y = (rng.random(n) < np.clip(p * 3.0, 0.0, 1.0)).astype(int)
    amounts = rng.lognormal(mean=5.5, sigma=0.8, size=n)
    return p, y, amounts


def test_single_threshold_actions():
    p = np.array([0.01, 0.4, 0.9])
    acts = actions_single_threshold(p, 0.4)
    assert list(acts) == ["approve", "block", "block"]


def test_two_threshold_actions():
    p = np.array([0.01, 0.1, 0.9])
    acts = actions_two_threshold(p, 0.05, 0.5)
    assert list(acts) == ["approve", "review", "block"]


def test_components_match_backtest():
    p, y, amounts = _synthetic(30)
    c_app, c_rev, c_blk = realized_cost_components(y, COSTS, amounts)
    for action, expected in (
        ("approve", c_app),
        ("review", c_rev),
        ("block", c_blk),
    ):
        actual = realized_cost(
            np.full(len(y), action, dtype=object), y, COSTS, amounts=amounts
        )
        assert np.allclose(actual, expected)


def test_best_single_threshold_matches_bruteforce():
    p, y, amounts = _synthetic(80)
    t, cost = best_single_threshold(p, y, COSTS, amounts, n_grid=10_000)

    best = np.inf
    for candidate in np.append(np.unique(p), np.inf):
        acts = actions_single_threshold(p, candidate)
        c = realized_cost(acts, y, COSTS, amounts=amounts).mean()
        best = min(best, c)

    assert cost == pytest.approx(best, rel=1e-12, abs=1e-12)


def test_best_two_threshold_matches_bruteforce():
    p, y, amounts = _synthetic(40)
    t_lo, t_hi, cost = best_two_threshold(p, y, COSTS, amounts, n_grid=10_000)
    assert t_lo <= t_hi

    candidates = np.append(np.unique(p), [np.inf])
    best = np.inf
    for lo in np.append(np.unique(p), [-np.inf]):
        for hi in candidates:
            if hi < lo:
                continue
            acts = actions_two_threshold(p, lo, hi)
            c = realized_cost(acts, y, COSTS, amounts=amounts).mean()
            best = min(best, c)

    assert cost == pytest.approx(best, rel=1e-12, abs=1e-12)


def test_threshold_policy_beats_or_matches_approve_all():
    p, y, amounts = _synthetic(100)
    _, cost = best_single_threshold(p, y, COSTS, amounts)
    approve_all = realized_cost(
        np.full(len(y), "approve", dtype=object), y, COSTS, amounts=amounts
    ).mean()
    assert cost <= approve_all + 1e-12


def test_amount_blind_ignores_amount_but_scaled_does_not():
    p = np.array([0.02, 0.02, 0.02])
    amounts = np.array([10.0, 100.0, 10_000.0])

    blind = amount_blind_actions(p, COSTS)
    assert len(set(blind)) == 1

    from src.policy.decide import choose_actions

    scaled, _, _ = choose_actions(p, COSTS, amounts)
    assert scaled[0] == "approve"
    assert scaled[2] in ("review", "block")


def test_no_review_actions_never_reviews():
    p = np.linspace(0, 1, 50)
    amounts = np.full(50, 500.0)
    acts = no_review_actions(p, COSTS, amounts)
    assert set(acts) <= {"approve", "block"}
