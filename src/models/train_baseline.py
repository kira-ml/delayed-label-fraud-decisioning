import pandas as pd
import lightgbm as lgb
from src.common import DATA_PROCESSED, ARTIFACTS, feature_columns

TRAIN = DATA_PROCESSED / "train.parquet"
VAL = DATA_PROCESSED / "val.parquet"
MODEL_OUT = ARTIFACTS / "model.txt"

PARAMS = {
    "objective": "binary",
    "metric": ["auc", "binary_logloss"],
    "verbosity": -1,
    "seed": 42,
    "num_threads": 0,
}


def run():
    train = pd.read_parquet(TRAIN)
    val = pd.read_parquet(VAL)

    feats = feature_columns(train)
    print(f"[train] {len(feats)} features, train={len(train):,} val={len(val):,}")

    # Convert object/string columns to pandas category with a shared category set.
    cat_cols = [c for c in feats if train[c].dtype == "object"]
    print(f"[train] categorical columns: {cat_cols}")
    for c in cat_cols:
        cats = sorted(set(train[c].dropna().unique()) | set(val[c].dropna().unique()))
        train[c] = pd.Categorical(train[c], categories=cats)
        val[c] = pd.Categorical(val[c], categories=cats)

    dtrain = lgb.Dataset(train[feats], label=train["fraud_bool"])
    dval = lgb.Dataset(val[feats], label=val["fraud_bool"], reference=dtrain)

    booster = lgb.train(
        PARAMS,
        dtrain,
        num_boost_round=2000,
        valid_sets=[dval],
        valid_names=["val"],
        callbacks=[lgb.early_stopping(50, verbose=False), lgb.log_evaluation(100)],
    )

    booster.save_model(str(MODEL_OUT))
    print(f"[train] best_iteration={booster.best_iteration}")
    print(f"[train] saved {MODEL_OUT}")


if __name__ == "__main__":
    run()