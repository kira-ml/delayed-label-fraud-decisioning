"""Streamlit app input validation tests (pure functions, no UI)."""
import pandas as pd
import pytest

from app.streamlit_app import validate_input
from src.models.preprocess import get_feature_columns


@pytest.fixture(scope="module")
def sample_row():
    df = pd.read_parquet("data/processed/primary_test.parquet").head(1)
    return df


@pytest.fixture(scope="module")
def required_cols(sample_row):
    return get_feature_columns(sample_row)


def test_valid_input_passes(sample_row, required_cols):
    assert validate_input(sample_row, required_cols) == []


def test_missing_column_fails(sample_row, required_cols):
    bad = sample_row.drop(columns=[required_cols[0]])
    errors = validate_input(bad, required_cols)
    assert any("Missing required columns" in e for e in errors)


def test_empty_input_fails(required_cols):
    empty = pd.DataFrame(columns=required_cols)
    errors = validate_input(empty, required_cols)
    assert any("no rows" in e.lower() for e in errors)


def test_missing_categorical_value_fails(sample_row, required_cols):
    bad = sample_row.copy()
    for c in ["payment_type", "employment_status"]:
        if c in bad.columns:
            bad.loc[0, c] = None
            break
    errors = validate_input(bad, required_cols)
    assert any("missing values" in e for e in errors)


def test_boundary_extreme_numeric_passes(sample_row, required_cols):
    """Very low numerics must not crash validation."""
    extreme = sample_row.copy()
    for c in extreme.columns:
        if extreme[c].dtype.kind in "if" and c != "customer_age":
            extreme[c] = 0.0  # minimum plausible
    errors = validate_input(extreme, required_cols)
    assert errors == []


def test_boundary_max_numeric_passes(sample_row, required_cols):
    """Large numerics must not crash validation.

    customer_age has a legitimate upper bound (120) enforced by validate_input,
    so it is excluded from the extreme-value sweep.
    """
    extreme = sample_row.copy()
    for c in extreme.columns:
        if extreme[c].dtype.kind in "if" and c != "customer_age":
            extreme[c] = 1e9
    errors = validate_input(extreme, required_cols)
    assert errors == []