# V2 Falsification Plan

> **Repository:** `delayed-label-fraud-decisioning`  
> **Branch:** `v2`  
> **Purpose:** Portfolio / resume — operational extension of the V1 final-project system  
> **Document:** V2 Falsification Plan  
> **Status:** v2.0.1-draft — H1 ranking formula amended before execution; see §11  
> **Last updated:** 2026-10-03

---

## 0. Derivation From V2 Problem Framing

This document is derived from `docs/v2/problem_framing.md` §5.1 and §8. It
names the six hypotheses that test whether V1's headline conclusion survives
operational reality, and it pre-registers the cheapest test and the numeric
kill criterion for each.

**Rule:** Every test in this document runs on existing V1 artifacts unless
explicitly stated otherwise. Where re-running an existing pipeline with new
parameters is required, that is stated in the hypothesis section.

**Rule:** Kill criteria are pre-registered. They are not modified after
results are seen. If a criterion turns out to be wrong, the correction is
recorded as a V2 amendment to this file with a date, not as a silent edit.

**Rule:** A hypothesis that fails its kill criterion is reported as a
non-finding and dropped from scope. Dropping is a legitimate outcome, not a
V2 failure.

**Rule:** No V2 code is written before Phase A produces a survivor. The two
exceptions are the two tests that require re-running an existing pipeline
with a new parameter (H2, H3), which are already parameterized.

---

## 1. Purpose

V1's headline finding — a 57.91% cost reduction vs. the strongest baseline,
with a 95% bootstrap CI of [53.95%, 62.13%] — was produced under three
load-bearing conditions that V1 did not vary:

1. A single static train/val/test split, no retraining.
2. A single 1-month label delay.
3. Unconstrained review capacity.

If any of those three conditions is what produced the advantage — rather
than the decision-centric framing itself — V1's claim is narrower than
it appears.

This document tests that narrower claim. It exists to prevent V2 from
becoming a feature checklist by forcing every proposed addition through a
pre-registered falsifiable test with a numeric kill criterion.

The output is a single report: `reports/v2_falsification.md`, one row per
hypothesis, one verdict per hypothesis. The report is written after all six
tests complete.

---

## 2. Method

Each hypothesis is structured identically:

- **Hypothesis.** A falsifiable claim, stated as a single sentence.
- **Load-bearing property.** Which V1 condition it tests.
- **Cheapest test.** The smallest experiment that can falsify the claim.
  Stated in terms of existing artifacts wherever possible.
- **Kill criterion.** A numeric threshold, pre-registered. If met, the
  hypothesis is killed.
- **If survives.** What happens next. A survived hypothesis earns a
  conditional spec and a Phase B build.
- **If killed.** What happens next. A killed hypothesis is dropped and
  recorded as a non-finding.
- **Effort.** Rough time estimate for the test alone.
- **Status.** `not started` at the time this document is written.

Tests are ordered by cost, cheapest first. The execution order is §4.

**What "cheapest" means:**

| Test cost category | Definition |
|---|---|
| Zero new code | Runs on existing artifacts via a script using existing functions |
| Minor code | A parameterized re-run of an existing pipeline step |
| Full re-run | A pipeline re-run with new configuration |

Five of six tests are "zero new code" or "minor code." One (H2) requires
a full re-run with a new delay regime. This is by design.

---

## 3. The Six Hypotheses

### Summary Table

| ID | Hypothesis | Cost | Kill criterion (pre-registered) | Status |
|---|---|---|---|---|
| H1 | Advantage stays >5% at plausible review capacity | Zero new code | Advantage <5% at any capacity ≥2% of test volume | not started |
| H2 | Advantage stays >5% at 2-month delay | Full re-run | Advantage <5% at 2-month delay | not started |
| H3 | LR still wins under rolling monthly retraining | Minor code | Model choice flips in either rolling step | not started |
| H4 | Feature drift is measurable month-over-month | Zero new code | Max PSI <0.1 across all features and all adjacent month pairs | not started |
| H5 | Block rate differs >5pp across protected groups | Zero new code | Max disparity <5pp across all tested groupings | not started |
| H6 | Direct cost estimate is not materially confounded | Zero new code | Any action-stratum ECE ≥0.05 | not started |

---

### H1 — Capacity-Constrained Decisioning

**Hypothesis.**  
The V1 policy advantage (>5% relative cost reduction vs. the strongest
baseline) is preserved when review is constrained to a finite per-window
capacity.

**Load-bearing property tested.**  
V1's unconstrained review. Every transaction routed to `review` was
reviewed. In V1's action distribution, 21,371 of 227,491 test transactions
(~9.4%) were routed to review. A real fraud operations team cannot review
9.4% of transactions at that scale.

**Cheapest test.**  
Rerun the decision step on existing `data/processed/scored_test.parquet`
with a capacity cap. Procedure:

1. Recompute expected costs for all three actions on the test window
   using existing `src/policy/decide.py` logic and the frozen
   `configs/costs.yaml`.
2. Identify transactions in the review band (i.e., where the argmin is
   `review` under no constraint).
3. For each capacity level `K ∈ {1%, 2%, 5%, 10%, 20%} × 227,491`:
   - Rank review-band transactions by the actual argmin gap
     `min(c_approve, c_block) - c_review`, where `c_*` are the expected
     costs returned by `src/policy/decide.py` `choose_actions()`
     (see §11 Amendments, 2026-10-03).
   - Keep top-`K` in review.
   - Route the rest by approve-vs-block argmin only.
4. Compute realized cost per transaction at each `K`.
5. Compare to the strongest baseline (LGBM + static 0.5 = 0.017798).

No classifier retraining. No new policy code beyond the ranking and
re-routing logic. Existing `choose_actions` function is reused.

**Kill criterion.**  
At any tested capacity `K ≥ 2% × 227,491 ≈ 4,550`, the advantage drops
below 5% relative reduction vs. the strongest baseline. If this occurs,
finite capacity is a real fragility of the V1 result.

Capacities below 2% are excluded from the kill criterion because they
represent review loads so small that no realistic fraud operation would
be designed around them.

**If survives.**  
Implement capacity-aware policy in `src/policy/decide_capacity.py`. Write
`docs/v2/protocols/decision_policy_capacity.md` before implementing. Add
capacity utilization as a V2 metric. Add a `configs/policy.yaml` with
`capacity_per_window`.

**If killed.**  
Record the capacity level at which the advantage breaks. This becomes the
V2 finding: "the V1 advantage requires review capacity above X% of
transaction volume." V1's paper is amended with a stated operating
envelope.

**Effort.**  
Half a day.

**Status.** `not started`

---

### H2 — Multi-Regime Delay

**Hypothesis.**  
The V1 policy advantage (>5% relative cost reduction) is preserved when
the label delay is 2 months instead of 1 month.

**Load-bearing property tested.**  
V1's single delay regime. `label_time = month + 1`. Under 2-month delay,
`label_time = month + 2`, which censors more rows and shrinks the effective
training window.

**Cheapest test.**  
Parameterize `src/data/simulate_delay.py` to accept `label_offset`. Rerun
the full pipeline (`python -m src.pipeline`) with `label_offset=2`.

Under 2-month delay:
- Observed: months 0–5 (since `month + 2 ≤ 7`).
- Censored: months 6–7.
- Split: train 0–1, val 2–3, test 4–5.
- Training rows: approximately 250,000 (down from 397,039).
- Censoring rate: approximately 25% (up from 9.68%).

The classifier is retrained on the smaller training window. The policy is
unchanged. The cost matrix is unchanged. The comparison is against the
same baseline set, retrained on the same window.

A 3-month delay (`label_offset=3`) is run as an exploratory follow-up if
the 2-month result survives. It is not part of H2's kill criterion.

**Kill criterion.**  
At 2-month delay, the policy advantage drops below 5% relative reduction
vs. the strongest baseline (retrained on the same window).

**If survives.**  
Extend `docs/data_card.md` with multi-regime delay rules. Add a
multi-regime comparison to `reports/v2_falsification.md` and to V1's
paper as a robustness subsection. The 3-month exploratory result is
reported even if it does not survive.

**If killed.**  
Record the delay regime at which the advantage breaks. V2 finding: "the
V1 advantage requires label delay ≤ N months." V1's paper is amended with
a stated delay envelope.

**Effort.**  
One day (mostly pipeline runtime).

**Status.** `not started`

---

### H3 — Rolling Retraining

**Hypothesis.**  
Logistic Regression remains the selected classifier under rolling monthly
retraining, as it was under V1's single static split.

**Load-bearing property tested.**  
V1's static split. V1 selected LR over LGBM by the noise-band guard
(LGBM vs. LR gap = 1.07%, below the 5% threshold). This selection may be
specific to the single split used. Under rolling retraining, the model
sees different training windows at each step.

**Cheapest test.**  
For each test month `m ∈ {5, 6}`:

1. Train on all observed months before `m` minus one validation month.
   - For `m = 5`: train on 0–3, validate on 4, predict on 5.
   - For `m = 6`: train on 0–4, validate on 5, predict on 6.
2. Fit LR, RF, and LGBM on the same training window with the same
   preprocessing pipeline and the same hyperparameter grids.
3. Select by validation realized cost with the same noise-band guard.
4. Record which classifier is selected at each step.
5. Evaluate the policy on the target test month using the selected
   classifier.

Compare the rolling-selected classifier against the V1 static-selected
classifier (LR, `C=10.0`, `max_iter=1000`).

**Kill criterion.**  
The model choice flips in either rolling step. That is, at `m = 5` or
`m = 6`, a classifier other than LR is selected by the noise-band guard.

Note: this is not a "kill the hypothesis" in the usual sense. The outcome
is binary — **confirmed** or **amended**. If confirmed, V1's classifier
conclusion holds. If amended, V1's paper requires a dated note that LR's
selection is split-dependent.

**If confirmed (LR still wins both steps).**  
Add a "Rolling retraining" subsection to V1's paper confirming the
classifier conclusion is stable. No V2 code beyond the test.

**If amended (model choice flips).**  
V1's paper is amended. Record the flip conditions. The rolling-selected
classifier becomes the V2 default for any subsequent V2 experiments.

**Effort.**  
One day.

**Status.** `not started`

---

### H4 — Feature Drift

**Hypothesis.**  
Feature drift is measurable month-over-month in the BAF dataset. That is,
at least one feature shows a Population Stability Index (PSI) ≥ 0.1 between
consecutive months.

**Load-bearing property tested.**  
The validity of V1's static split. If features drift substantially month
over month, a static split may overstate the policy's real-world
performance. V1's `data_card.md` §5.3 already names fraud-rate drift as a
limitation but does not quantify feature drift.

**Cheapest test.**  
Compute PSI for all 28 classifier features between consecutive months
(0→1, 1→2, ..., 6→7) on `data/interim/transactions.parquet`.

For continuous features, bin into deciles using month 0's distribution as
the reference. For categorical features, use the category frequencies.

PSI formula:

```
PSI = sum over bins of (actual% - expected%) * ln(actual% / expected%)
```

Interpretation threshold (industry standard):

- PSI < 0.1: no meaningful drift
- 0.1 ≤ PSI < 0.25: moderate drift, monitor
- PSI ≥ 0.25: significant drift, action required

No new code beyond a PSI computation script. Existing artifacts suffice.

**Kill criterion.**  
Max PSI across all features and all adjacent month pairs is < 0.1. If met,
feature drift is not measurable in BAF at month granularity, and a drift
detector has no signal to detect.

**If survives (any PSI ≥ 0.1).**  
Write `docs/v2/protocols/monitoring.md` specifying a PSI-based drift
detector, alert thresholds, and a response policy (retrain / recalibrate /
alert). Implement the detector in `src/monitoring/drift_detector.py`.
Add a drift summary to V1's paper.

**If killed (all PSI < 0.1).**  
Record the non-finding. Drift detection is dropped from V2 scope. V1's
static split is not invalidated by drift at month granularity.

**Effort.**  
Half a day.

**Status.** `not started`

---

### H5 — Group Disparity

**Hypothesis.**  
V1's block decisions differ by more than 5 percentage points across at
least one grouping of transactions by a candidate protected attribute.

**Load-bearing property tested.**  
Group fairness of the V1 policy. V1's `decision_policy.md` §11 named
segment disparity as out of scope. It is a real operational and regulatory
concern, and BAF's features include plausible proxies.

**Cheapest test.**  
Using `data/processed/action_log.parquet` (test window only):

1. Define candidate groupings:
   - `customer_age` in bins: [0–25), [25–35), [35–45), [45–55), [55–65), [65+]
   - `employment_status` categories (existing in BAF)
   - `housing_status` categories (existing in BAF)
2. For each grouping, compute block rate per group:
   `block_rate(g) = count(action == 'block' | group == g) / count(group == g)`
3. Compute `max(block_rate) - min(block_rate)` across groups within each
   grouping.
4. Report per-group fraud rates alongside block rates, so the diagnostic
   distinguishes "different treatment" from "different base rates."

No new code beyond a groupby. Existing artifacts suffice.

**Kill criterion.**  
Maximum block-rate disparity < 5 percentage points across all tested
groupings. If met, group disparity is not measurable at this sample size
and threshold.

The 5pp threshold is a standard fairness-diagnostic starting point. It is
not a regulatory threshold and is not treated as one.

**If survives (any disparity ≥ 5pp).**  
Write `docs/v2/protocols/fairness.md` specifying:
- Which grouping shows disparity
- Whether disparity is explained by base-rate differences
- Candidate constraints (equalized odds, demographic parity on block rate)
- Cost-fairness tradeoff evaluation plan

Implement the constraint only if the diagnostic shows disparity that is
not explained by base rate.

**If killed (all disparities < 5pp).**  
Record the non-finding. Fairness constraints are dropped from V2 scope.
V1's paper adds a short paragraph noting that no disparity above 5pp was
measured on the tested groupings.

**Effort.**  
Half a day.

**Status.** `not started`

---

### H6 — Causal Validity of the Direct Estimate

**Hypothesis.**  
V1's direct estimate of the policy's cost (realized cost per transaction
on the test window) is not materially confounded by the policy's
deterministic selection on features that correlate with unobserved
outcome determinants.

**Load-bearing property tested.**  
The internal validity of V1's headline number. V1's policy is
deterministic: given `p_fraud` and `amount`, it produces one action. There
is no randomization. Direct cost estimation is therefore an observational
estimate. If the classifier is calibrated within each action stratum, the
direct estimate is approximately the causal estimate under conditional
exchangeability given the model's inputs. If calibration fails within any
stratum, confounding is plausible.

**Cheapest test.**  
Stratified calibration check on the test window.

1. Using `data/processed/scored_test.parquet` and
   `data/processed/action_log.parquet` (joined on `transaction_id`), split
   the test window by action: `approve`, `review`, `block`.
2. Within each action stratum, compute ECE (10 quantile bins) of
   `p_fraud` against observed `fraud_bool`.
3. Report per-stratum ECE and per-stratum Brier.
4. Compare to the aggregate ECE (V1's number, 0.0033).

Under conditional exchangeability given the model's inputs, per-stratum
calibration is a necessary condition for the direct estimate to be
unbiased. If per-stratum ECE is comparable to aggregate ECE, the direct
estimate is approximately unbiased. If any stratum's ECE materially
exceeds the aggregate, confounding is plausible and the direct estimate
may over- or under-state the policy's true effect.

No new code beyond a stratified version of the existing
`src/evaluation/calibration.py` logic.

**Kill criterion.**  
Any action stratum has ECE ≥ 0.05. If met, causal machinery (IPW,
doubly robust estimation, or a randomized logging experiment) is required
to validate the V1 headline. H6 is killed.

**If survives (all stratum ECE < 0.05).**  
Record the confirmation. The V1 direct estimate is approximately
unbiased. Full causal machinery is not required for V2. A short paragraph
in V1's paper states the stratified calibration result as a validity
check on the headline number.

**If killed (any stratum ECE ≥ 0.05).**  
Write `docs/v2/protocols/causal_evaluation.md` specifying:
- Which stratum shows miscalibration
- The direction and magnitude of the plausible bias on the V1 headline
- Whether a doubly-robust estimator (combining propensity and outcome
  models) is feasible on the existing action log
- Whether a randomized logging experiment on the test window is required

Implement the estimator only if the bias is material (>5% of the V1
advantage).

**Effort.**  
Half a day for the diagnostic. Full causal machinery is a Phase B
project if H6 is killed.

**Status.** `not started`

---

## 4. Execution Order

Cheapest first. The order is chosen so that early kills reduce the scope
of later work.

| Step | Hypothesis | Reason for position |
|---|---|---|
| 1 | H4 — Drift | Pure script; if no drift, H2's multi-regime result is easier to interpret |
| 2 | H5 — Fairness | Groupby; independent of the pipeline |
| 3 | H1 — Capacity | Re-ranks existing artifacts; highest-EV test |
| 4 | H6 — Causal diagnostic | Stratified calibration; cheap; gates Phase B causal work |
| 5 | H3 — Rolling retrain | Refit loop; no pipeline re-run |
| 6 | H2 — Multi-regime delay | Full pipeline re-run; save for last |

**Rule:** Verdicts are not written until all six tests complete. The
falsification report is a single document produced at the end of Phase A.

**Rule:** If a test unexpectedly requires code beyond the "zero new code"
or "minor code" categories in §3, the scope change is recorded as an
amendment to this file before the test runs.

---

## 5. Verdict Format

Every hypothesis receives exactly one of four verdicts:

| Verdict | Meaning | Action |
|---|---|---|
| **Survived** | Hypothesis holds; kill criterion not met | Write conditional spec; enter Phase B |
| **Killed** | Hypothesis falsified; kill criterion met | Report non-finding; drop from scope |
| **Inconclusive — needs more data** | Test ran but produced an ambiguous result (e.g., effect size near threshold, sample size limits) | Report; do not enter Phase B; specify what additional data would resolve it |
| **Blocked** | Test could not be run (missing artifact, broken dependency) | Diagnose; do not proceed; do not enter Phase B |

**Rule:** "Inconclusive" is not used to avoid a decision. If the test
produced a result, that result is either a survivor or a kill. Inconclusive
is reserved for cases where the test could not produce a discriminating
result at the available sample size.

**Rule:** "Blocked" is a diagnostic signal, not a verdict. It is resolved
before the falsification report is written.

---

## 6. Non-Findings Discipline

A killed hypothesis is a **non-finding** and is reported as such. The
reporting format per non-finding:

```markdown
## H{n} — {Short name} — KILLED

**Test run:** {date}
**Test result:** {the numeric output that triggered the kill}
**Kill criterion:** {the pre-registered threshold, restated}
**Interpretation:** {one paragraph on what this means for V1's claim}
**Consequence:** {what is dropped from V2 scope; whether V1 needs amendment}
**Amends V1?:** {yes / no; if yes, which V1 document and which claim}
```

Non-findings are reported at the same length as findings. A V2 that
produces three findings and three non-findings is a stronger artifact than
a V2 that produces six findings, because the non-findings demonstrate the
discipline that produced the findings.

---

## 7. V1 Amendment Rules

If a hypothesis produces a result that contradicts V1, V1 is amended, not
defended. The amendment rules:

1. **The V1 number is preserved with a label.** The original number is
   restated as "under V1 conditions" alongside the new number.
2. **The V1 claim is narrowed.** The original claim stands for the
   conditions under which it was produced. It is not extended.
3. **The amendment is dated.** V1's paper and `docs/paper/reference_sheet.md`
   receive a dated note at the point of the claim.
4. **The amendment is recorded in `docs/v2/documentation_map.md`.** V1→V2
   status changes are tracked in one place.

The V1 headline is amended if:

- H1 is killed: the 57.91% advantage is bounded to "unconstrained review."
- H2 is killed: the 57.91% advantage is bounded to "1-month delay."
- H3 is amended: LR's selection is noted as split-dependent.
- H6 is killed: the direct estimate is noted as having measurable
  confounding in the affected stratum.

H4 and H5 do not amend the headline directly. They amend the limitations
section.

---

## 8. Relationship to V2 Problem Framing

This document is derived from `docs/v2/problem_framing.md` §5.1 and §8.
Every rule in §0 of the framing document applies here. Specifically:

- The base-rate assumption (framing §5.3) applies: most hypotheses are
  expected to be non-findings.
- The scope discipline (framing §4, §5.2) applies: no test is added
  without a kill criterion.
- The falsification discipline (framing §8) is the organizing method of
  this document.

The falsification report (`reports/v2_falsification.md`) is the output of
this plan. It is the gate to Phase B. No Phase B work begins until the
report is written.

---

## 9. Definition of Done for This Document

- [x] All six hypotheses are stated as falsifiable claims (§3)
- [x] Every hypothesis has a cheapest test (§3)
- [x] Every hypothesis has a numeric kill criterion, pre-registered (§3)
- [x] Every hypothesis has a survivor action and a kill action (§3)
- [x] Every hypothesis has an effort estimate (§3)
- [x] Execution order is cheapest-first (§4)
- [x] Verdict format is defined (§5)
- [x] Non-findings discipline is defined (§6)
- [x] V1 amendment rules are defined (§7)
- [x] Relationship to the V2 problem framing is stated (§8)

**Downstream (not blockers for this doc):**

- [ ] `docs/v2/documentation_map.md` — V1→V2 doc status table
- [ ] `docs/v2/README.md` — reading order for the folder
- [ ] `docs/v2/cut_list.md` — what V2 does not do and why
- [ ] Run Phase A tests, write `reports/v2_falsification.md`
- [ ] Conditional protocol docs — written only after survivors are known

---

## 10. Guiding Rules

> Every hypothesis has a cheapest test and a numeric kill criterion
> written before the test runs. No exceptions.

> Kill criteria are not modified after results are seen. If a criterion is
> wrong, the correction is recorded as a dated amendment, not a silent
> edit.

> A killed hypothesis is a non-finding. Non-findings are reported at the
> same length as findings.

> A V1 headline that is contradicted by a V2 result is amended, not
> defended. The V1 number is preserved with a conditions label.

> The falsification report is the gate to Phase B. No Phase B code is
> written before the report exists.

---

## 11. Amendments

### 2026-10-03 — H1 ranking formula corrected before execution

**Original (as pre-registered on 2026-10-02, §3 H1):**

```
expected_savings = p_fraud * fraud_loss(amount) - review_cost
```

**Amended (before H1 ran):**

```
expected_savings = min(c_approve, c_block) - c_review
```

where `c_approve`, `c_review`, and `c_block` are the per-row expected
costs returned by `src/policy/decide.py` `choose_actions()`.

**Reason:** the original formula ignored `residual_fraud_loss` and the
`block` alternative. It is a two-action ranking heuristic applied to a
three-action policy: it frames the choice as "approve vs. review" when
the actual choice at each transaction is "approve / review / block." The
amended formula is the actual value of routing a transaction to review
instead of its next-best action, which is what the capacity allocation
problem requires.

**Discipline check:** this amendment is dated before H1's first
execution. No H1 results were seen before the formula was changed. The
change distinguishes "design error caught in review" from "goalposts
moved after results." It is the former.

**Source of truth:** the amended formula uses the same components that
`src/policy/decide.py` `choose_actions()` returns per row
(`c_approve`, `c_review`, `c_block`), so ranking is consistent with
action selection. The original formula would have required re-deriving
`fraud_loss(amount)` and `review_cost` separately from the costs dict,
duplicating logic that already exists in `choose_actions()`.

**Effect on kill criterion:** none. The kill criterion (§3 H1) is
"advantage < 5% at any tested capacity `K ≥ 4,550`." It is a property of
the outcome, not of the ranking formula. The amendment changes which
transactions stay in the review band when capacity binds; it does not
change the kill criterion.

---

## 12. Changelog

| Date | Change | Reason |
|---|---|---|
| 2026-10-02 | v2.0-draft — initial falsification plan; six hypotheses H1–H6; cheapest tests pre-registered; kill criteria pre-registered; execution order defined; verdict format defined; V1 amendment rules defined | First-principles scoping of V2 as a falsification exercise on V1's conclusion, derived from `docs/v2/problem_framing.md` §5.1 and §8 |
| 2026-10-03 | v2.0.1 — H1 ranking formula amended before execution; see §11 Amendments | Correct the ranking formula before results are seen; preserve falsification discipline |
