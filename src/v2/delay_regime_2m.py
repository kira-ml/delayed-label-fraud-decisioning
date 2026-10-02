"""H2 — Multi-regime delay: 2-month label delay.

Reruns the pipeline end-to-end under a 2-month delay regime. This is
the only V2 test that requires training a classifier on a new split.
It does not touch V1's artifacts and does not touch V1's frozen test
window. All outputs are isolated under reports/v2/intermediate/ and
data/v2/2month/ (the latter is only used if intermediate parquets are
needed; this script keeps everything in memory).

Under 2-month delay:
    decision_time = month
    label_time    = month + 2
    observed      = label_time <= 7

Split:
    train: months 0-1
    val:   months 2-3
    test:  months 4-5
    censored: months 6-7

Reads:  data/interim/transactions.parquet
        configs/costs.yaml
Writes: reports/v2/intermediate/h2_delay_2m.json

Run: python -m src.v2.delay_regime_2m

See docs/v2/falsification_plan.md §3 H2 and
    docs/v2/evaluation_framework.md §5.2 and §6.2.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.common import DATA_INTERIM, load_costs, SEED
from src.models.preprocess import (
    build_preprocessor, get_feature_columns, get_numeric_categorical,
)
from src.models.train_compare import ALGORITHMS, PARAM_GRIDS, make_model
from src.policy.decide import choose_actions
from src.evaluation.backtest import realized_cost
from src.evaluation.calibration import ece as quantile_ece

IN_PATH = DATA_INTERIM / "transactions.parquet"
OUT_DIR = Path("reports/v2/intermediate")
OUT_PATH = OUT_DIR / "h2_delay_2m.json"

DELAY_MONTHS = 2
LAST_MONTH = 7

TRAIN_MONTHS_2M = [0, 1]
VAL_MONTHS_2M = [2, 3]
TEST_MONTHS_2M = [4, 5]
CENSORED_MONTHS_2M = [6, 7]

MIN_RELATIVE_EFFECT = 0.05
SIMPLICITY_ORDER = ["logistic_regression", "random_forest", "lightgbm"]
ADVANTAGE_THRESHOLD = 0.05
N_BOOT = 1000
BOOT_SEED = 42


def _to_array(X):
    if hasattr(X, "toarray"):
        return X.toarray()
    return X


def _apply_delay(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["label_month"] = df["month"] + DELAY_MONTHS
    df["observed"] = df["label_month"] <= LAST_MONTH
    return df


def _split_2m(df: pd.DataFrame):
    obs = df[df["observed"]]
    train = obs[obs["month"].isin(TRAIN_MONTHS_2M)].copy()
    val = obs[obs["month"].isin(VAL_MONTHS_2M)].copy()
    test = obs[obs["month"].isin(TEST_MONTHS_2M)].copy()
    censored = df[~df["observed"]].copy()
    assert len(train) + len(val) + len(test) == len(obs), (
        "2-month split does not add up to observed rows"
    )
    return train, val, test, censored


def _fit_predict(alg, params, X_train, y_train, X_pred):
    pre = build_preprocessor(alg, *get_numeric_categorical(X_train))
    X_tr = _to_array(pre.fit_transform(X_train))
    X_pr = _to_array(pre.transform(X_pred))
    model = make_model(alg, params)
    model.fit(X_tr, y_train)
    return model, pre, model.predict_proba(X_pr)[:, 1]


def _noise_band_select(val_costs: dict[str, float]):
    ranked = sorted(val_costs.items(), key=lambda kv: kv[1])
    best_alg, best_mean = ranked[0]
    _, second_mean = ranked[1]
    gap = second_mean - best_mean
    rel_gap = gap / best_mean if best_mean > 0 else 0.0
    if rel_gap >= MIN_RELATIVE_EFFECT:
        return best_alg, True, rel_gap
    candidates = [
        alg for alg in SIMPLICITY_ORDER
        if alg in val_costs
        and (val_costs[alg] - best_mean) / best_mean < MIN_RELATIVE_EFFECT
    ]
    return (candidates[0] if candidates else best_alg), False, rel_gap


def _baseline_actions(p, p_rf, p_lgbm):
    n = len(p)
    rng = np.random.default_rng(SEED)
    return {
        "Random":      rng.choice(["approve", "review", "block"], size=n),
        "Approve-all": np.full(n, "approve", dtype=object),
        "Block-all":   np.full(n, "block", dtype=object),
        "LR+0.5":      np.where(p >= 0.5, "block", "approve").astype(object),
        "RF+0.5":      np.where(p_rf >= 0.5, "block", "approve").astype(object),
        "LGBM+0.5":    np.where(p_lgbm >= 0.5, "block", "approve").astype(object),
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    costs = load_costs()
    df = pd.read_parquet(IN_PATH)
    df = _apply_delay(df)
    train, val, test, censored = _split_2m(df)

    n_total = len(df)
    n_cens = len(censored)
    cens_rate = n_cens / n_total

    print(f"[h2] Loaded {n_total:,} rows, delay={DELAY_MONTHS} months")
    print(f"[h2] Censored: {n_cens:,} ({cens_rate:.2%})")
    print(f"[h2] Train (months {TRAIN_MONTHS_2M}): {len(train):,}  "
          f"fraud={train['fraud_bool'].mean():.4%}")
    print(f"[h2] Val   (months {VAL_MONTHS_2M}):   {len(val):,}  "
          f"fraud={val['fraud_bool'].mean():.4%}")
    print(f"[h2] Test  (months {TEST_MONTHS_2M}):  {len(test):,}  "
          f"fraud={test['fraud_bool'].mean():.4%}")

    features = get_feature_columns(train)
    X_train = train[features]
    y_train = train["fraud_bool"]
    X_val = val[features]
    y_val = val["fraud_bool"]
    amounts_val = val["amount_proxy"].to_numpy()
    X_test = test[features]
    y_test = test["fraud_bool"]
    amounts_test = test["amount_proxy"].to_numpy()

    # Grid search per algorithm on validation window.
    per_alg_best: dict[str, dict] = {}
    for alg in ALGORITHMS:
        best_cfg_idx = 0
        best_cost = float("inf")
        for ci, params in enumerate(PARAM_GRIDS[alg]):
            _, _, p_val = _fit_predict(
                alg, params, X_train, y_train, X_val
            )
            actions, _, _ = choose_actions(p_val, costs, amounts_val)
            rc = float(
                realized_cost(
                    actions, y_val, costs, amounts=amounts_val
                ).mean()
            )
            if rc < best_cost:
                best_cost = rc
                best_cfg_idx = ci
        per_alg_best[alg] = {
            "config_idx": best_cfg_idx,
            "config": PARAM_GRIDS[alg][best_cfg_idx],
            "val_cost": best_cost,
        }
        print(f"[h2] {alg:<22} best cfg#{best_cfg_idx}  "
              f"val_cost={best_cost:.6f}")

    val_costs = {alg: v["val_cost"] for alg, v in per_alg_best.items()}
    selected_alg, is_finding, rel_gap = _noise_band_select(val_costs)
    print(f"[h2] Selection: {selected_alg} "
          f"({'finding' if is_finding else 'non-finding/simplicity'}, "
          f"top gap {rel_gap:.2%})")

    # Refit selected classifier on the full train window; score test.
    sel_cfg = per_alg_best[selected_alg]["config"]
    model_sel, pre_sel, p_test_sel = _fit_predict(
        selected_alg, sel_cfg, X_train, y_train, X_test
    )

    # Score test with the other two classifiers for the static-0.5 baselines.
    other_ps = {}
    for alg in ALGORITHMS:
        if alg == selected_alg:
            other_ps[alg] = p_test_sel
        else:
            _, _, p_other = _fit_predict(
                alg, per_alg_best[alg]["config"],
                X_train, y_train, X_test,
            )
            other_ps[alg] = p_other

    # Assign columns for the baseline set, regardless of which is selected.
    p_lr = other_ps["logistic_regression"]
    p_rf = other_ps["random_forest"]
    p_lgbm = other_ps["lightgbm"]

    # Policy action on the test window.
    policy_actions, _, _ = choose_actions(p_test_sel, costs, amounts_test)
    policy_cost = realized_cost(
        policy_actions, y_test, costs, amounts=amounts_test
    )

    baselines = _baseline_actions(p_lr, p_rf, p_lgbm)
    baseline_costs = {
        name: realized_cost(acts, y_test, costs, amounts=amounts_test)
        for name, acts in baselines.items()
    }
    baseline_means = {
        name: float(c.mean()) for name, c in baseline_costs.items()
    }
    strongest_name = min(baseline_means, key=baseline_means.get)
    strongest_cost_arr = baseline_costs[strongest_name]
    strongest_mean = baseline_means[strongest_name]

    policy_mean = float(policy_cost.mean())
    advantage = (strongest_mean - policy_mean) / strongest_mean

    # Calibration on validation (supporting evidence).
    _, _, p_val_sel = _fit_predict(
        selected_alg, sel_cfg, X_train, y_train, X_val
    )
    ece_val, _ = quantile_ece(p_val_sel, y_val.to_numpy(), 10)
    brier_val = float(
        np.mean((p_val_sel - y_val.to_numpy()) ** 2)
    )

    # Bootstrap on the test window (same method as V1: 1000, seed 42).
    n = len(policy_cost)
    rng = np.random.default_rng(BOOT_SEED)
    pol_boot = np.empty(N_BOOT)
    bas_boot = np.empty(N_BOOT)
    adv_boot = np.empty(N_BOOT)
    for i in range(N_BOOT):
        idx = rng.integers(0, n, size=n)
        pc = float(policy_cost[idx].mean())
        bc = float(strongest_cost_arr[idx].mean())
        pol_boot[i] = pc
        bas_boot[i] = bc
        adv_boot[i] = (bc - pc) / bc if bc > 0 else 0.0

    pol_lo, pol_hi = np.percentile(pol_boot, [2.5, 97.5])
    bas_lo, bas_hi = np.percentile(bas_boot, [2.5, 97.5])
    adv_lo, adv_hi = np.percentile(adv_boot, [2.5, 97.5])
    excludes_zero = bool(adv_lo > 0)

    verdict = "survived" if advantage >= ADVANTAGE_THRESHOLD else "killed"

    print()
    print(f"[h2] Policy cost/txn:   {policy_mean:.6f}")
    print(f"[h2] Strongest baseline ({strongest_name}): "
          f"{strongest_mean:.6f}")
    print(f"[h2] Advantage: {advantage:.2%}  "
          f"95% CI [{adv_lo:.2%}, {adv_hi:.2%}]  "
          f"excludes zero: {excludes_zero}")
    print(f"[h2] ECE (val): {ece_val:.4f}  Brier (val): {brier_val:.6f}")
    print(f"[h2] Verdict: {verdict}")

    out = {
        "hypothesis": "H2",
        "delay_months": DELAY_MONTHS,
        "last_month": LAST_MONTH,
        "kill_criterion": (
            f"advantage < {ADVANTAGE_THRESHOLD:.0%} at {DELAY_MONTHS}-month delay"
        ),
        "advantage_threshold": ADVANTAGE_THRESHOLD,
        "split": {
            "train_months": TRAIN_MONTHS_2M,
            "val_months": VAL_MONTHS_2M,
            "test_months": TEST_MONTHS_2M,
            "censored_months": CENSORED_MONTHS_2M,
        },
        "n_total": int(n_total),
        "n_censored": int(n_cens),
        "censored_rate": float(cens_rate),
        "n_train": int(len(train)),
        "n_val": int(len(val)),
        "n_test": int(len(test)),
        "fraud_rate_train": float(train["fraud_bool"].mean()),
        "fraud_rate_val": float(val["fraud_bool"].mean()),
        "fraud_rate_test": float(test["fraud_bool"].mean()),
        "per_algorithm_best": per_alg_best,
        "selected_algorithm": selected_alg,
        "selection_is_finding": bool(is_finding),
        "selection_top_gap_relative": float(rel_gap),
        "policy_cost_per_txn": policy_mean,
        "baselines": baseline_means,
        "strongest_baseline": strongest_name,
        "strongest_baseline_cost_per_txn": strongest_mean,
        "advantage": float(advantage),
        "advantage_ci_95": [float(adv_lo), float(adv_hi)],
        "advantage_excludes_zero": excludes_zero,
        "policy_cost_ci_95": [float(pol_lo), float(pol_hi)],
        "baseline_cost_ci_95": [float(bas_lo), float(bas_hi)],
        "ece_val": float(ece_val),
        "brier_val": float(brier_val),
        "verdict": verdict,
    }

    OUT_PATH.write_text(
        json.dumps(out, indent=2, default=str),
        encoding="utf-8",
    )
    print(f"[h2] Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()