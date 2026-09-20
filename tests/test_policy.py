import numpy as np
import pytest
from src.policy.decide import choose_actions

DEFAULT_COSTS = {
    "fraud_loss": 1.0,
    "false_positive_cost": 0.1,
    "review_cost": 0.02,
    "residual_fraud_loss": 0.3,
}


def test_approve_when_p_is_clearly_low():
    actions, _, _ = choose_actions([0.001], DEFAULT_COSTS)
    assert actions[0] == "approve"


def test_review_when_p_is_between_thresholds():
    actions, _, _ = choose_actions([0.05], DEFAULT_COSTS)
    assert actions[0] == "review"


def test_block_when_p_is_clearly_high():
    actions, _, _ = choose_actions([0.8], DEFAULT_COSTS)
    assert actions[0] == "block"


def test_all_three_actions_appear_over_range():
    p = np.linspace(0.0, 1.0, 101)
    actions, _, _ = choose_actions(p, DEFAULT_COSTS)
    assert set(actions) == {"approve", "review", "block"}


def test_edge_case_a_review_band_collapses_when_residual_ge_fraud():
    # fraud_loss <= residual_fraud_loss -> review never wins
    costs = dict(DEFAULT_COSTS, fraud_loss=0.3, residual_fraud_loss=0.3)
    p = np.linspace(0.0, 1.0, 101)
    actions, _, _ = choose_actions(p, costs)
    assert "review" not in set(actions)


def test_edge_case_b_argmin_correct_when_thresholds_cross():
    # force p_review >= p_block: large review_cost, tiny false_positive_cost
    costs = {
        "fraud_loss": 1.0,
        "false_positive_cost": 0.05,
        "review_cost": 0.10,
        "residual_fraud_loss": 0.3,
    }
    # p_review = 0.10 / 0.7 = 0.143
    # p_block  = (0.05 - 0.10) / 0.35 = -0.143
    # Threshold rule is degenerate; argmin must still produce valid actions.
    p = np.linspace(0.0, 1.0, 101)
    actions, chosen, (c_app, c_rev, c_blk) = choose_actions(p, costs)
    # Every chosen cost equals the min of the three
    assert np.allclose(chosen, np.minimum(np.minimum(c_app, c_rev), c_blk))


def test_edge_case_c_chosen_cost_is_always_minimum():
    for p_val in [0.0, 0.0286, 0.1, 0.2, 0.5, 1.0]:
        actions, chosen, (c_app, c_rev, c_blk) = choose_actions([p_val], DEFAULT_COSTS)
        assert chosen[0] == min(c_app[0], c_rev[0], c_blk[0])