import pandas as pd
import lightgbm as lgb
from src.common import DATA_PROCESSED, ARTIFACTS

TRAIN = DATA_PROCESSED / "train.parquet"
VAL = DATA_PROCESSED / "val.parquet"
TEST = DATA_PROCESSED / "test.parquet"
MODEL = ARTIFACTS / "model.txt"
OUT = DATA_PROCESSED / "scored_test.parquet"


def run():
    booster = lgb.Booster(model_file=str(MODEL))
    feats = booster.feature_name()

    # Rebuild the same category mapping used at training time so that
    # LightGBM's internal integer codes match. Categories come from the
    # train ∪ val union, exactly as in train_baseline.py.
    train = pd.read_parquet(TRAIN)
    val = pd.read_parquet(VAL)
    cat_cols = [c for c in feats if train[c].dtype == "object"]
    cat_maps = {
        c: sorted(set(train[c].dropna().unique()) | set(val[c].dropna().unique()))
        for c in cat_cols
    }
    del train, val

    test = pd.read_parquet(TEST)
    for c, cats in cat_maps.items():
        test[c] = pd.Categorical(test[c], categories=cats)

    missing = [c for c in feats if c not in test.columns]
    assert not missing, f"test set is missing features: {missing}"

    test["p_fraud"] = booster.predict(test[feats])
    test.to_parquet(OUT, index=False)

    lo, hi = test["p_fraud"].min(), test["p_fraud"].max()
    assert 0.0 <= lo <= hi <= 1.0
    print(f"[score] wrote {OUT.name}: {len(test):,} rows, p_fraud in [{lo:.4f}, {hi:.4f}]")
    print(f"[score] fraud rate in test: {test['fraud_bool'].mean():.4%}")


if __name__ == "__main__":
    run()