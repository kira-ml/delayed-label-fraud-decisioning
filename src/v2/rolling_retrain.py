"""H3 — Rolling retraining classifier-stability diagnostic.

Tests whether the V1 classifier selection (LR over LGBM/RF by the
noise-band guard) is specific to the single static split, or stable
under rolling monthly retraining.

Design note: H3's pre-registered split (falsification_plan.md §3 H3)
uses month 5 as both step-1's test month and step-2's validation month.
This overlap is a characteristic of the rolling structure and is
recorded as a limitation in the H3 verdict. Step-1's selection uses
month 4 validation; step-2's selection uses month 5 validation;
each step's target month is separate.

Reads:  data/interim/labeled.parquet
        configs/costs.yaml
Writes: reports/v2/intermediate/h3_rolling_retrain.json

Run: python -m src.v2.rolling_retrain

See docs/v2/falsification_plan.md §3 H3 and
    docs/v2/evaluation_framework.md §5.3 and §6.3.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.common import DATA_INTERIM, load_costs
from src.models.preprocess import (
    build_preprocessor, get_feature_columns, get_numeric_categorical,
)
from src.models.train_compare import ALGORITHMS, PARAM_GRIDS, make_model
from src.policy.decide import choose_actions
from src.evaluation.backtest import realized_cost

LABELED = DATA_INTERIM / "labeled.parquet"
OUT_DIR = Path("reports/v2/intermediate")
OUT_PATH = OUT_DIR / "h3_rolling_retrain.json"

# Pre-registered rolling steps from falsification_plan.md §3 H3.
STEPS = [
    {"target_month": 5, "train_months": [0, 1, 2, 3], "val_month": 4},
    {"target_month": 6, "train_months": [0, 1, 2, 3, 4], "val_month": 5},
]

# Noise-band guard, per V1's evaluation_protocol.md §17.1 and §13.2.
MIN_RELATIVE_EFFECT = 0.05
SIMPLICITY_ORDER = ["logistic_regression", "random_forest", "lightgbm"]

# V1's static-selected classifier configuration.
V1_LR_PARAMS = {"C": 10.0, "max_iter": 1000}


def _to_array(X):
    if hasattr(X, "toarray"):
        return X.toarray()
    return X


def _fit_predict(
    alg: str,
    params: dict,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_pred: pd.DataFrame,
) -> np.ndarray:
    """Fit on train, return p_fraud on pred."""
    pre = build_preprocessor(alg, *get_numeric_categorical(X_train))
    X_tr = _to_array(pre.fit_transform(X_train))
    X_pr = _to_array(pre.transform(X_pred))
    model = make_model(alg, params)
    model.fit(X_tr, y_train)
    return model.predict_proba(X_pr)[:, 1]


def _noise_band_select(val_costs: dict[str, float]) -> tuple[str, bool]:
    """Apply V1's noise-band guard to per-algorithm validation costs.

    Returns (selected_algorithm, is_finding).
    """
    ranked = sorted(val_costs.items(), key=lambda kv: kv[1])
    best_alg, best_mean = ranked[0]
    _, second_mean = ranked[1]
    gap = second_mean - best_mean
    rel_gap = gap / best_mean if best_mean > 0 else 0.0

    if rel_gap >= MIN_RELATIVE_EFFECT:
        return best_alg, True

    candidates = [
        alg for alg in SIMPLICITY_ORDER
        if alg in val_costs
        and (val_costs[alg] - best_mean) / best_mean < MIN_RELATIVE_EFFECT
    ]
    return (candidates[0] if candidates else best_alg), False


def _run_step(step: dict, labeled: pd.DataFrame, costs: dict) -> dict:
    train_months = step["train_months"]
    val_month = step["val_month"]
    target_month = step["target_month"]

    train_df = labeled[labeled["month"].isin(train_months)]
    val_df = labeled[labeled["month"] == val_month]
    target_df = labeled[labeled["month"] == target_month]

    features = get_feature_columns(train_df)
    X_train = train_df[features]
    y_train = train_df["fraud_bool"]
    X_val = val_df[features]
    y_val = val_df["fraud_bool"]
    amounts_val = val_df["amount_proxy"].to_numpy()
    X_target = target_df[features]
    y_target = target_df["fraud_bool"]
    amounts_target = target_df["amount_proxy"].to_numpy()

    print(f"\n--- Step: target month {target_month} "
          f"(train {train_months}, val {val_month}) ---")
    print(f"    train n={len(train_df):,}  val n={len(val_df):,}  "
          f"target n={len(target_df):,}")

    per_alg_best: dict[str, dict] = {}
    for alg in ALGORITHMS:
        best_cfg_idx = 0
        best_cost = float("inf")
        for ci, params in enumerate(PARAM_GRIDS[alg]):
            p_val = _fit_predict(alg, params, X_train, y_train, X_val)
            actions, _, _ = choose_actions(p_val, costs, amounts_val)
            rc = float(
                realized_cost(
                    actions, y_val, costs, amounts=amounts_val
                ).mean()
            )
            print(f"    {alg:<22} cfg#{ci}  val_cost={rc:.6f}")
            if rc < best_cost:
                best_cost = rc
                best_cfg_idx = ci
        per_alg_best[alg] = {
            "config_idx": best_cfg_idx,
            "config": PARAM_GRIDS[alg][best_cfg_idx],
            "val_cost": best_cost,
        }

    val_costs = {alg: v["val_cost"] for alg, v in per_alg_best.items()}
    selected_alg, is_finding = _noise_band_select(val_costs)

    print(f"    Selected: {selected_alg} "
          f"({'finding' if is_finding else 'non-finding/simplicity'})")

    # Target-month evaluation: selected classifier.
    sel_cfg = per_alg_best[selected_alg]["config"]
    p_target_sel = _fit_predict(
        selected_alg, sel_cfg, X_train, y_train, X_target
    )
    actions_sel, _, _ = choose_actions(
        p_target_sel, costs, amounts_target
    )
    target_cost_sel = float(
        realized_cost(
            actions_sel, y_target, costs, amounts=amounts_target
        ).mean()
    )

    # Target-month evaluation: V1's LR.
    p_target_lr = _fit_predict(
        "logistic_regression", V1_LR_PARAMS, X_train, y_train, X_target
    )
    actions_lr, _, _ = choose_actions(
        p_target_lr, costs, amounts_target
    )
    target_cost_lr = float(
        realized_cost(
            actions_lr, y_target, costs, amounts=amounts_target
        ).mean()
    )

    print(f"    Target cost (selected {selected_alg}): "
          f"{target_cost_sel:.6f}")
    print(f"    Target cost (V1 LR):                    "
          f"{target_cost_lr:.6f}")

    return {
        "target_month": target_month,
        "train_months": train_months,
        "val_month": val_month,
        "n_train": int(len(train_df)),
        "n_val": int(len(val_df)),
        "n_target": int(len(target_df)),
        "per_algorithm_best": per_alg_best,
        "val_costs": val_costs,
        "selected_algorithm": selected_alg,
        "is_finding": bool(is_finding),
        "target_cost_selected": target_cost_sel,
        "target_cost_v1_lr": target_cost_lr,
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    costs = load_costs()
    labeled = pd.read_parquet(LABELED)
    labeled = labeled[labeled["observed"]].copy()

    print(f"[h3] Loaded {len(labeled):,} observed rows "
          f"(months {sorted(labeled['month'].unique().tolist())})")
    print(f"[h3] Kill criterion: model choice flips in either rolling step")
    print(f"[h3] Noise-band threshold: {MIN_RELATIVE_EFFECT:.0%}")

    results = []
    for step in STEPS:
        r = _run_step(step, labeled, costs)
        results.append(r)

    selections = [r["selected_algorithm"] for r in results]
    lr_every_step = all(s == "logistic_regression" for s in selections)
    verdict = "confirmed" if lr_every_step else "amended"

    print()
    print(f"[h3] Selections: {selections}")
    print(f"[h3] LR selected at every step: {lr_every_step}")
    print(f"[h3] Verdict: {verdict}")

    out = {
        "hypothesis": "H3",
        "kill_criterion": "model choice flips in either rolling step",
        "verdict_format": "binary: confirmed / amended",
        "min_relative_effect": MIN_RELATIVE_EFFECT,
        "simplicity_order": SIMPLICITY_ORDER,
        "v1_lr_params": V1_LR_PARAMS,
        "n_observed": int(len(labeled)),
        "steps": results,
        "selections": selections,
        "lr_selected_at_every_step": bool(lr_every_step),
        "verdict": verdict,
    }

    OUT_PATH.write_text(
        json.dumps(out, indent=2, default=str),
        encoding="utf-8",
    )
    print(f"[h3] Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()