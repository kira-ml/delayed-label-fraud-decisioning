import pandas as pd
from src.common import DATA_INTERIM, DATA_PROCESSED

IN = DATA_INTERIM / "labeled.parquet"
TRAIN_MONTHS = {0, 1, 2}
VAL_MONTHS = {3, 4}
TEST_MONTHS = {5, 6}


def run():
    df = pd.read_parquet(IN)
    n_total = len(df)

    observed = df[df["observed"]].copy()
    n_obs = len(observed)
    n_cens = n_total - n_obs
    print(f"[split] total={n_total:,}  observed={n_obs:,}  censored={n_cens:,} ({n_cens / n_total:.2%})")

    sizes = {}
    for name, months in [("train", TRAIN_MONTHS), ("val", VAL_MONTHS), ("test", TEST_MONTHS)]:
        part = observed[observed["month"].isin(months)].copy()
        out = DATA_PROCESSED / f"{name}.parquet"
        part.to_parquet(out, index=False)
        sizes[name] = len(part)
        print(f"[split] {name}: {len(part):,} rows ({sorted(months)}) -> {out.name}")

    assert sum(sizes.values()) == n_obs, "split sizes do not add up to observed total"
    print("[split] OK")


if __name__ == "__main__":
    run()