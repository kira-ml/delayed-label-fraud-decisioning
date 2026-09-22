"""End-to-end: all pipeline artifacts exist and match the documented schema."""
from pathlib import Path
import pandas as pd
import pytest

SUPPLEMENTARY_ARTIFACTS = [
    "data/interim/transactions.parquet",
    "data/interim/labeled.parquet",
    "data/processed/train.parquet",
    "data/processed/val.parquet",
    "data/processed/test.parquet",
    "data/processed/scored_test.parquet",
    "data/processed/action_log.parquet",
    "reports/mvp_backtest.md",
]

PRIMARY_ARTIFACTS = [
    "data/processed/primary_train.parquet",
    "data/processed/primary_test.parquet",
    "models/best_model.pkl",
    "models/preprocessing.pkl",
    "reports/model_comparison.md",
]


@pytest.mark.parametrize("path", SUPPLEMENTARY_ARTIFACTS)
def test_supplementary_artifact_exists(path):
    assert Path(path).exists(), f"missing supplementary artifact: {path}"


@pytest.mark.parametrize("path", PRIMARY_ARTIFACTS)
def test_primary_artifact_exists(path):
    assert Path(path).exists(), f"missing primary artifact: {path}"


@pytest.mark.parametrize("path", SUPPLEMENTARY_ARTIFACTS)
def test_supplementary_artifact_exists(path):
    assert Path(path).exists(), f"missing supplementary artifact: {path}"


@pytest.mark.parametrize("path", PRIMARY_ARTIFACTS)
def test_primary_artifact_exists(path):
    assert Path(path).exists(), f"missing primary artifact: {path}"


def test_action_log_schema():
    log = pd.read_parquet("data/processed/action_log.parquet")
    required = {
        "transaction_id", "month", "p_fraud", "action",
        "expected_cost_approve", "expected_cost_review", "expected_cost_block",
        "chosen_expected_cost", "reason",
    }
    missing = required - set(log.columns)
    assert not missing, f"action log missing columns: {missing}"


def test_action_log_actions_are_valid():
    log = pd.read_parquet("data/processed/action_log.parquet")
    assert set(log["action"].unique()) <= {"approve", "review", "block"}


def test_action_log_chosen_cost_is_min():
    """chosen_expected_cost must equal min of the three option costs."""
    log = pd.read_parquet("data/processed/action_log.parquet")
    computed = log[["expected_cost_approve",
                    "expected_cost_review",
                    "expected_cost_block"]].min(axis=1)
    diff = (log["chosen_expected_cost"] - computed).abs().max()
    assert diff < 1e-9, f"argmin violation, max diff = {diff}"