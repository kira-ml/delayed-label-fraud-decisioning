"""Score the supplementary test set with the LightGBM baseline."""
from pathlib import Path
import pandas as pd
import lightgbm as lgb

from src.common import CATEGORICAL_COLS
from src.models.preprocess import get_feature_columns

TRAIN_PATH = Path("data/processed/train.parquet")
VAL_PATH = Path("data/processed/val.parquet")
TEST_PATH = Path("data/processed/test.parquet")
MODEL_PATH = Path("artifacts/model.txt")
OUT_PATH = Path("data/processed/scored_test.parquet")


def main() -> None:
    test = pd.read_parquet(TEST_PATH)
    train = pd.read_parquet(TRAIN_PATH)
    val = pd.read_parquet(VAL_PATH)
    model = lgb.Booster(model_file=str(MODEL_PATH))

    features = get_feature_columns(test)
    X_test = test[features].copy()

    # Rebuild category mapping from train + val (same as training-time)
    ref = pd.concat([train[features], val[features]], axis=0)
    for c in CATEGORICAL_COLS:
        if c in X_test.columns:
            cats = ref[c].astype("category").cat.categories
            X_test[c] = pd.Categorical(X_test[c], categories=cats)

    p = model.predict(X_test)
    assert ((p >= 0) & (p <= 1)).all(), "p_fraud out of [0, 1]"

    out = test.copy()
    out["p_fraud"] = p
    out.to_parquet(OUT_PATH, index=False)
    print(f"[score] Wrote {len(out):,} scored rows to {OUT_PATH}")
    print(f"[score] Mean p_fraud: {p.mean():.6f}")


if __name__ == "__main__":
    main()