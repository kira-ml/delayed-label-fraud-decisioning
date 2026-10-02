"""H4 — Feature drift diagnostic.

Tests whether feature distributions drift month-over-month in the BAF
dataset. If PSI >= 0.1 for any feature between adjacent months, H4
survives and drift detection becomes in scope. Otherwise H4 is killed
and drift detection is dropped from V2.

Reads:  data/interim/transactions.parquet
Writes: reports/v2/intermediate/h4_drift.json

Run: python -m src.v2.drift

See docs/v2/falsification_plan.md §3 H4 and
    docs/v2/evaluation_framework.md §5.4 and §6.4.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import ks_2samp

from src.common import DATA_INTERIM, CATEGORICAL_COLS, FEATURE_EXCLUDE

IN_PATH = DATA_INTERIM / "transactions.parquet"
OUT_DIR = Path("reports/v2/intermediate")
OUT_PATH = OUT_DIR / "h4_drift.json"

# Pre-registered threshold from falsification_plan.md §3 H4.
PSI_DRIFT_THRESHOLD = 0.10      # kill criterion: max PSI < 0.10
PSI_MODERATE_THRESHOLD = 0.25   # classification only; not a kill criterion

N_BINS_CONTINUOUS = 10          # decile bins per evaluation_framework.md §5.4
EPS = 1e-6                      # zero-frequency substitution


def _features(df: pd.DataFrame) -> list[str]:
    """Classifier features, in a stable order."""
    return [c for c in df.columns if c not in FEATURE_EXCLUDE]


def _psi_continuous(ref: np.ndarray, cmp: np.ndarray,
                    n_bins: int = N_BINS_CONTINUOUS) -> float:
    """PSI between two continuous distributions.

    Bins are deciles of the reference distribution. The lowest bin is
    closed on both sides to include the minimum value.
    """
    ref = np.asarray(ref, dtype=float)
    cmp = np.asarray(cmp, dtype=float)

    # Deciles of the reference distribution; collapse duplicates.
    edges = np.quantile(ref, np.linspace(0.0, 1.0, n_bins + 1))
    edges = np.unique(edges)
    if len(edges) < 3:
        # Degenerate: fewer than 2 usable bins. PSI is undefined; return 0.
        return 0.0

    edges[0] = -np.inf
    edges[-1] = np.inf

    psi = 0.0
    for i in range(len(edges) - 1):
        lo, hi = edges[i], edges[i + 1]
        if i == 0:
            ref_mask = (ref >= lo) & (ref <= hi)
            cmp_mask = (cmp >= lo) & (cmp <= hi)
        else:
            ref_mask = (ref > lo) & (ref <= hi)
            cmp_mask = (cmp > lo) & (cmp <= hi)

        ref_pct = ref_mask.sum() / len(ref) if len(ref) else 0.0
        cmp_pct = cmp_mask.sum() / len(cmp) if len(cmp) else 0.0

        ref_pct = max(ref_pct, EPS)
        cmp_pct = max(cmp_pct, EPS)
        psi += (cmp_pct - ref_pct) * np.log(cmp_pct / ref_pct)

    return float(psi)


def _psi_categorical(ref: pd.Series, cmp: pd.Series) -> float:
    """PSI between two categorical distributions.

    Categories present in only one month get EPS for the missing side.
    """
    ref_counts = ref.value_counts(normalize=True)
    cmp_counts = cmp.value_counts(normalize=True)

    categories = ref_counts.index.union(cmp_counts.index)
    psi = 0.0
    for cat in categories:
        ref_pct = max(float(ref_counts.get(cat, 0.0)), EPS)
        cmp_pct = max(float(cmp_counts.get(cat, 0.0)), EPS)
        psi += (cmp_pct - ref_pct) * np.log(cmp_pct / ref_pct)

    return float(psi)


def _classify(psi: float) -> str:
    if psi < PSI_DRIFT_THRESHOLD:
        return "none"
    if psi < PSI_MODERATE_THRESHOLD:
        return "moderate"
    return "significant"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(IN_PATH)
    features = _features(df)
    months = sorted(df["month"].unique().tolist())

    print(f"[drift] Loaded {len(df):,} rows, {len(features)} features, "
          f"months {months}")
    print(f"[drift] Kill criterion: max PSI < {PSI_DRIFT_THRESHOLD} "
          f"across all features and adjacent pairs")
    print()

    results: dict = {
        "hypothesis": "H4",
        "kill_criterion": (
            f"max PSI < {PSI_DRIFT_THRESHOLD} across all features and "
            "all adjacent month pairs"
        ),
        "psi_drift_threshold": PSI_DRIFT_THRESHOLD,
        "psi_moderate_threshold": PSI_MODERATE_THRESHOLD,
        "months": months,
        "features": features,
        "pairs": [],
    }

    all_psi_values: list[tuple[str, tuple[int, int], float]] = []

    for i in range(len(months) - 1):
        m_ref, m_cmp = months[i], months[i + 1]
        ref_df = df[df["month"] == m_ref]
        cmp_df = df[df["month"] == m_cmp]

        pair_entry = {
            "ref_month": int(m_ref),
            "cmp_month": int(m_cmp),
            "n_ref": int(len(ref_df)),
            "n_cmp": int(len(cmp_df)),
            "features": [],
        }

        for feat in features:
            if feat in CATEGORICAL_COLS:
                psi = _psi_categorical(
                    ref_df[feat].astype(str),
                    cmp_df[feat].astype(str),
                )
                ks_stat = None
                ks_pvalue = None
            else:
                ref_vals = ref_df[feat].dropna().to_numpy()
                cmp_vals = cmp_df[feat].dropna().to_numpy()
                psi = _psi_continuous(ref_vals, cmp_vals)
                ks = ks_2samp(ref_vals, cmp_vals)
                ks_stat = float(ks.statistic)
                ks_pvalue = float(ks.pvalue)

            entry = {
                "feature": feat,
                "psi": psi,
                "classification": _classify(psi),
                "ks_statistic": ks_stat,
                "ks_pvalue": ks_pvalue,
            }
            pair_entry["features"].append(entry)
            all_psi_values.append((feat, (int(m_ref), int(m_cmp)), psi))

        results["pairs"].append(pair_entry)

        print(f"[drift] months {m_ref}->{m_cmp}: "
              f"n_ref={len(ref_df):,}, n_cmp={len(cmp_df):,}")

    # Aggregate
    if all_psi_values:
        max_feat, max_pair, max_psi = max(all_psi_values, key=lambda t: t[2])
        drifted = [
            {"feature": f, "pair": list(p), "psi": psi}
            for f, p, psi in all_psi_values
            if psi >= PSI_DRIFT_THRESHOLD
        ]
        results["max_psi"] = max_psi
        results["max_psi_feature"] = max_feat
        results["max_psi_pair"] = list(max_pair)
        results["drifted_features"] = drifted
        results["n_drifted"] = len(drifted)
        results["verdict"] = (
            "survived" if max_psi >= PSI_DRIFT_THRESHOLD else "killed"
        )
    else:
        results["max_psi"] = 0.0
        results["max_psi_feature"] = None
        results["max_psi_pair"] = None
        results["drifted_features"] = []
        results["n_drifted"] = 0
        results["verdict"] = "blocked"

    print()
    print(f"[drift] Max PSI = {results['max_psi']:.4f} "
          f"({results['max_psi_feature']}, "
          f"months {results['max_psi_pair']})")
    print(f"[drift] Features with PSI >= {PSI_DRIFT_THRESHOLD}: "
          f"{results['n_drifted']}")
    print(f"[drift] Verdict: {results['verdict']}")

    OUT_PATH.write_text(
        json.dumps(results, indent=2), encoding="utf-8"
    )
    print(f"[drift] Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()