"""Drift detector — PSI-based monitoring.

Observes Population Stability Index per feature between a reference
window and a comparison window. Reports drift classification. Does not
trigger any automated action.

See docs/v2/protocols/monitoring.md.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from scipy.stats import ks_2samp

from src.common import CATEGORICAL_COLS, DATA_INTERIM, MODELS
from src.v2.drift import (
    _classify,
    _features,
    _psi_categorical,
    _psi_continuous,
)

IN_PATH = DATA_INTERIM / "transactions.parquet"
IMP_PATH = MODELS / "feature_importances.json"
OUT_PATH = Path("reports/v2/drift_monitor.json")

SIGNIFICANT = "significant"
MODERATE = "moderate"


def _top5_features() -> set[str]:
    """Return the top-5 feature names by LR importance, or empty set."""
    if not IMP_PATH.exists():
        return set()
    imp = json.loads(IMP_PATH.read_text(encoding="utf-8"))
    pairs = sorted(
        zip(imp["features"], imp["importances"]),
        key=lambda kv: kv[1], reverse=True,
    )
    return {f for f, _ in pairs[:5]}


def detect_drift(ref_df, cmp_df, features, top5=None):
    """Compute PSI per feature between two windows.

    Returns a list of per-feature dicts, one per feature.
    """
    top5 = top5 or set()
    rows = []
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

        rows.append({
            "feature": feat,
            "psi": float(psi),
            "classification": _classify(psi),
            "ks_statistic": ks_stat,
            "ks_pvalue": ks_pvalue,
            "top_importance": feat in top5,
        })
    return rows


def _summarize(all_rows: list[dict]) -> dict:
    if not all_rows:
        return {
            "max_psi": 0.0,
            "max_psi_feature": None,
            "max_psi_pair": None,
            "n_significant": 0,
            "n_moderate": 0,
            "n_none": 0,
            "n_top5_drifted": 0,
            "alert_level": "none",
        }

    top = max(all_rows, key=lambda r: r["psi"])
    n_sig = sum(1 for r in all_rows if r["classification"] == SIGNIFICANT)
    n_mod = sum(1 for r in all_rows if r["classification"] == MODERATE)
    n_none = sum(1 for r in all_rows if r["classification"] == "none")
    n_top5 = sum(
        1 for r in all_rows
        if r["top_importance"] and r["classification"] != "none"
    )
    if n_sig:
        alert = SIGNIFICANT
    elif n_mod:
        alert = MODERATE
    else:
        alert = "none"

    return {
        "max_psi": top["psi"],
        "max_psi_feature": top["feature"],
        "max_psi_pair": top.get("_pair"),
        "n_significant": n_sig,
        "n_moderate": n_mod,
        "n_none": n_none,
        "n_top5_drifted": n_top5,
        "alert_level": alert,
    }


def _print_pair(ref_label, cmp_label, rows) -> None:
    print(f"\n[drift] ref={ref_label}  cmp={cmp_label}")
    drifted = [r for r in rows if r["classification"] != "none"]
    if not drifted:
        print("  no drift (all features PSI < 0.1)")
        return
    for r in sorted(drifted, key=lambda x: -x["psi"]):
        tag = "  [top-5]" if r["top_importance"] else ""
        print(f"  {r['feature']:<35} PSI={r['psi']:>8.4f}  "
              f"{r['classification']}{tag}")


def main() -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(IN_PATH)
    features = _features(df)
    months = sorted(df["month"].unique().tolist())
    top5 = _top5_features()

    print(f"[drift] Loaded {len(df):,} rows, {len(features)} features, "
          f"months {months}")
    print(f"[drift] Top-5 importance features: {sorted(top5)}")
    print("[drift] Pairing adjacent months (matching H4's diagnostic)")

    pairs_payload = []
    all_rows = []
    for i in range(len(months) - 1):
        m_ref, m_cmp = months[i], months[i + 1]
        ref_df = df[df["month"] == m_ref]
        cmp_df = df[df["month"] == m_cmp]
        rows = detect_drift(ref_df, cmp_df, features, top5=top5)
        for r in rows:
            r["_pair"] = [int(m_ref), int(m_cmp)]
        _print_pair(m_ref, m_cmp, rows)
        pairs_payload.append({
            "ref_window": int(m_ref),
            "cmp_window": int(m_cmp),
            "n_ref": int(len(ref_df)),
            "n_cmp": int(len(cmp_df)),
            "features": [
                {k: v for k, v in r.items() if k != "_pair"}
                for r in rows
            ],
        })
        all_rows.extend(rows)

    summary = _summarize(all_rows)

    print()
    print(f"[drift] Max PSI = {summary['max_psi']:.4f} "
          f"({summary['max_psi_feature']}, "
          f"months {summary['max_psi_pair']})")
    print(f"[drift] Alert level: {summary['alert_level']}")
    print(f"[drift] Significant features: {summary['n_significant']}, "
          f"moderate: {summary['n_moderate']}, "
          f"top-5 drifted: {summary['n_top5_drifted']}")

    out = {
        "reference_windows": "adjacent months",
        "features": features,
        "pairs": pairs_payload,
        "summary": summary,
    }
    OUT_PATH.write_text(
        json.dumps(out, indent=2, default=str), encoding="utf-8",
    )
    print(f"[drift] Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()