"""Reproducibility: same seed produces same predictions."""
import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import RandomForestClassifier

from src.common import SEED
from src.models.preprocess import get_feature_columns


def test_random_forest_deterministic():
    df = pd.read_parquet("data/processed/primary_train.parquet").head(20_000)
    X = df[get_feature_columns(df)].select_dtypes(include=np.number)
    y = df["fraud_bool"]

    m1 = RandomForestClassifier(n_estimators=50, random_state=SEED, n_jobs=1)
    m1.fit(X, y)
    p1 = m1.predict_proba(X)[:, 1]

    m2 = RandomForestClassifier(n_estimators=50, random_state=SEED, n_jobs=1)
    m2.fit(X, y)
    p2 = m2.predict_proba(X)[:, 1]

    np.testing.assert_array_equal(p1, p2)


def test_lightgbm_deterministic():
    import lightgbm as lgb
    df = pd.read_parquet("data/processed/primary_train.parquet").head(20_000)
    X = df[get_feature_columns(df)].select_dtypes(include=np.number)
    y = df["fraud_bool"]

    m1 = lgb.LGBMClassifier(n_estimators=50, random_state=SEED, verbose=-1)
    m1.fit(X, y)
    p1 = m1.predict_proba(X)[:, 1]

    m2 = lgb.LGBMClassifier(n_estimators=50, random_state=SEED, verbose=-1)
    m2.fit(X, y)
    p2 = m2.predict_proba(X)[:, 1]

    np.testing.assert_array_equal(p1, p2)