"""Load the BAF dataset and normalize it to the canonical schema.

Produces data/interim/transactions.parquet with:
  - transaction_id (row index)
  - amount_proxy (proposed_credit_limit)
  - sorted by month
"""
from pathlib import Path
import pandas as pd

from src.common import set_seed

RAW_PATH = Path("data/original/Base.csv")
OUT_PATH = Path("data/interim/transactions.parquet")


def load_raw(path: Path = RAW_PATH) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"Raw dataset not found at {path}. "
            "Download the BAF Base.csv from the Kaggle link in docs/data_card.md §2.1."
        )
    return pd.read_csv(path)


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
    print(f"[load] Wrote {len(df):,} rows x {df.shape[1]} cols to {OUT_PATH}")
    print(f"[load] Fraud rate: {df['fraud_bool'].mean():.4%}")
    print(f"[load] Months: {sorted(df['month'].unique())}")


if __name__ == "__main__":
    main()