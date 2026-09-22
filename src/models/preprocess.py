"""Algorithm-specific preprocessing for the primary 3-algorithm comparison.

See docs/evaluation_protocol.md §4.3:
  - Logistic Regression: one-hot + StandardScaler
  - Random Forest:       ordinal encoding, no scaling
  - LightGBM:            native categorical (pandas category dtype), no scaling
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import (
    OneHotEncoder, OrdinalEncoder, StandardScaler,
)

from src.common import FEATURE_EXCLUDE, CATEGORICAL_COLS


def get_feature_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c not in FEATURE_EXCLUDE]


def get_numeric_categorical(df: pd.DataFrame) -> tuple[list[str], list[str]]:
    feats = get_feature_columns(df)
    cat = [c for c in CATEGORICAL_COLS if c in feats]
    num = [c for c in feats if c not in cat]
    return num, cat


class LGBMPreprocessor(BaseEstimator, TransformerMixin):
    """Convert categorical columns to pandas category dtype.

    Stores category mappings so validation/test use the same categories
    as training (avoids the classic 'category mismatch' LightGBM bug).
    """

    def __init__(self, categorical_cols: list[str]):
        self.categorical_cols = categorical_cols
        self.categories_: dict[str, pd.Index] = {}

    def fit(self, X: pd.DataFrame, y=None) -> "LGBMPreprocessor":
        for c in self.categorical_cols:
            if c in X.columns:
                self.categories_[c] = X[c].astype("category").cat.categories
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        X = X.copy()
        for c in self.categorical_cols:
            if c in X.columns and c in self.categories_:
                X[c] = pd.Categorical(X[c], categories=self.categories_[c])
        return X

    def get_feature_names_out(self, input_features=None):
        return np.array(input_features if input_features is not None else [])


def build_preprocessor(algorithm: str,
                       numeric_cols: list[str],
                       categorical_cols: list[str]):
    """Return an *unfitted* preprocessor for the given algorithm."""
    if algorithm == "logistic_regression":
        return ColumnTransformer([
            ("num", StandardScaler(), numeric_cols),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False),
             categorical_cols),
        ])
    if algorithm == "random_forest":
        return ColumnTransformer([
            ("num", "passthrough", numeric_cols),
            ("cat", OrdinalEncoder(handle_unknown="use_encoded_value",
                                   unknown_value=-1),
             categorical_cols),
        ])
    if algorithm == "lightgbm":
        return LGBMPreprocessor(categorical_cols)
    raise ValueError(f"Unknown algorithm: {algorithm}")