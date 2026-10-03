"""Unit tests for src/monitoring/drift_detector.py.

See docs/v2/protocols/monitoring.md §6.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.monitoring.drift_detector import detect_drift


def test_psi_identical_distributions():
    rng = np.random.default_rng(42)
    x = rng.normal(0, 1, size=5000)
    ref = pd.DataFrame({"f_num": x, "payment_type": ["A"] * 5000})
    cmp = pd.DataFrame({"f_num": x.copy(), "payment_type": ["A"] * 5000})
    rows = detect_drift(ref, cmp, ["f_num", "payment_type"], top5=set())
    by = {r["feature"]: r for r in rows}
    assert by["f_num"]["psi"] < 0.01
    assert by["payment_type"]["psi"] < 0.01
    assert by["f_num"]["classification"] == "none"
    assert by["payment_type"]["classification"] == "none"


def test_psi_shifted_normal_is_flagged():
    rng = np.random.default_rng(42)
    ref = pd.DataFrame({
        "f_num": rng.normal(0, 1, size=5000),
        "payment_type": ["A"] * 5000,
    })
    cmp = pd.DataFrame({
        "f_num": rng.normal(1, 1, size=5000),   # 1-sigma shift
        "payment_type": ["A"] * 5000,
    })
    rows = detect_drift(ref, cmp, ["f_num", "payment_type"], top5=set())
    by = {r["feature"]: r for r in rows}
    assert by["f_num"]["psi"] > 0.1
    assert by["f_num"]["classification"] in ("moderate", "significant")


def test_psi_unchanged_categorical_is_zero():
    ref = pd.DataFrame({
        "f_num": np.zeros(1000),
        "payment_type": ["A", "B", "C", "D"] * 250,
    })
    cmp = ref.copy()
    rows = detect_drift(ref, cmp, ["f_num", "payment_type"], top5=set())
    by = {r["feature"]: r for r in rows}
    assert by["payment_type"]["psi"] < 0.01


def test_top_importance_tagging():
    ref = pd.DataFrame({
        "f_num": np.zeros(1000),
        "payment_type": ["A"] * 1000,
    })
    cmp = ref.copy()
    rows = detect_drift(ref, cmp, ["f_num", "payment_type"], top5={"f_num"})
    by = {r["feature"]: r for r in rows}
    assert by["f_num"]["top_importance"] is True
    assert by["payment_type"]["top_importance"] is False


def test_ks_reported_for_continuous_only():
    ref = pd.DataFrame({
        "f_num": np.zeros(500),
        "payment_type": ["A"] * 500,
    })
    cmp = ref.copy()
    rows = detect_drift(ref, cmp, ["f_num", "payment_type"], top5=set())
    by = {r["feature"]: r for r in rows}
    assert by["f_num"]["ks_statistic"] is not None
    assert by["f_num"]["ks_pvalue"] is not None
    assert by["payment_type"]["ks_statistic"] is None
    assert by["payment_type"]["ks_pvalue"] is None