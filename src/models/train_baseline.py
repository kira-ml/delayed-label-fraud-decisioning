"""Train the supplementary LightGBM baseline on the chronological split."""
from pathlib import Path
import json
import pandas as pd
import lightgbm as lgb

from src.common import FEATURE_EXCLUDE, CATEGORICAL_COLS, SEED
from src.models.preprocess import get_feature_columns

TRAIN_PATH = Path("data/processed/train.parquet")
VAL_PATH = Path("data/processed/val.parquet")
MODEL_PATH = Path("artifacts/model.txt")
CATEGORIES_PATH = Path("artifacts/categories.json")


def _prepare(df: pd.DataFrame, features: list[str],
             categories: dict | None = None) -> pd.DataFrame:
    X = df[features].copy()
    for c in CATEGORICAL_COLS:
        if c not in X.columns:
            continue
        if categories and c in categories:
            X[c] = pd.Categorical(X[c], categories=categories[c])
        else:
            X[c] = X[c].astype("category")
    return X


def main() -> None:
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    train = pd.read_parquet(TRAIN_PATH)
    val = pd.read_parquet(VAL_PATH)

    features = get_feature_columns(train)
    X_train = _prepare(train, features)
    X_val = _prepare(val, features, categories={
        c: X_train[c].cat.categories
        for c in CATEGORICAL_COLS if c in X_train.columns
    })
    y_train = train["fraud_bool"]
    y_val = val["fraud_bool"]

    params = {
        "objective": "binary",
        "metric": "auc",
        "seed": SEED,
        "verbose": -1,
        # NOTE: no is_unbalance / scale_pos_weight here. The cost-sensitive
        # policy assumes calibrated probabilities. Class reweighting shifts
        # the outputs by ~90x and makes E[cost] incorrect. Asymmetry is
        # handled by the cost matrix, not by the training objective.
    }

    dtrain = lgb.Dataset(X_train, y_train)
    dval = lgb.Dataset(X_val, y_val, reference=dtrain)

    model = lgb.train(
        params,
        dtrain,
        num_boost_round=1000,
        valid_sets=[dval],
        callbacks=[lgb.early_stopping(50, verbose=False)],
    )
    model.save_model(str(MODEL_PATH))
    print(f"[train_baseline] Best iteration: {model.best_iteration}")
    print(f"[train_baseline] Saved model to {MODEL_PATH}")

    cat_map = {
        c: [str(v) for v in X_train[c].cat.categories]
        for c in CATEGORICAL_COLS if c in X_train.columns
    }
    CATEGORIES_PATH.write_text(json.dumps(cat_map, indent=2), encoding="utf-8")
    print(f"[train_baseline] Saved categories to {CATEGORIES_PATH}")


if __name__ == "__main__":
    main()