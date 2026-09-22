"""Load the BAF dataset and normalize it to the canonical schema.

Produces data/interim/transactions.parquet with:
  - transaction_id (row index)
  - amount_proxy (proposed_credit_limit)
  - sorted by month
"""
from pathlib import Path
import pandas as pd

from src.common import DATA_RAW, DATA_INTERIM, set_seed

# Canonical path first (course-required layout), then the historical fallback
CANDIDATE_PATHS = [
    DATA_RAW / "Base.csv",            # data/original/Base.csv  <- canonical
    Path("data/raw/baf/Base.csv"),    # legacy path from data_card.md v0.2
]
OUT_PATH = DATA_INTERIM / "transactions.parquet"


def _find_raw() -> Path:
    for p in CANDIDATE_PATHS:
        if p.exists():
            return p
    searched = "\n  ".join(str(p) for p in CANDIDATE_PATHS)
    raise FileNotFoundError(
        "Raw BAF dataset not found. Searched:\n  "
        f"{searched}\n"
        "Download Base.csv from the Kaggle link in docs/data_card.md §2.1 "
        "and place it at data/original/Base.csv."
    )


def load_raw(path: Path | None = None) -> pd.DataFrame:
    return pd.read_csv(path or _find_raw())


def normalize(df: pd.DataFrame) -> pd.DataFrame:
    """Add transaction_id and amount_proxy; sort by month."""
    df = df.reset_index(drop=True)
    df["transaction_id"] = df.index.astype("int64")
    if "proposed_credit_limit" in df.columns:
        df["amount_proxy"] = df["proposed_credit_limit"].astype("float64")
    df = df.sort_values("month").reset_index(drop=True)
    return df


def main() -> None:
    set_seed()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df = load_raw()
    df = normalize(df)
    df.to_parquet(OUT_PATH, index=False)
    print(f"[load] Read {_find_raw()}")
    print(f"[load] Wrote {len(df):,} rows x {df.shape[1]} cols to {OUT_PATH}")
    print(f"[load] Fraud rate: {df['fraud_bool'].mean():.4%}")
    print(f"[load] Months: {sorted(df['month'].unique())}")


if __name__ == "__main__":
    main()