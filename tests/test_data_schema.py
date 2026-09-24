"""Schema and integrity tests for pipeline data artifacts."""
import pandas as pd
import pytest
from pathlib import Path

from src.common import FEATURE_EXCLUDE, CATEGORICAL_COLS


@pytest.fixture(scope="module")
def df():
    return pd.read_parquet("data/interim/transactions.parquet")


def test_transactions_row_count(df):
    assert len(df) == 1_000_000


def test_transactions_columns_present(df):
    required = {"transaction_id", "month", "fraud_bool", "amount_proxy"}
    missing = required - set(df.columns)
    assert not missing, f"missing columns: {missing}"


def test_transaction_id_is_unique(df):
    assert df["transaction_id"].is_unique


def test_fraud_bool_is_binary(df):
    assert set(df["fraud_bool"].unique()) <= {0, 1}


def test_month_range(df):
    assert df["month"].min() == 0
    assert df["month"].max() == 7


def test_no_missing_values(df):
    assert df.isna().sum().sum() == 0


def test_categorical_columns_present(df):
    for c in CATEGORICAL_COLS:
        assert c in df.columns, f"missing categorical {c}"


@pytest.fixture(scope="module")
def test_df():
    return pd.read_parquet("data/processed/test.parquet")


def test_test_features_exclude_leak_columns(test_df):
    """Model features must not include any FEATURE_EXCLUDE column."""
    from src.models.preprocess import get_feature_columns
    features = set(get_feature_columns(test_df))
    leaked = features & set(FEATURE_EXCLUDE)
    assert not leaked, f"leak columns present in features: {leaked}"


def test_test_fraud_rate(test_df):
    """Test-split fraud rate ~1.26% (docs/data_card.md §5.2)."""
    r = test_df["fraud_bool"].mean()
    assert 0.010 < r < 0.016, f"unexpected test fraud rate: {r}"