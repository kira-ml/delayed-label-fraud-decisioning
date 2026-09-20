import pandas as pd
from src.common import DATA_INTERIM

IN = DATA_INTERIM / "transactions.parquet"
OUT = DATA_INTERIM / "labeled.parquet"

DELAY_MONTHS = 1
LAST_MONTH = 7


def run():
    df = pd.read_parquet(IN)
    df["label_month"] = df["month"] + DELAY_MONTHS
    df["observed"] = df["label_month"] <= LAST_MONTH

    df.to_parquet(OUT, index=False)

    n = len(df)
    n_cens = int((~df["observed"]).sum())
    print(f"[delay] wrote {OUT.name}: {n:,} rows")
    print(f"[delay] censored: {n_cens:,} ({n_cens / n:.2%})")
    return df


if __name__ == "__main__":
    run()