"""
One-shot doc reconciliation.

Replaces stale test-calibrated values with train-calibrated values across
docs/. Each (old, new) pair is verified: if the old string is not found,
the script fails loudly rather than silently skipping.

Run: python scripts/reconcile_docs.py
"""
from pathlib import Path

DOCS = Path("docs")

# (file, old_substring, new_substring)
REPLACEMENTS = [
    # ------------------------------------------------------------------
    # Global rate constant
    # ------------------------------------------------------------------
    (
        "decision_policy.md",
        "`fraud_loss_rate = 0.002067377733397323` (chosen so that `mean(fraud_loss_rate * amount_proxy) = 1.0` on the test set, keeping the comparison apples-to-apples with constant loss)",
        "`fraud_loss_rate = 0.0019187869` (chosen so that `mean(fraud_loss_rate * amount_proxy) = 1.0` on the **train** set, keeping the comparison apples-to-apples with constant loss and avoiding test-window leakage)",
    ),
    (
        "decision_policy.md",
        "fraud_loss_rate: 0.002067377733397323",
        "fraud_loss_rate: 0.0019187869",
    ),
    (
        "decision_policy.md",
        "| Amount-scaled | **0.007777** | 0.018892 | **58.8%** |",
        "| Amount-scaled (train-cal) | **0.007566** | 0.017543 | **56.9%** |",
    ),
    (
        "decision_policy.md",
        "- Cost/txn change: **−12.6%** relative",
        "- Cost/txn change: **−15.0%** relative",
    ),
    (
        "decision_policy.md",
        "**Verdict: success stop.** Amount scaling is adopted as the new default. Both thresholds were exceeded, and the policy's advantage over the strongest baseline nearly doubled.",
        "**Verdict: success stop.** Amount scaling is adopted as the new default. Both thresholds were exceeded, and the policy's advantage over the strongest baseline more than doubled. The result survives a full cost sensitivity analysis and bootstrap CIs on the test set (see `reports/decision_backtest.md` §Sensitivity and §Statistical Rigor).",
    ),

    # ------------------------------------------------------------------
    # evaluation_protocol.md
    # ------------------------------------------------------------------
    (
        "evaluation_protocol.md",
        "fraud_loss_rate: 0.002067377733397323",
        "fraud_loss_rate: 0.0019187869",
    ),
    (
        "evaluation_protocol.md",
        "- **Amount scaling was tested and adopted.** Under constant `fraud_loss`, the policy's advantage over the strongest baseline was 26.4%. Under amount scaling it is 58.8%.",
        "- **Amount scaling was tested and adopted.** Under constant `fraud_loss`, the policy's advantage over the strongest baseline was 26.4%. Under amount scaling (train-calibrated rate) it is 56.9%.",
    ),
    (
        "evaluation_protocol.md",
        "- `fraud_loss_rate = 0.002067377733397323` was chosen so that `mean(fraud_loss_rate × amount_proxy) = 1.0` on the test set. This keeps the amount-scaled run directly comparable to the constant-loss run. **Caveat:** the rate is calibrated on test-window amounts, which would not be available at deployment. In production, derive from training-window amounts. Documented as a limitation.",
        "- `fraud_loss_rate = 0.0019187869` is derived from **training-window** amounts: `1 / mean(amount_proxy on train) = 1 / 521.1626`. This keeps `mean(fraud_loss_rate × amount_proxy) = 1.0` on train, matching the constant-loss comparison scale without using test data. No test-window leakage.",
    ),
    (
        "evaluation_protocol.md",
        "**Setup:** `amount_scaled: true`, `fraud_loss_rate = 0.002067377733397323`.",
        "**Setup:** `amount_scaled: true`, `fraud_loss_rate = 0.0019187869`.",
    ),
    (
        "evaluation_protocol.md",
        "| Amount-scaled | **0.007777** | 0.018892 | **58.8%** |",
        "| Amount-scaled (train-cal) | **0.007566** | 0.017543 | **56.9%** |",
    ),
    (
        "evaluation_protocol.md",
        "- Decision flips: 5,542 / 227,491 = **2.44%**\n- Cost/txn change: **−12.6%** relative",
        "- Cost/txn change: **−15.0%** relative (satisfies the ≥ 1% stop criterion)",
    ),
    (
        "evaluation_protocol.md",
        "| Amount-scaled `fraud_loss` | ✅ Run, success stop, adopted |\n| `false_positive_cost` | ❌ Not run in MVP |\n| `review_cost` | ❌ Not run in MVP |\n| `residual_fraud_loss` | ❌ Not run in MVP |",
        "| Amount-scaled `fraud_loss` | ✅ Run, success stop, adopted |\n| `false_positive_cost` | ✅ Run — policy advantage 55.6–59.6% across 2× range |\n| `review_cost` | ✅ Run — policy advantage 46.5–64.6% across 2× range |\n| `residual_fraud_loss` | ✅ Run — policy advantage 49.9–62.1% across 2× range |",
    ),
    (
        "evaluation_protocol.md",
        "**Only amount scaling was tested.** The other three are required for the final portfolio report but were deliberately out of MVP scope.",
        "**All four parameters are tested.** Amount scaling was adopted as the default. The other three were run via `src/evaluation/sensitivity.py` and confirmed the policy remains lowest-cost across a 2× range on each. Minimum advantage across all variations: 46.46%.",
    ),
    (
        "evaluation_protocol.md",
        "### 12.3 Caveat on `fraud_loss_rate`\n\nThe rate is calibrated on test-window amounts. In production, this would derive from training-window amounts to avoid using test data. Documented as a limitation in the report.",
        "### 12.3 Rate Calibration\n\n`fraud_loss_rate` is derived from **training-window** amounts (`1 / mean(amount_proxy on train)`). No test data is used in the derivation. The earlier test-calibrated rate and its caveat are preserved in git history (`9b51a24`).",
    ),
    (
        "evaluation_protocol.md",
        "| Bootstrap CIs | ❌ Not run in MVP |",
        "| Bootstrap CIs | ✅ Run — 95% CI on advantage [52.77%, 60.91%] |",
    ),
    (
        "evaluation_protocol.md",
        "**MVP limitation, stated explicitly:** no bootstrap confidence intervals. The policy's advantage over the strongest baseline is large enough (26.4% constant, 58.8% amount-scaled) that a CI would not plausibly exclude zero, but this is an assertion rather than a measured fact. Formal significance testing is deferred.",
        "**Bootstrap CIs computed.** 1,000 resamples of the test set (n = 227,491) with replacement give a 95% CI on the policy's advantage of **[52.77%, 60.91%]**, excluding zero. The policy and baseline CIs are disjoint. See `reports/bootstrap.md` for full output and `reports/decision_backtest.md` §Statistical Rigor for interpretation.",
    ),
    (
        "evaluation_protocol.md",
        "| Random | 0.047402 | ✓ (−83.6%) |\n| Approve-all | 0.020393 | ✓ (−61.9%) |\n| Block-all | 0.098742 | ✓ (−92.1%) |\n| LightGBM + static 0.5 | 0.018892 | ✓ (−58.8%) |\n| **Cost-sensitive policy** | **0.007777** | — |",
        "| Random | 0.046931 | ✓ (−83.9%) |\n| Approve-all | 0.018928 | ✓ (−60.0%) |\n| Block-all | 0.098742 | ✓ (−92.3%) |\n| LightGBM + static 0.5 | 0.017543 | ✓ (−56.9%) |\n| **Cost-sensitive policy** | **0.007566** | — |",
    ),

    # ------------------------------------------------------------------
    # mvp_architecture.md
    # ------------------------------------------------------------------
    (
        "mvp_architecture.md",
        "fraud_loss_rate: 0.002067377733397323",
        "fraud_loss_rate: 0.0019187869",
    ),
    (
        "mvp_architecture.md",
        "The rate was chosen so that `mean(fraud_loss_rate * amount_proxy) = 1.0` on the test set, keeping the comparison with constant `fraud_loss` apples-to-apples. The result was a success stop — the policy's advantage over the strongest baseline improved from 26.4% to 58.8%.",
        "The rate is derived from **training-window** amounts: `1 / mean(amount_proxy on train) = 1 / 521.1626 = 0.0019187869`. This keeps `mean(fraud_loss_rate * amount_proxy) = 1.0` on train, matching the constant-loss comparison scale without test-window leakage. The result was a success stop — the policy's advantage over the strongest baseline improved from 26.4% to 56.9%, and the result survives full cost sensitivity and bootstrap CIs.",
    ),

    # ------------------------------------------------------------------
    # architecture.md
    # ------------------------------------------------------------------
    (
        "architecture.md",
        "amount_scaled: false\nfraud_loss_rate: 0.0",
        "amount_scaled: true\nfraud_loss_rate: 0.0019187869",
    ),

    # ------------------------------------------------------------------
    # data_card.md
    # ------------------------------------------------------------------
    (
        "data_card.md",
        "| Time granularity | **TBD — verify before modeling** (see Section 4.6) |",
        "| Time granularity | **Month-level** (integer `month`, values 0–7); day-level unavailable |",
    ),
    (
        "data_card.md",
        "This is a **blocking pre-modeling task** and appears in the Definition of Done (Section 12).",
        "**Completed.** BAF exposes month-level granularity only — no day-level timestamp. Per `evaluation_protocol.md` §6.3, delay regimes use the month-based fallback (1 / 2 / 3 months). The MVP runs a single 1-month regime. This was resolved before modeling; no day-based regime is claimed anywhere in the docs.",
    ),
    (
        "data_card.md",
        "| Week 1 | TBD after EDA | TBD after EDA | TBD after EDA |",
        "| MVP (month-based) | month 3 | month 5 | month 7 |",
    ),

    # ------------------------------------------------------------------
    # problem_framing.md
    # ------------------------------------------------------------------
    (
        "problem_framing.md",
        "| BAF timestamp granularity is insufficient | Verify before modeling; fallback to month-based regimes |",
        "| BAF timestamp granularity is insufficient | **Resolved.** Month-level only; month-based fallback applied per `evaluation_protocol.md` §6.3 |",
    ),

    # ------------------------------------------------------------------
    # 2026-09-21.md
    # ------------------------------------------------------------------
    (
        "2026-09-21.md",
        "- [ ] Amount-scaled fraud loss sensitivity analysis — **deferred**; post-MVP per `mvp_2_weeks.md` ¬ß15",
        "- [x] Amount-scaled fraud loss sensitivity analysis — **run and adopted** (see post-log update below)",
    ),
]


def main():
    n_ok = 0
    n_fail = 0
    for fname, old, new in REPLACEMENTS:
        path = DOCS / fname
        if not path.exists():
            print(f"[MISSING FILE] {path}")
            n_fail += 1
            continue
        text = path.read_text(encoding="utf-8")
        if old not in text:
            print(f"[NOT FOUND]  {fname}: {old[:60]!r}...")
            n_fail += 1
            continue
        text = text.replace(old, new, 1)
        path.write_text(text, encoding="utf-8")
        print(f"[OK]         {fname}: {old[:60]!r}...")
        n_ok += 1

    print()
    print(f"Done. {n_ok} applied, {n_fail} failed.")
    if n_fail:
        print("Fix the [NOT FOUND] entries — the exact string wasn't found.")
        print("The text in the doc may have different whitespace or wording.")


if __name__ == "__main__":
    main()