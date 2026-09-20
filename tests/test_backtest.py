import numpy as np
from src.evaluation.backtest import realized_cost

COSTS = {
    "fraud_loss": 1.0,
    "false_positive_cost": 0.1,
    "review_cost": 0.02,
    "residual_fraud_loss": 0.3,
}


def test_realized_cost_matrix():
    """Six (action, label) combinations must match the cost table exactly."""
    actions = np.array(["approve", "review", "block", "approve", "review", "block"])
    y = np.array([1, 1, 1, 0, 0, 0])
    c = realized_cost(actions, y, COSTS)
    expected = np.array([
        1.0,          # fraud + approve -> fraud_loss
        0.02 + 0.3,   # fraud + review  -> review_cost + residual_fraud_loss
        0.0,          # fraud + block   -> 0
        0.0,          # legit + approve -> 0
        0.02,         # legit + review  -> review_cost
        0.1,          # legit + block   -> false_positive_cost
    ])
    assert np.allclose(c, expected)


def test_realized_cost_zero_for_approve_on_legit():
    c = realized_cost(["approve"], [0], COSTS)
    assert c[0] == 0.0


def test_expected_and_realized_agree_at_extremes():
    """
    Cross-check: when p is 0 or 1, expected cost should equal realized cost
    for the argmin-chosen action on the corresponding true label.
    """
    from src.policy.decide import choose_actions

    # p = 1.0, truth = fraud -> chosen should be block (0 cost)
    actions, chosen, _ = choose_actions([1.0], COSTS)
    realized = realized_cost(actions, [1], COSTS)
    assert actions[0] == "block"
    assert realized[0] == chosen[0] == 0.0

    # p = 0.0, truth = legit -> chosen should be approve (0 cost)
    actions, chosen, _ = choose_actions([0.0], COSTS)
    realized = realized_cost(actions, [0], COSTS)
    assert actions[0] == "approve"
    assert realized[0] == chosen[0] == 0.0