"""Chronological train/val/test split for the decision pipeline.

Splits:
    train: months 0,1,2
    val:   months 3,4
    test:  months 5,6
    censored: month 7 (excluded, counted)
"""
from pathlib import Path
import pandas as pd

from src.common import (
    TRAIN_MONTHS, VAL_MONTHS, TEST_MONTHS,
)

IN_PATH = Path("data/interim/labeled.parquet")
OUT_DIR = Path("data/processed")


def split(df: pd.DataFrame):
    observed = df[df["observed"]].copy()
    train = observed[observed["month"].isin(TRAIN_MONTHS)].copy()
    val = observed[observed["month"].isin(VAL_MONTHS)].copy()
    test = observed[observed["month"].isin(TEST_MONTHS)].copy()
    censored = df[~df["observed"]].copy()
    return train, val, test, censored


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_parquet(IN_PATH)
    train, val, test, censored = split(df)

    assert len(train) + len(val) + len(test) == int(df["observed"].sum()), \
        "train + val + test != observed"

    train.to_parquet(OUT_DIR / "train.parquet", index=False)
    val.to_parquet(OUT_DIR / "val.parquet", index=False)
    test.to_parquet(OUT_DIR / "test.parquet", index=False)

    print(f"[split] Train:    {len(train):>9,}  fraud={train['fraud_bool'].mean():.4%}")
    print(f"[split] Val:      {len(val):>9,}  fraud={val['fraud_bool'].mean():.4%}")
    print(f"[split] Test:     {len(test):>9,}  fraud={test['fraud_bool'].mean():.4%}")
    print(f"[split] Censored: {len(censored):>9,}  "
          f"({100 * len(censored) / len(df):.2f}%)")


if __name__ == "__main__":
    main()