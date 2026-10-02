"""H5 — Group disparity diagnostic.

Tests whether V1's block decisions differ materially across candidate
protected groupings. If max block-rate disparity >= 5 percentage points
in any grouping, H5 survives and a fairness constraint enters Phase B
scope. Otherwise H5 is killed and fairness constraints are dropped.

Reads:  data/processed/action_log.parquet
        data/processed/test.parquet
Writes: reports/v2/intermediate/h5_fairness.json

Run: python -m src.v2.fairness

See docs/v2/falsification_plan.md §3 H5 and
    docs/v2/evaluation_framework.md §5.5 and §6.5.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.common import DATA_PROCESSED

ACTION_LOG = DATA_PROCESSED / "action_log.parquet"
TEST = DATA_PROCESSED / "test.parquet"
OUT_DIR = Path("reports/v2/intermediate")
OUT_PATH = OUT_DIR / "h5_fairness.json"

# Pre-registered threshold from falsification_plan.md §3 H5.
DISPARITY_THRESHOLD = 0.05  # 5 percentage points

# Sample-size guard from evaluation_framework.md §5.5.
MIN_GROUP_SIZE = 500

# Pre-registered binning for customer_age from falsification_plan.md §3 H5.
AGE_BINS = [0, 25, 35, 45, 55, 65, np.inf]
AGE_LABELS = ["[0-25)", "[25-35)", "[35-45)", "[45-55)", "[55-65)", "[65+"]

# Groupings to test.
GROUPINGS = [
    {"name": "customer_age", "source": "binned"},
    {"name": "employment_status", "source": "categorical"},
    {"name": "housing_status", "source": "categorical"},
]


def _load() -> pd.DataFrame:
    """Join action_log with test for the grouping attributes and label."""
    log = pd.read_parquet(ACTION_LOG)
    test = pd.read_parquet(TEST)[
        ["transaction_id", "customer_age", "employment_status",
         "housing_status", "fraud_bool"]
    ]
    df = log.merge(test, on="transaction_id", how="left", suffixes=("", "_t"))
    assert len(df) == len(log), "join dropped rows"
    assert df["fraud_bool"].notna().all(), "join produced NaN labels"
    assert df["action"].notna().all(), "missing actions"
    return df


def _prepare_age(df: pd.DataFrame) -> pd.DataFrame:
    """Add a `customer_age_bin` column using the pre-registered bins."""
    df = df.copy()
    df["customer_age_bin"] = pd.cut(
        df["customer_age"],
        bins=AGE_BINS,
        labels=AGE_LABELS,
        right=False,        # [a, b) intervals
        include_lowest=True,
    )
    return df


def _group_stats(df: pd.DataFrame, group_col: str) -> list[dict]:
    """Per-group n, action rates, and fraud rate."""
    rows = []
    for g, sub in df.groupby(group_col, observed=True):
        n = len(sub)
        if n == 0:
            continue
        n_block = int((sub["action"] == "block").sum())
        n_review = int((sub["action"] == "review").sum())
        n_approve = int((sub["action"] == "approve").sum())
        n_fraud = int(sub["fraud_bool"].sum())
        rows.append({
            "group": str(g),
            "n": n,
            "n_block": n_block,
            "n_review": n_review,
            "n_approve": n_approve,
            "n_fraud": n_fraud,
            "block_rate": n_block / n,
            "review_rate": n_review / n,
            "fraud_rate": n_fraud / n,
            "meets_sample_size": n >= MIN_GROUP_SIZE,
        })
    return rows


def _disparity(rows: list[dict], key: str) -> float | None:
    """Max - min of `key` across groups meeting the sample-size guard."""
    valid = [
        r[key] for r in rows
        if r["meets_sample_size"] and r[key] is not None
    ]
    if len(valid) < 2:
        return None
    return float(max(valid) - min(valid))


def _print_grouping(name: str, rows: list[dict],
                    block_disp: float | None,
                    review_disp: float | None) -> None:
    print()
    print(f"=== Grouping: {name} ===")
    print(f"{'group':<22}{'n':>10}{'block_rate':>13}"
          f"{'review_rate':>13}{'fraud_rate':>13}{'size_ok':>10}")
    print("-" * 81)
    for r in rows:
        print(
            f"{r['group']:<22}"
            f"{r['n']:>10,}"
            f"{r['block_rate']:>13.4f}"
            f"{r['review_rate']:>13.4f}"
            f"{r['fraud_rate']:>13.4f}"
            f"{str(r['meets_sample_size']):>10}"
        )
    if block_disp is None:
        print("  block-rate disparity: undefined (< 2 groups meet sample size)")
    else:
        print(f"  block-rate disparity: {block_disp:.4f} "
              f"({block_disp * 100:.2f}pp)")
    if review_disp is not None:
        print(f"  review-rate disparity: {review_disp:.4f} "
              f"({review_disp * 100:.2f}pp)")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    df = _load()
    df = _prepare_age(df)

    print(f"[fairness] Loaded {len(df):,} test-window rows")
    print(f"[fairness] Kill criterion: max block-rate disparity < "
          f"{DISPARITY_THRESHOLD * 100:.1f}pp across all groupings")
    print(f"[fairness] Sample-size guard: groups with n < "
          f"{MIN_GROUP_SIZE} excluded from disparity")

    results: dict = {
        "hypothesis": "H5",
        "kill_criterion": (
            f"max block-rate disparity < {DISPARITY_THRESHOLD} "
            "across all tested groupings"
        ),
        "disparity_threshold": DISPARITY_THRESHOLD,
        "min_group_size": MIN_GROUP_SIZE,
        "test_window_rows": int(len(df)),
        "groupings": [],
    }

    # Column name per grouping
    source_col = {
        "customer_age": "customer_age_bin",
        "employment_status": "employment_status",
        "housing_status": "housing_status",
    }

    max_block_disp_overall: float = 0.0
    max_block_disp_grouping: str | None = None

    for spec in GROUPINGS:
        col = source_col[spec["name"]]
        rows = _group_stats(df, col)
        block_disp = _disparity(rows, "block_rate")
        review_disp = _disparity(rows, "review_rate")

        _print_grouping(spec["name"], rows, block_disp, review_disp)

        results["groupings"].append({
            "name": spec["name"],
            "column": col,
            "groups": rows,
            "block_rate_disparity": block_disp,
            "review_rate_disparity": review_disp,
        })

        if block_disp is not None and block_disp > max_block_disp_overall:
            max_block_disp_overall = block_disp
            max_block_disp_grouping = spec["name"]

    # Verdict
    results["max_block_rate_disparity"] = max_block_disp_overall
    results["max_block_rate_disparity_grouping"] = max_block_disp_grouping
    if max_block_disp_overall >= DISPARITY_THRESHOLD:
        results["verdict"] = "survived"
    elif max_block_disp_grouping is None:
        results["verdict"] = "blocked"
    else:
        results["verdict"] = "killed"

    print()
    print(f"[fairness] Max block-rate disparity: "
          f"{max_block_disp_overall:.4f} "
          f"({max_block_disp_overall * 100:.2f}pp) "
          f"in grouping {max_block_disp_grouping}")
    print(f"[fairness] Verdict: {results['verdict']}")

    OUT_PATH.write_text(
        json.dumps(results, indent=2, default=str),
        encoding="utf-8",
    )
    print(f"[fairness] Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()