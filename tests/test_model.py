"""Saved model behavior tests."""
import numpy as np
import pandas as pd
import pytest
import joblib

from src.models.preprocess import get_feature_columns


@pytest.fixture(scope="module")
def model_and_pre():
    model = joblib.load("models/best_model.pkl")
    pre = joblib.load("models/preprocessing.pkl")
    return model, pre


@pytest.fixture(scope="module")
def test_df():
    return pd.read_parquet("data/processed/test.parquet").head(5_000)


def test_saved_model_is_loadable(model_and_pre):
    model, _ = model_and_pre
    assert hasattr(model, "predict_proba")


def test_predict_shape(model_and_pre, test_df):
    model, pre = model_and_pre
    X = pre.transform(test_df[get_feature_columns(test_df)])
    if hasattr(X, "toarray"):
        X = X.toarray()
    preds = model.predict(X)
    assert len(preds) == len(test_df)


def test_predictions_are_binary(model_and_pre, test_df):
    model, pre = model_and_pre
    X = pre.transform(test_df[get_feature_columns(test_df)])
    if hasattr(X, "toarray"):
        X = X.toarray()
    preds = model.predict(X)
    assert set(np.unique(preds)) <= {0, 1}


def test_probabilities_in_range(model_and_pre, test_df):
    model, pre = model_and_pre
    X = pre.transform(test_df[get_feature_columns(test_df)])
    if hasattr(X, "toarray"):
        X = X.toarray()
    p = model.predict_proba(X)[:, 1]
    assert p.min() >= 0.0
    assert p.max() <= 1.0


def test_calibration_mean_probability(model_and_pre, test_df):
    """Calibrated model: mean p_fraud within 2x the observed base rate."""
    model, pre = model_and_pre
    X = pre.transform(test_df[get_feature_columns(test_df)])
    if hasattr(X, "toarray"):
        X = X.toarray()
    p = model.predict_proba(X)[:, 1]
    true_rate = test_df["fraud_bool"].mean()
    # Allow 2x slack for a 5k sample
    assert abs(p.mean() - true_rate) < 2 * true_rate, \
        f"model appears uncalibrated: mean p={p.mean():.4f}, true={true_rate:.4f}"