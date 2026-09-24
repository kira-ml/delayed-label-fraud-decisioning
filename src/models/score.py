"""Score the test set with the selected classifier and its saved pipeline."""
from pathlib import Path
import json
import pandas as pd
import joblib

from src.common import MODELS

TEST_PATH = Path("data/processed/test.parquet")
MODEL_PATH = MODELS / "best_model.pkl"
PREPROC_PATH = MODELS / "preprocessing.pkl"
FEATURES_PATH = MODELS / "feature_columns.json"
OUT_PATH = Path("data/processed/scored_test.parquet")


def _to_array(X):
    if hasattr(X, "toarray"):
        return X.toarray()
    return X


def main() -> None:
    test = pd.read_parquet(TEST_PATH)
    model = joblib.load(MODEL_PATH)
    pre = joblib.load(PREPROC_PATH)
    features = json.loads(FEATURES_PATH.read_text(encoding="utf-8"))

    X_test = _to_array(pre.transform(test[features]))
    p = model.predict_proba(X_test)[:, 1]
    assert ((p >= 0) & (p <= 1)).all(), "p_fraud out of [0, 1]"

    out = test.copy()
    out["p_fraud"] = p
    out.to_parquet(OUT_PATH, index=False)
    print(f"[score] Wrote {len(out):,} scored rows to {OUT_PATH}")
    print(f"[score] Mean p_fraud: {p.mean():.6f}")


if __name__ == "__main__":
    main()