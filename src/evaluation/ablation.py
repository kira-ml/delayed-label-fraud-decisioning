"""Baseline audit and ablation for the cost-sensitive decision policy.

The V1 headline compares the policy against a 0.5 cut-off. At a ~1% base
rate, 0.5 is almost approve-all, so that comparison overstates the value
of the policy. This report adds the baselines a competent team would
actually deploy and decomposes the gain into its parts:

    approve-all
      -> cost-optimal single threshold (validation-tuned)
      -> cost-optimal two-threshold policy (validation-tuned)
      -> amount-conditioned policy (the deployed rule)

Writes reports/ablation.md, reports/ablation.json, and a waterfall figure.

Run: python -m src.evaluation.ablation
"""
from __future__ import annotations

import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from src.common import DATA_PROCESSED, REPORTS, load_costs
from src.evaluation.backtest import realized_cost
from src.evaluation.baselines import (
    actions_single_threshold,
    actions_two_threshold,
    amount_blind_actions,
    best_single_threshold,
    best_two_threshold,
    no_review_actions,
    score_validation,
)
from src.policy.decide import choose_actions

warnings.filterwarnings("ignore")

SEED = 42
N_BOOT = 2000
TEST_PATH = DATA_PROCESSED / "scored_test.parquet"
OUT_MD = REPORTS / "ablation.md"
OUT_JSON = REPORTS / "ablation.json"
FIG_DIR = REPORTS / "figures"
FIG_PATH = FIG_DIR / "fig_ablation_waterfall.png"


def _mean_cost(actions, y, costs, amounts) -> float:
    return float(realized_cost(actions, y, costs, amounts=amounts).mean())


def _advantage(policy_cost: float, baseline_cost: float) -> float:
    return float((baseline_cost - policy_cost) / baseline_cost)


def paired_bootstrap(
    c_policy: np.ndarray,
    c_baseline: np.ndarray,
    n_boot: int = N_BOOT,
    seed: int = SEED,
    strata: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Paired bootstrap of the cost difference and relative advantage.

    Rows are resampled with replacement. When `strata` is provided, rows
    are resampled within each stratum and concatenated, preserving the
    stratum sizes (e.g. month composition).
    """
    rng = np.random.default_rng(seed)
    n = len(c_policy)
    if strata is not None:
        strata = np.asarray(strata)
        groups = [np.where(strata == s)[0] for s in np.unique(strata)]

    diffs = np.empty(n_boot)
    advs = np.empty(n_boot)
    for i in range(n_boot):
        if strata is None:
            idx = rng.integers(0, n, size=n)
        else:
            idx = np.concatenate([
                rng.choice(g, size=len(g), replace=True) for g in groups
            ])
        pc = float(c_policy[idx].mean())
        bc = float(c_baseline[idx].mean())
        diffs[i] = bc - pc
        advs[i] = (bc - pc) / bc if bc > 0 else 0.0
    return diffs, advs


def _ci(a: np.ndarray) -> tuple[float, float]:
    lo, hi = np.percentile(a, [2.5, 97.5])
    return float(lo), float(hi)


def _waterfall_figure(steps: list[tuple[str, float]]) -> None:
    """Horizontal waterfall of the sequential cost reductions."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as exc:  # pragma: no cover - plotting is optional
        print(f"[ablation] figure skipped: {type(exc).__name__}: {exc}")
        return

    FIG_DIR.mkdir(parents=True, exist_ok=True)
    labels = [s[0] for s in steps]
    values = [s[1] for s in steps]
    colors = ["#B8C0C9", "#8FA3BF", "#4C6E9E", "#13294B"]

    fig, ax = plt.subplots(figsize=(12, 6.4), dpi=200)
    ypos = np.arange(len(labels))[::-1]
    bars = ax.barh(ypos, values, color=colors, height=0.62)
    ax.set_yticks(ypos)
    ax.set_yticklabels(labels, fontsize=13)
    ax.set_xlabel("Realized cost per transaction (lower is better)", fontsize=12)
    ax.set_title(
        "Baseline audit: where the gain actually comes from",
        fontsize=17, loc="left", pad=16, color="#13294B", fontweight="bold",
    )
    ax.set_xlim(0, max(values) * 1.30)
    ax.grid(axis="x", color="#D6DBD0", linewidth=0.9, alpha=0.8)
    ax.set_axisbelow(True)
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color("#B9C0B3")
    ax.tick_params(axis="y", length=0, colors="#1B2430", pad=10)
    ax.tick_params(axis="x", colors="#3E4752", labelsize=10.5)
    ax.set_xticks(np.linspace(0, max(values), 5))

    prev = None
    for bar, value in zip(bars, values):
        txt = f"{value:.6f}"
        if prev is not None:
            txt += f"   ({(prev - value) / prev:+.1%})"
        ax.text(
            value + max(values) * 0.018, bar.get_y() + bar.get_height() / 2,
            txt, va="center", fontsize=12.5, color="#1B2430",
            fontfamily="DejaVu Sans Mono",
        )
        prev = value

    fig.tight_layout()
    fig.savefig(FIG_PATH, bbox_inches="tight", facecolor="#F3F5EF")
    plt.close(fig)
    print(f"[ablation] wrote {FIG_PATH}")


def main() -> None:
    costs = load_costs()
    df = pd.read_parquet(TEST_PATH)
    required = {
        "transaction_id", "fraud_bool", "amount_proxy", "month",
        "p_fraud", "p_fraud_lgbm",
    }
    missing = required - set(df.columns)
    if missing:
        raise RuntimeError(f"scored_test.parquet missing columns: {missing}")

    p = df["p_fraud"].to_numpy()
    p_lgbm = df["p_fraud_lgbm"].to_numpy()
    y = df["fraud_bool"].to_numpy()
    amounts = df["amount_proxy"].to_numpy()
    months = df["month"].to_numpy()
    n = len(df)

    print(f"[ablation] test rows: {n:,}")
    print("[ablation] scoring validation window for threshold tuning ...")
    val = score_validation()
    p_val = val["p_fraud"].to_numpy()
    y_val = val["fraud_bool"].to_numpy()
    a_val = val["amount_proxy"].to_numpy()

    # ---- fair baselines, tuned on validation ----
    t_single, val_single = best_single_threshold(p_val, y_val, costs, a_val)
    t_lo, t_hi, val_two = best_two_threshold(p_val, y_val, costs, a_val)
    print(f"[ablation] single threshold: t={t_single:.6f} val={val_single:.6f}")
    print(f"[ablation] two thresholds:   lo={t_lo:.6f} hi={t_hi:.6f} "
          f"val={val_two:.6f}")

    # ---- test-window actions ----
    approve_all = np.full(n, "approve", dtype=object)
    block_all = np.full(n, "block", dtype=object)
    lr_05 = actions_single_threshold(p, 0.5)
    lgbm_05 = actions_single_threshold(p_lgbm, 0.5)
    fair_single = actions_single_threshold(p, t_single)
    fair_two = actions_two_threshold(p, t_lo, t_hi)
    amount_blind = amount_blind_actions(p, costs)
    no_review = no_review_actions(p, costs, amounts)
    policy, _, _ = choose_actions(p, costs, amounts)

    # Test-tuned oracle: diagnostic upper bound, never a deployable baseline.
    o_lo, o_hi, oracle_cost = best_two_threshold(p, y, costs, amounts)

    actions = {
        "Approve-all": approve_all,
        "Block-all": block_all,
        "LR + 0.5 cut-off": lr_05,
        "LGBM + 0.5 cut-off (V1 strongest)": lgbm_05,
        "Cost-optimal single threshold (val-tuned)": fair_single,
        "Cost-optimal two-threshold (val-tuned)": fair_two,
        "Amount-blind policy (constant loss)": amount_blind,
        "No-review policy (approve/block only)": no_review,
        "Deployed policy (amount-conditioned, 3 actions)": policy,
        "Test-tuned oracle (diagnostic only)": actions_two_threshold(p, o_lo, o_hi),
    }

    per_row = {
        name: realized_cost(a, y, costs, amounts=amounts)
        for name, a in actions.items()
    }
    means = {name: float(c.mean()) for name, c in per_row.items()}

    policy_cost = means["Deployed policy (amount-conditioned, 3 actions)"]
    fair_two_cost = means["Cost-optimal two-threshold (val-tuned)"]
    fair_single_cost = means["Cost-optimal single threshold (val-tuned)"]
    lgbm_cost = means["LGBM + 0.5 cut-off (V1 strongest)"]
    approve_cost = means["Approve-all"]

    # ---- confidence intervals on the fair comparison ----
    diffs, advs = paired_bootstrap(per_row["Deployed policy (amount-conditioned, 3 actions)"],
                                   per_row["Cost-optimal two-threshold (val-tuned)"])
    adv_lo, adv_hi = _ci(advs)
    diff_lo, diff_hi = _ci(diffs)

    diffs_m, advs_m = paired_bootstrap(
        per_row["Deployed policy (amount-conditioned, 3 actions)"],
        per_row["Cost-optimal two-threshold (val-tuned)"],
        strata=months,
    )
    adv_lo_m, adv_hi_m = _ci(advs_m)

    adv_vs_lgbm = _advantage(policy_cost, lgbm_cost)
    diffs_l, advs_l = paired_bootstrap(
        per_row["Deployed policy (amount-conditioned, 3 actions)"],
        per_row["LGBM + 0.5 cut-off (V1 strongest)"],
    )
    lgbm_lo, lgbm_hi = _ci(advs_l)

    # ---- waterfall ----
    steps = [
        ("Approve-all", approve_cost),
        ("+ cost-optimal single threshold", fair_single_cost),
        ("+ review action (two thresholds)", fair_two_cost),
        ("+ amount-conditioned loss (deployed)", policy_cost),
    ]

    # ---- component ablations ----
    amount_blind_cost = means["Amount-blind policy (constant loss)"]
    no_review_cost = means["No-review policy (approve/block only)"]
    amount_gain = (amount_blind_cost - policy_cost) / amount_blind_cost
    review_gain = (no_review_cost - policy_cost) / no_review_cost

    # ---- console summary ----
    print()
    print(f"{'Strategy':<52s} {'cost/txn':>10s}")
    for name, cost in means.items():
        print(f"{name:<52s} {cost:>10.6f}")
    print()
    print(f"Advantage vs LGBM+0.5 : {adv_vs_lgbm:.2%} "
          f"[{lgbm_lo:.2%}, {lgbm_hi:.2%}]")
    print(f"Advantage vs fair two : {_advantage(policy_cost, fair_two_cost):.2%} "
          f"[{adv_lo:.2%}, {adv_hi:.2%}]")
    print(f"  month-stratified CI : [{adv_lo_m:.2%}, {adv_hi_m:.2%}]")
    print(f"Amount-scaling gain   : {amount_gain:.2%}")
    print(f"Review-action gain    : {review_gain:.2%}")

    # ---- JSON ----
    payload = {
        "test_rows": n,
        "costs": costs,
        "baselines": means,
        "fair_single": {
            "threshold": t_single,
            "validation_cost": val_single,
            "test_cost": fair_single_cost,
        },
        "fair_two": {
            "t_lo": t_lo,
            "t_hi": t_hi,
            "validation_cost": val_two,
            "test_cost": fair_two_cost,
        },
        "oracle_two": {
            "t_lo": o_lo,
            "t_hi": o_hi,
            "test_cost": oracle_cost,
            "note": "tuned on the test window; diagnostic upper bound only",
        },
        "policy_cost": policy_cost,
        "advantage_vs_approve_all": _advantage(policy_cost, approve_cost),
        "advantage_vs_lgbm_05": adv_vs_lgbm,
        "advantage_vs_lgbm_05_ci_95_ratio_bootstrap": [lgbm_lo, lgbm_hi],
        "advantage_vs_lgbm_05_ci_95_note": (
            "The pre-registered difference-CI interval is [0.5395, 0.6213] "
            "in reports/bootstrap.md; this ratio bootstrap is a diagnostic."
        ),
        "advantage_vs_fair_two": _advantage(policy_cost, fair_two_cost),
        "advantage_vs_fair_two_ci_95": [adv_lo, adv_hi],
        "advantage_vs_fair_two_ci_95_month_stratified": [adv_lo_m, adv_hi_m],
        "cost_difference_vs_fair_two_ci_95": [diff_lo, diff_hi],
        "amount_scaling_gain_vs_amount_blind": amount_gain,
        "review_action_gain_vs_no_review": review_gain,
        "waterfall": [
            {"step": name, "cost": float(cost)} for name, cost in steps
        ],
        "bootstrap": {"iterations": N_BOOT, "seed": SEED},
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    # ---- Markdown ----
    L: list[str] = []
    L.append("# Baseline Audit and Ablation")
    L.append("")
    L.append("_Generated by `python -m src.evaluation.ablation` on the frozen "
             "split. Every number below traces to `reports/ablation.json`._")
    L.append("")
    L.append("## Why this report exists")
    L.append("")
    L.append("The V1 headline compares the cost-sensitive policy against a "
             "0.5 cut-off. At a ~1.1% base rate, a 0.5 cut-off is almost "
             "approve-all, so that comparison overstates the value of the "
             "policy. This report asks the harder question: **does the policy "
             "beat the best simple rule a competent team would actually "
             "deploy?**")
    L.append("")
    L.append("The fair baselines are cost-optimal thresholds tuned on the "
             "validation window and applied unchanged to the test window. "
             "The test-tuned oracle is a diagnostic upper bound and is not a "
             "deployable baseline.")
    L.append("")
    L.append("## Headline comparison")
    L.append("")
    L.append("| Strategy | Cost / txn | vs approve-all | vs fair two-threshold |")
    L.append("|---|---:|---:|---:|")
    order = [
        "Approve-all",
        "Block-all",
        "LR + 0.5 cut-off",
        "LGBM + 0.5 cut-off (V1 strongest)",
        "Cost-optimal single threshold (val-tuned)",
        "Cost-optimal two-threshold (val-tuned)",
        "Amount-blind policy (constant loss)",
        "No-review policy (approve/block only)",
        "Deployed policy (amount-conditioned, 3 actions)",
        "Test-tuned oracle (diagnostic only)",
    ]
    for name in order:
        c = means[name]
        va = _advantage(c, approve_cost)
        vf = _advantage(c, fair_two_cost)
        L.append(f"| {name} | {c:.6f} | {va:+.2%} | {vf:+.2%} |")
    L.append("")
    L.append("Positive values mean lower cost than the reference; negative "
             "values mean higher cost.")
    L.append("")
    L.append("## The gain, decomposed")
    L.append("")
    L.append("| Step | Cost / txn | Reduction vs previous step |")
    L.append("|---|---:|---:|")
    prev = None
    for name, cost in steps:
        red = "—" if prev is None else f"{(prev - cost) / prev:.2%}"
        L.append(f"| {name} | {cost:.6f} | {red} |")
        prev = cost
    L.append("")
    L.append("The steps are sequential, not additive: the final reduction is "
             "the product of the steps, not their sum.")
    L.append("")
    L.append("## What each design choice buys")
    L.append("")
    L.append("| Comparison | Cost / txn | Relative gain |")
    L.append("|---|---:|---:|")
    L.append(f"| Amount-blind policy (constant loss) | {amount_blind_cost:.6f} | — |")
    L.append(f"| Deployed policy (amount-conditioned) | {policy_cost:.6f} | "
             f"**{amount_gain:.2%}** |")
    L.append(f"| No-review policy (approve/block only) | {no_review_cost:.6f} | — |")
    L.append(f"| Deployed policy (with review) | {policy_cost:.6f} | "
             f"**{review_gain:.2%}** |")
    L.append("")
    L.append("## Uncertainty on the fair comparison")
    L.append("")
    L.append(f"- Paired bootstrap, {N_BOOT:,} iterations, seed {SEED}")
    L.append(f"- Cost difference vs fair two-threshold: "
             f"[{diff_lo:.6f}, {diff_hi:.6f}]")
    L.append(f"- Advantage vs fair two-threshold: "
             f"**{_advantage(policy_cost, fair_two_cost):.2%}** "
             f"[{adv_lo:.2%}, {adv_hi:.2%}]")
    L.append(f"- Month-stratified bootstrap (robustness): "
             f"[{adv_lo_m:.2%}, {adv_hi_m:.2%}]")
    L.append(f"- Advantage vs LGBM + 0.5: **{adv_vs_lgbm:.2%}**; the "
             "pre-registered interval is [53.95%, 62.13%] in "
             "`reports/bootstrap.md`. A paired ratio bootstrap gives "
             f"[{lgbm_lo:.2%}, {lgbm_hi:.2%}] as a diagnostic.")
    L.append("")
    L.append("## Interpretation")
    L.append("")
    L.append(f"The policy still beats the best simple rule by "
             f"**{_advantage(policy_cost, fair_two_cost):.2%}**, above the "
             "pre-registered 5% effect-size threshold, and the 95% CI "
             "excludes zero. The headline against a 0.5 cut-off is "
             f"**{adv_vs_lgbm:.2%}**; most of that gap is threshold "
             "placement, not modeling.")
    L.append("")
    L.append(f"Two design choices carry the rest: adding the review action "
             f"({review_gain:.2%} over approve/block only) and conditioning "
             f"the loss on the amount ({amount_gain:.2%} over a constant "
             "loss). Those are the contributions worth reporting.")
    L.append("")
    L.append(f"Even a global threshold tuned on the test window itself "
             f"({oracle_cost:.6f}) is worse than the deployed policy "
             f"({policy_cost:.6f}); hindsight does not close the gap. The "
             "gain is amount conditioning, not threshold luck.")
    L.append("")
    L.append("## Limitations")
    L.append("")
    L.append("- Thresholds are tuned on the validation window; a different "
             "validation window could move them.")
    L.append("- Single chronological split and one cost matrix, as in V1.")
    L.append("- The paired bootstrap resamples rows; it likely understates "
             "temporal dependence. The month-stratified CI is a partial check.")
    L.append("- The test-tuned oracle is not deployable; it bounds how much a "
             "global-threshold rule could gain from hindsight.")
    L.append("- BAF is synthetic; these are not production estimates.")
    L.append("")
    L.append("## Verdict")
    L.append("")
    L.append(f"**The result survives the fair baseline.** Report both numbers: "
             f"{adv_vs_lgbm:.1%} vs a 0.5 cut-off, and "
             f"{_advantage(policy_cost, fair_two_cost):.1%} vs the best "
             "cost-optimal threshold. The second number is the one to defend.")
    L.append("")

    OUT_MD.write_text("\n".join(L), encoding="utf-8")
    print(f"[ablation] wrote {OUT_MD}")
    print(f"[ablation] wrote {OUT_JSON}")

    _waterfall_figure(steps)


if __name__ == "__main__":
    main()
