"""Read-only diagnostic: check whether RF+0.5 or LGBM+0.5 beats LR+0.5.

Does not touch models on disk, reports, or the pipeline.

Run:
    python -m scripts.check_baselines
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from src.common import load_costs
from src.models.preprocess import (
    build_preprocessor, get_feature_columns, get_numeric_categorical,
)
from src.models.train_compare import ALGORITHMS, RESULTS_PATH, make_model
from src.evaluation.backtest import realized_cost


def _to_array(X):
    return X.toarray() if hasattr(X, "toarray") else X


def _static_actions(p):
    return np.where(p >= 0.5, "block", "approve").astype(object)


def main() -> None:
    train = pd.read_parquet("data/processed/train.parquet")
    test = pd.read_parquet("data/processed/test.parquet")
    features = get_feature_columns(train)
    costs = load_costs()

    X_train = train[features]
    y_train = train["fraud_bool"]
    X_test = test[features]
    y_test = test["fraud_bool"].to_numpy()
    amounts_test = test["amount_proxy"].to_numpy()

    data = json.loads(RESULTS_PATH.read_text())
    selected_params = data["selected_params"]

    rows = []
    for alg in ALGORITHMS:
        params = selected_params[alg]
        model = make_model(alg, params)

        pre = build_preprocessor(alg, *get_numeric_categorical(X_train))
        X_tr = _to_array(pre.fit_transform(X_train))
        X_te = _to_array(pre.transform(X_test))

        model.fit(X_tr, y_train)
        p = model.predict_proba(X_te)[:, 1]
        acts = _static_actions(p)
        rc = realized_cost(acts, y_test, costs, amounts=amounts_test).mean()
        rows.append((alg, rc))

    # Also include approve-all and block-all for completeness
    n = len(y_test)
    approve_all = np.full(n, "approve", dtype=object)
    block_all = np.full(n, "block", dtype=object)
    approve_cost = realized_cost(approve_all, y_test, costs, amounts=amounts_test).mean()
    block_cost = realized_cost(block_all, y_test, costs, amounts=amounts_test).mean()

    print()
    print("=== Static 0.5 baselines on test window ===")
    for alg, rc in rows:
        print(f"  {alg:<22} + 0.5   {rc:.6f}")
    print(f"  approve-all                     {approve_cost:.6f}")
    print(f"  block-all                       {block_cost:.6f}")
    print()

    strongest_alg, strongest_rc = min(rows, key=lambda kv: kv[1])
    print(f"Strongest classifier + 0.5: {strongest_alg} ({strongest_rc:.6f})")
    print(f"Currently reported strongest (LR+0.5): 0.018737")
    if abs(strongest_rc - 0.018737) < 1e-6:
        print("-> UNCHANGED. LR+0.5 remains the strongest baseline.")
    else:
        print("-> CHANGED. Report the new strongest baseline to the user.")


if __name__ == "__main__":
    main()