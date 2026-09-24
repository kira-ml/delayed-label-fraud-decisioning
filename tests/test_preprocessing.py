"""Preprocessing pipeline tests: fit on train only, transform twice = same output."""
import numpy as np
import pandas as pd
import pytest

from src.models.preprocess import (
    build_preprocessor, get_feature_columns, get_numeric_categorical,
)


@pytest.fixture(scope="module")
def train_df():
    return pd.read_parquet("data/processed/train.parquet").head(50_000)


@pytest.fixture(scope="module")
def test_df():
    return pd.read_parquet("data/processed/test.parquet").head(5_000)


@pytest.mark.parametrize("algorithm", ["logistic_regression", "random_forest", "lightgbm"])
def test_preprocessor_fits_and_transforms(algorithm, train_df):
    features = get_feature_columns(train_df)
    num, cat = get_numeric_categorical(train_df)
    pre = build_preprocessor(algorithm, num, cat)
    X = pre.fit_transform(train_df[features])
    assert X is not None
    n_rows = X.shape[0] if hasattr(X, "shape") else len(X)
    assert n_rows == len(train_df)


@pytest.mark.parametrize("algorithm", ["logistic_regression", "random_forest", "lightgbm"])
def test_transform_is_deterministic(algorithm, train_df, test_df):
    """Same input → same output. No hidden randomness."""
    features = get_feature_columns(train_df)
    num, cat = get_numeric_categorical(train_df)
    pre = build_preprocessor(algorithm, num, cat)
    pre.fit(train_df[features])

    X1 = pre.transform(test_df[features])
    X2 = pre.transform(test_df[features])

    if hasattr(X1, "toarray"):
        X1, X2 = X1.toarray(), X2.toarray()
    np.testing.assert_array_equal(X1, X2)


@pytest.mark.parametrize("algorithm", ["logistic_regression", "random_forest", "lightgbm"])
def test_unseen_categories_dont_crash(algorithm, train_df):
    """Fit on train, transform a row with a category not seen during fit."""
    features = get_feature_columns(train_df)
    num, cat = get_numeric_categorical(train_df)
    pre = build_preprocessor(algorithm, num, cat)
    pre.fit(train_df[features])

    row = train_df.iloc[[0]][features].copy()
    for c in cat:
        row[c] = "__UNSEEN_CATEGORY__"
    # Should not raise; encoder handles unknown values
    pre.transform(row)