"""Chronological 80/20 split for the primary classification task.

Train: months 0–5 (~80%)
Test:  months 6–7 (~20%)
"""
from pathlib import Path
import pandas as pd

from src.common import PRIMARY_TRAIN_MONTHS, PRIMARY_TEST_MONTHS

IN_PATH = Path("data/interim/transactions.parquet")
OUT_DIR = Path("data/processed")


def split(df: pd.DataFrame):
    train = df[df["month"].isin(PRIMARY_TRAIN_MONTHS)].copy()
    test = df[df["month"].isin(PRIMARY_TEST_MONTHS)].copy()
    return train, test


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_parquet(IN_PATH)
    train, test = split(df)

    train.to_parquet(OUT_DIR / "primary_train.parquet", index=False)
    test.to_parquet(OUT_DIR / "primary_test.parquet", index=False)

    n = len(df)
    print(f"[primary_split] Train: {len(train):>9,} ({100 * len(train) / n:.1f}%) "
          f"fraud={train['fraud_bool'].mean():.4%}")
    print(f"[primary_split] Test:  {len(test):>9,} ({100 * len(test) / n:.1f}%) "
          f"fraud={test['fraud_bool'].mean():.4%}")


if __name__ == "__main__":
    main()