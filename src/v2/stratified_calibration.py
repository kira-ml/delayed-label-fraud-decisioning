"""H6 — Causal validity diagnostic (stratified calibration).

Tests whether V1's direct cost estimate is materially confounded by the
policy's deterministic selection on the classifier's inputs. The
diagnostic is a necessary condition: if `p_fraud` is calibrated within
each action stratum, the direct estimate is approximately unbiased under
conditional exchangeability given the model's inputs.

Method: split the test window by action (approve / review / block) and
compute ECE within each stratum. Compare per-stratum ECE to the
aggregate ECE.

Reads:  data/processed/scored_test.parquet
        data/processed/action_log.parquet
Writes: reports/v2/intermediate/h6_stratified_calibration.json

Run: python -m src.v2.stratified_calibration

See docs/v2/falsification_plan.md §3 H6 and
    docs/v2/evaluation_framework.md §5.6 and §6.6.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.common import DATA_PROCESSED
from src.evaluation.calibration import ece as quantile_ece

SCORED = DATA_PROCESSED / "scored_test.parquet"
ACTIONS = DATA_PROCESSED / "action_log.parquet"
OUT_DIR = Path("reports/v2/intermediate")
OUT_PATH = OUT_DIR / "h6_stratified_calibration.json"

# Pre-registered threshold from falsification_plan.md §3 H6.
STRATUM_ECE_THRESHOLD = 0.05

# Sample-size guard from evaluation_framework.md §5.6:
# if a stratum has fewer than this many rows with p_fraud > 0.01, fall
# back to equal-width bins instead of quantile bins.
MIN_ROWS_FOR_QUANTILE = 100

N_BINS = 10
P_LOW_THRESHOLD = 0.01


def _ece_equal_width(p: np.ndarray, y: np.ndarray,
                     n_bins: int = N_BINS) -> tuple[float, pd.DataFrame]:
    """ECE with equal-width bins over [0, 1]. Fallback for small strata."""
    p = np.asarray(p, dtype=float)
    y = np.asarray(y, dtype=float)

    edges = np.linspace(0.0, 1.0, n_bins + 1)
    edges[0] = -np.inf
    edges[-1] = np.inf

    rows = []
    weighted_gap = 0.0
    for i in range(len(edges) - 1):
        lo, hi = edges[i], edges[i + 1]
        if i == 0:
            mask = (p >= lo) & (p <= hi)
        else:
            mask = (p > lo) & (p <= hi)
        n = int(mask.sum())
        if n == 0:
            continue
        mean_p = float(p[mask].mean())
        mean_y = float(y[mask].mean())
        gap = abs(mean_p - mean_y)
        weight = n / len(p)
        weighted_gap += gap * weight
        rows.append({
            "bin": i,
            "n": n,
            "share": weight,
            "mean_p": mean_p,
            "mean_y": mean_y,
            "gap": gap,
        })
    return float(weighted_gap), pd.DataFrame(rows)


def _ece(p: np.ndarray, y: np.ndarray, small_stratum: bool):
    """Pick binning strategy per evaluation_framework.md §5.6."""
    if small_stratum:
        return _ece_equal_width(p, y, N_BINS), "equal_width"
    return quantile_ece(p, y, N_BINS), "quantile"


def _brier(p: np.ndarray, y: np.ndarray) -> float:
    return float(np.mean((np.asarray(p, dtype=float)
                          - np.asarray(y, dtype=float)) ** 2))


def _stratum(p: np.ndarray, y: np.ndarray, name: str) -> dict:
    n = len(p)
    if n == 0:
        return {
            "name": name,
            "n": 0,
            "n_p_gt_001": 0,
            "binning": None,
            "ece": None,
            "brier": None,
            "base_rate": None,
            "p_mean": None,
            "p_min": None,
            "p_max": None,
            "reliability_table": [],
            "small_stratum_fallback": None,
        }

    p = np.asarray(p, dtype=float)
    y = np.asarray(y, dtype=float)
    n_high = int((p > P_LOW_THRESHOLD).sum())
    small = n_high < MIN_ROWS_FOR_QUANTILE

    (ece_value, table), binning = _ece(p, y, small)
    return {
        "name": name,
        "n": int(n),
        "n_p_gt_001": n_high,
        "binning": binning,
        "small_stratum_fallback": bool(small),
        "ece": float(ece_value),
        "brier": _brier(p, y),
        "base_rate": float(y.mean()),
        "p_mean": float(p.mean()),
        "p_min": float(p.min()),
        "p_max": float(p.max()),
        "reliability_table": table.to_dict(orient="records"),
    }


def _print_stratum(s: dict) -> None:
    if s["n"] == 0:
        print(f"  {s['name']:<10} empty stratum")
        return
    fallback = " (equal-width fallback)" if s["small_stratum_fallback"] else ""
    print(f"  {s['name']:<10} n={s['n']:>8,}  "
          f"base_rate={s['base_rate']:.4%}  "
          f"p_mean={s['p_mean']:.6f}  "
          f"p_range=[{s['p_min']:.6f}, {s['p_max']:.6f}]")
    print(f"             binning={s['binning']}{fallback}  "
          f"ECE={s['ece']:.4f}  Brier={s['brier']:.6f}")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    scored = pd.read_parquet(SCORED)[
        ["transaction_id", "p_fraud", "fraud_bool"]
    ]
    log = pd.read_parquet(ACTIONS)[["transaction_id", "action"]]
    df = scored.merge(log, on="transaction_id", how="inner")
    assert len(df) == len(log), (
        f"merge lost rows: scored={len(scored)}, log={len(log)}, "
        f"merged={len(df)}"
    )

    p_all = df["p_fraud"].to_numpy()
    y_all = df["fraud_bool"].to_numpy()

    print(f"[h6] Loaded {len(df):,} test-window rows")
    print(f"[h6] Kill criterion: any action stratum has "
          f"ECE >= {STRATUM_ECE_THRESHOLD}")
    print(f"[h6] Sample-size fallback: stratum with < "
          f"{MIN_ROWS_FOR_QUANTILE} rows with p > {P_LOW_THRESHOLD} "
          f"uses equal-width bins")
    print()

    # Aggregate reference (should match V1's 0.0033 on the test window).
    agg_ece, agg_table = quantile_ece(p_all, y_all, N_BINS)
    agg_brier = _brier(p_all, y_all)

    print(f"[h6] Aggregate: n={len(df):,}  ECE={agg_ece:.4f}  "
          f"Brier={agg_brier:.6f}")
    print()

    strata = []
    for action in ("approve", "review", "block"):
        sub = df[df["action"] == action]
        s = _stratum(
            sub["p_fraud"].to_numpy(),
            sub["fraud_bool"].to_numpy(),
            action,
        )
        strata.append(s)

    print("[h6] Per-stratum calibration:")
    for s in strata:
        _print_stratum(s)
    print()

    # Kill criterion: any stratum ECE >= 0.05
    valid_eces = [s["ece"] for s in strata if s["ece"] is not None]
    max_ece = max(valid_eces) if valid_eces else None
    max_ece_stratum = None
    if max_ece is not None:
        for s in strata:
            if s["ece"] is not None and s["ece"] == max_ece:
                max_ece_stratum = s["name"]
                break

    if max_ece is None:
        verdict = "blocked"
    elif max_ece >= STRATUM_ECE_THRESHOLD:
        verdict = "killed"
    else:
        verdict = "survived"

    ece_ratio = (
        max_ece / agg_ece if (max_ece is not None and agg_ece > 0) else None
    )

    results = {
        "hypothesis": "H6",
        "kill_criterion": (
            f"any action stratum has ECE >= {STRATUM_ECE_THRESHOLD}"
        ),
        "stratum_ece_threshold": STRATUM_ECE_THRESHOLD,
        "min_rows_for_quantile": MIN_ROWS_FOR_QUANTILE,
        "p_low_threshold": P_LOW_THRESHOLD,
        "n_bins": N_BINS,
        "test_window_rows": int(len(df)),
        "aggregate_ece": float(agg_ece),
        "aggregate_brier": float(agg_brier),
        "aggregate_reliability_table": agg_table.to_dict(orient="records"),
        "strata": strata,
        "max_stratum_ece": float(max_ece) if max_ece is not None else None,
        "max_stratum_ece_name": max_ece_stratum,
        "ece_ratio_max_over_aggregate": (
            float(ece_ratio) if ece_ratio is not None else None
        ),
        "verdict": verdict,
    }

    print(f"[h6] Max stratum ECE: {max_ece:.4f} "
          f"({max_ece_stratum})" if max_ece is not None else
          "[h6] Max stratum ECE: undefined")
    if ece_ratio is not None:
        print(f"[h6] Ratio max_stratum / aggregate: {ece_ratio:.2f}x")
    print(f"[h6] Verdict: {verdict}")

    OUT_PATH.write_text(
        json.dumps(results, indent=2, default=str),
        encoding="utf-8",
    )
    print(f"[h6] Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()