import pandas as pd
from src.common import DATA_RAW, DATA_INTERIM

BASE_CSV = DATA_RAW / "baf" / "Base.csv"
OUT = DATA_INTERIM / "transactions.parquet"


def run():
    df = pd.read_csv(BASE_CSV)
    df = df.reset_index().rename(columns={"index": "transaction_id"})
    df["amount_proxy"] = df["proposed_credit_limit"]
    df = df.sort_values("month", kind="stable").reset_index(drop=True)

    df.to_parquet(OUT, index=False)
    print(f"[load] wrote {OUT.name}: {len(df):,} rows, {len(df.columns)} cols")
    print(f"[load] months: {sorted(df['month'].unique().tolist())}")
    print(f"[load] fraud rate: {df['fraud_bool'].mean():.4%}")
    return df


if __name__ == "__main__":
    run()