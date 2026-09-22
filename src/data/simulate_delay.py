"""Simulate the 1-month label delay regime.

Produces data/interim/labeled.parquet with two new columns:
  - label_month = month + DELAY_MONTHS
  - observed    = label_month <= LAST_MONTH
"""
from pathlib import Path
import pandas as pd

IN_PATH = Path("data/interim/transactions.parquet")
OUT_PATH = Path("data/interim/labeled.parquet")

DELAY_MONTHS = 1
LAST_MONTH = 7


def simulate(df: pd.DataFrame,
             delta: int = DELAY_MONTHS,
             last_month: int = LAST_MONTH) -> pd.DataFrame:
    df = df.copy()
    df["label_month"] = df["month"] + delta
    df["observed"] = df["label_month"] <= last_month
    return df


def main() -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df = pd.read_parquet(IN_PATH)
    df = simulate(df)
    df.to_parquet(OUT_PATH, index=False)
    n_censored = int((~df["observed"]).sum())
    print(f"[simulate_delay] Wrote {len(df):,} rows to {OUT_PATH}")
    print(f"[simulate_delay] Censored: {n_censored:,} "
          f"({100 * n_censored / len(df):.2f}%)")


if __name__ == "__main__":
    main()