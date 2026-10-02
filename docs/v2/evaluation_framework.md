# V2 Evaluation Framework

> **Repository:** `delayed-label-fraud-decisioning`  
> **Branch:** `v2`  
> **Purpose:** Portfolio / resume — operational extension of the V1 final-project system  
> **Document:** V2 Evaluation Framework  
> **Status:** v2.0.1 — additive to V1's evaluation protocol; §5.1 aligned with the 2026-10-03 H1 amendment; Phase A complete  
> **Last updated:** 2026-10-03

---

## 0. Derivation From V2 Framing and Falsification Plan

This document is derived from `docs/v2/problem_framing.md` §5–§6 and
`docs/v2/falsification_plan.md` §3. It specifies **how** each of the six
V2 hypotheses is evaluated: which window, which classifier, which policy,
which comparison, which metrics, and which verdict thresholds.

**Rule:** V1's `docs/evaluation_protocol.md` v1.0 remains the standard. V2
extends it. **In any conflict between this document and V1's protocol, V1's
protocol wins and this document is amended.**

**Rule:** No metric, comparison, or procedure is introduced in V2 without
being defined here. If a hypothesis needs a metric that is not defined,
this document is amended **before** the test runs.

**Rule:** Kill criteria are pre-registered in `falsification_plan.md` §3
and are not modified after results are seen. This document does not
introduce new kill criteria; it defines the measurement that decides
whether a pre-registered kill criterion is met.

---

## 1. Purpose

V1's evaluation protocol answers one question: *does the cost-sensitive
policy beat the strongest baseline on a fixed test window?*

V2 asks six different questions (H1–H6), each requiring evaluation under a
different condition: constrained capacity, longer delay, rolling
retraining, feature drift, group disparity, and stratified validity of the
direct estimate.

This document defines:

- What V2 **preserves** from V1's evaluation discipline
- What V2 **adds** in new metric categories
- How each hypothesis is evaluated **per hypothesis**
- How V2 results are **reported** and what counts as a verdict
- What is **forbidden** in V2 evaluation

It exists to prevent:

- Fragmented metrics invented separately for each hypothesis
- Contradiction with V1's protocol
- Post-hoc metric invention after results are seen
- Re-contamination of V1's frozen test window
- Ambiguity about what "survives" means for each hypothesis

---

## 2. Relationship to V1's Evaluation Protocol

V1's `docs/evaluation_protocol.md` v1.0 is inherited and remains
authoritative. V2 adds the following mappings.

| V1 protocol section | V2 status | V2 addition |
|---|---|---|
| §3 Principles | Inherited | None |
| §4 Single chronological split | Extended | H2 (multi-regime), H3 (rolling structure) |
| §5 Classifiers under comparison | Inherited | Re-opened only by H3 |
| §6 Preprocessing | Inherited | None |
| §7 Calibration gate | Extended | H6 stratifies the gate by action |
| §8 Hyperparameter selection | Inherited | None |
| §9 Decision policy | Extended | H1 constrains review capacity |
| §10 Primary metric | Inherited | Cost per transaction remains the primary metric |
| §11 Supporting metrics | Extended | V2 metrics defined in §5 below |
| §12 Baselines | Inherited | Same baseline set; retrained on the same window per hypothesis |
| §13 Statistical rigor | Inherited | Same bootstrap, seed, effect size |
| §14 Sensitivity analysis | Inherited | None for V2 |
| §15 Forbidden practices | Extended | V2 additions in §9 below |
| §17 Stop criteria | Extended | V2 verdict format in §8 below |

**Rule:** No V1 section is replaced. All V2 additions are extensions.

---

## 3. What V2 Evaluates

Six hypotheses, from `falsification_plan.md` §3, each testing a specific
load-bearing property of V1's conclusion.

| ID | Tests | Load-bearing property |
|---|---|---|
| H1 | Capacity-constrained policy | Unconstrained review |
| H2 | Multi-regime delay | 1-month delay only |
| H3 | Rolling retraining | Single static split |
| H4 | Feature drift | Static split validity |
| H5 | Group disparity | No fairness diagnostics |
| H6 | Stratified calibration | Direct cost estimate unbiased |

Each hypothesis has its own evaluation framework in §6.

---

## 4. Preserved V1 Discipline

The following V1 disciplines apply unchanged to V2. Restating them here
because each hypothesis's evaluation must satisfy all of them.

- **Test window used once per experiment.** See §4.1 for what counts as
  a new use.
- **Bootstrap confidence intervals.** 1,000 resamples, seed 42, 95% CI on
  any advantage claimed.
- **Minimum effect size.** 5% relative reduction, unless the hypothesis
  specifies otherwise in `falsification_plan.md`.
- **Pre-registered kill criteria.** Set before the test; not modified
  after results.
- **Non-findings reported as non-findings.** Same length as findings.
- **Fixed random seed 42** for all stochastic operations.
- **No shuffling.** No temporal reordering.
- **No test-window tuning.** Any form.

### 4.1 Re-Analysis of V1's Frozen Test Artifacts

Three V2 hypotheses (H1, H5, H6) re-analyze V1's frozen test-window
artifacts:

- `data/processed/scored_test.parquet` — frozen `p_fraud` scores
- `data/processed/action_log.parquet` — frozen decisions

These analyses do **not** retrain a classifier, do **not** re-tune a
policy, and do **not** modify any decision. They apply new analyses to
frozen inputs.

**Rule:** Re-analysis of V1's frozen test artifacts is **not** a new use
of the test window. The classifier and its decisions are frozen. V2 adds
analysis, not modeling.

H2 and H3 use different splits or training structures and are separate
experiments. Their evaluation windows are defined in §6.2 and §6.3
respectively. Each uses its own pre-registered split.

---

## 5. New Metric Categories

Six new metric categories are introduced by V2. Each is defined once here
and reused across hypotheses where applicable.

### 5.1 Capacity Metrics (for H1)

| Metric | Definition | Reported at |
|---|---|---|
| Review band size | Count of transactions where argmin is `review` under no constraint | Full test window |
| Capacity utilization | `min(review_band_size, K) / K` where `K` is capacity | Each capacity level |
| Cost-capacity curve | `cost/txn` as a function of `K` | `K ∈ {1%, 2%, 5%, 10%, 20%} × 227,491` |
| Cost at unconstrained capacity | V1's number restated as reference (0.007491) | Reference |
| Advantage vs. strongest baseline | `(baseline_cost - policy_cost) / baseline_cost` | Each capacity level |
| Review-band savings distribution | Distribution of `min(c_approve, c_block) - c_review` within the band | Diagnostic |

**Capacity levels tested:** `K ∈ {1%, 2%, 5%, 10%, 20%} × 227,491`.
That is `{2,275, 4,550, 11,375, 22,749, 45,498}` reviews.

**Ranking rule within the band:** descending by the argmin gap
`min(c_approve, c_block) - c_review`, where `c_approve`, `c_review`, and
`c_block` are the per-row expected costs returned by
`src/policy/decide.py` `choose_actions()`. This is the actual value of
routing a review-band transaction to review instead of its next-best
action. See `falsification_plan.md` §11 (amendment 2026-10-03) for the
change from the original pre-registered formula
(`p_fraud * fraud_loss(amount) - review_cost`). Ties broken by
`transaction_id` ascending for reproducibility.

### 5.2 Multi-Regime Delay Metrics (for H2)

| Metric | Definition |
|---|---|
| Censoring rate | Censored rows / total rows |
| Training window size | Rows in the training months |
| Validation window size | Rows in the validation months |
| Test window size | Rows in the test window |
| Policy cost/txn | Realized cost per transaction on the multi-regime test window |
| Advantage vs. strongest baseline | Same baseline set, retrained on the same window |
| Bootstrap CI on advantage | Same method as V1 |
| Degradation vs. V1 | `(V1_advantage - H2_advantage) / V1_advantage` |
| ECE on validation | Same procedure as V1, on the new validation window |

**Definition:** the multi-regime split for a delay of `d` months is:

```
observed  = month + d <= 7
train     = months [0, ..., floor((7 - d) * 2/5)]
val       = months [floor((7 - d) * 2/5) + 1, ..., floor((7 - d) * 4/5)]
test      = months [floor((7 - d) * 4/5) + 1, ..., 7 - d]
censored  = months [8 - d, ..., 7]
```

For `d = 2`: train = 0–1, val = 2–3, test = 4–5, censored = 6–7.

### 5.3 Rolling Metrics (for H3)

| Metric | Definition |
|---|---|
| Training months per step | Contiguous months used for training |
| Validation month per step | The month used for selection |
| Target month per step | The month predicted on |
| Selected classifier per step | LR / RF / LGBM |
| Validation realized cost per classifier per step | The selection criterion |
| Gap to runner-up per step | Relative % between best and second-best |
| Noise-band verdict per step | Finding (gap ≥ 5%) / Non-finding (gap < 5%) |
| Aggregate rolling cost/txn | Combined realized cost across all rolling steps |

**Steps defined:** for target month `m ∈ {5, 6}`:

- `m = 5`: train on 0–3, validate on 4, predict on 5
- `m = 6`: train on 0–4, validate on 5, predict on 6

The same hyperparameter grids and preprocessing pipeline as V1 are used
at each step. No grid modifications.

### 5.4 Drift Metrics (for H4)

| Metric | Definition | Reported for |
|---|---|---|
| PSI (Population Stability Index) | Standard PSI between adjacent months, with the earlier month as reference | Every classifier feature × every adjacent month pair |
| KS statistic | Two-sample Kolmogorov–Smirnov statistic | Continuous features × every adjacent month pair |
| Drift classification | None (`< 0.1`) / moderate (`0.1 ≤ PSI < 0.25`) / significant (`≥ 0.25`) | Per feature per month pair |
| Max PSI | Maximum PSI across all features and all adjacent pairs | One number |
| Drifted feature list | Features with any PSI `≥ 0.1` | Diagnostic list |

**Binning for continuous features:** deciles of the reference month's
distribution. Ten bins per feature.

**Binning for categorical features:** existing categories of the feature.
Categories present in the reference month and absent in the comparison
month are assigned a small epsilon frequency (`1e-6`) to avoid division
by zero. Categories absent in both months are omitted.

### 5.5 Fairness Metrics (for H5)

| Metric | Definition | Reported for |
|---|---|---|
| Block rate per group | `count(action == 'block' \| group == g) / count(group == g)` | Each group in each grouping |
| Review rate per group | `count(action == 'review' \| group == g) / count(group == g)` | Each group in each grouping |
| Fraud rate per group | `count(fraud_bool == 1 \| group == g) / count(group == g)` | Each group in each grouping (base-rate context) |
| Block-rate disparity | `max(block_rate) - min(block_rate)` within a grouping | Each grouping |
| Review-rate disparity | `max(review_rate) - min(review_rate)` within a grouping | Each grouping |

**Groupings tested:**

- `customer_age` in bins: `[0–25), [25–35), [35–45), [45–55), [55–65), [65+)`
- `employment_status` — existing BAF categories
- `housing_status` — existing BAF categories

**Sample-size guard:** groups with `count(group) < 500` are reported but
excluded from the disparity calculation. Groups below this threshold
produce unstable rates.

### 5.6 Causal Validity Metrics (for H6)

| Metric | Definition | Reported for |
|---|---|---|
| Aggregate ECE | ECE on the full test window (V1's number, restated) | Reference |
| Stratum ECE | ECE within each action stratum | `approve`, `review`, `block` |
| Stratum Brier | Brier within each action stratum | Each stratum |
| Stratum size | Count per stratum | Each stratum |
| Max stratum ECE | Maximum of the three stratum ECEs | One number |
| ECE ratio | `max_stratum_ECE / aggregate_ECE` | Diagnostic |

**Binning:** same as V1's calibration procedure — 10 quantile bins within
each stratum. If a stratum has fewer than 100 rows with `p_fraud > 0.01`,
the ECE computation uses equal-width bins (`0.1` width) instead of
quantile bins and this substitution is reported.

---

## 6. Per-Hypothesis Evaluation Framework

Each hypothesis is evaluated under the following structure. The kill
criterion is restated from `falsification_plan.md` §3 for locality; the
falsification plan is the source of truth.

### 6.1 H1 — Capacity-Constrained Decisioning

| Field | Value |
|---|---|
| Evaluation window | V1's frozen test window (227,491 rows) |
| Classifier | V1's frozen LR (`C=10.0`, `max_iter=1000`); no retrain |
| Policy | V1's argmin policy with capacity constraint applied |
| Comparison | Each capacity level vs. strongest V1 baseline (LGBM + static 0.5 = 0.017798) |
| Primary metric | Advantage at each capacity level |
| Supporting metrics | §5.1 |
| CI method | Bootstrap on the frozen test window, 1,000 resamples, seed 42 |
| Kill criterion | Advantage < 5% at any `K ≥ 4,550` |
| Verdict field | Survived / Killed / Inconclusive |

**Note:** the classifier and its scores are frozen. The capacity constraint
changes routing only. This preserves the "used once" discipline (§4.1).

### 6.2 H2 — Multi-Regime Delay

| Field | Value |
|---|---|
| Evaluation window | 2-month delay test window (months 4–5) |
| Classifier | LR (`C=10.0`, `max_iter=1000`), retrained on the 2-month training window |
| Policy | V1's argmin policy, unchanged |
| Comparison | Same baseline set, retrained on the 2-month window |
| Primary metric | Advantage on the 2-month test window |
| Supporting metrics | §5.2 |
| CI method | Bootstrap on the 2-month test window, 1,000 resamples, seed 42 |
| Kill criterion | Advantage < 5% |
| Verdict field | Survived / Killed / Inconclusive |

**Note:** this is a **new experiment** with its own pre-registered split.
It is not a re-analysis of V1's test window. V1's headline is unchanged by
H2's result unless H2 is killed, in which case V1's paper is amended with
the delay envelope.

### 6.3 H3 — Rolling Retraining

| Field | Value |
|---|---|
| Evaluation window | V1's frozen split structure, months 5 and 6 as separate test steps |
| Classifier | LR, RF, and LGBM retrained at each step |
| Policy | V1's argmin policy, unchanged |
| Comparison | Classifier selected at each step vs. V1's static LR |
| Primary metric | Which classifier wins the noise-band guard per step |
| Supporting metrics | §5.3 |
| CI method | Not applicable (selection is discrete, not a cost advantage) |
| Kill criterion | Model choice flips in either step |
| Verdict field | **Confirmed** (LR wins both steps) / **Amended** (a different classifier wins at least one step) |

**Note:** the verdict format is binary, not the standard four-verdict
format. This is intentional and documented in `falsification_plan.md` §3.
H3 tests V1's classifier conclusion, not a V2 assumption.

### 6.4 H4 — Feature Drift

| Field | Value |
|---|---|
| Evaluation window | Full transaction timeline (all 8 months) |
| Data | Raw features from `data/interim/transactions.parquet` |
| Comparison | Adjacent month pairs (0→1, 1→2, ..., 6→7) |
| Primary metric | Max PSI across all features and adjacent pairs |
| Supporting metrics | §5.4 |
| CI method | Not applicable (PSI is deterministic given the data) |
| Kill criterion | Max PSI < 0.1 |
| Verdict field | Survived / Killed |

**Note:** the analysis uses raw features, not the model's scores. It does
not touch V1's test window.

### 6.5 H5 — Group Disparity

| Field | Value |
|---|---|
| Evaluation window | V1's frozen `action_log.parquet` (test window only) |
| Data | V1's frozen decisions, joined with group attributes |
| Comparison | Block rate and review rate across groups within each grouping |
| Primary metric | Max block-rate disparity across groupings |
| Supporting metrics | §5.5 |
| CI method | Not required by the kill criterion; a bootstrap CI on each disparity is reported as supporting evidence |
| Kill criterion | Max block-rate disparity < 5 percentage points |
| Verdict field | Survived / Killed / Inconclusive |

**Note:** the analysis uses V1's frozen decisions. No decision is modified.

### 6.6 H6 — Causal Validity (Stratified Calibration)

| Field | Value |
|---|---|
| Evaluation window | V1's frozen test window |
| Data | `scored_test.parquet` joined with `action_log.parquet` and observed labels |
| Comparison | Per-stratum ECE vs. aggregate ECE |
| Primary metric | Max per-stratum ECE |
| Supporting metrics | §5.6 |
| CI method | Not required by the kill criterion |
| Kill criterion | Any action stratum has ECE ≥ 0.05 |
| Verdict field | Survived / Killed / Inconclusive |

**Note:** the diagnostic is a **necessary** condition for the direct
estimate to be unbiased, not a sufficient one. A survival means the direct
estimate is not visibly confounded by miscalibration within strata. Full
causal machinery (IPW, doubly robust) is deferred to Phase B and is only
built if H6 is killed with a material bias estimate.

---

## 7. Reporting Format

Every V2 result is reported in `reports/v2_falsification.md` using the
format below. The full report contains one section per hypothesis, in
execution order (`falsification_plan.md` §4).

```markdown
## H{n} — {Short name} — {VERDICT}

### Setup
- Test window:
- Classifier:
- Policy:
- Comparison:
- Pre-registered kill criterion: (restated from falsification_plan.md §3)

### Metrics
| Metric | Value | 95% CI (if applicable) |
|---|---:|---:|
| ... | ... | ... |

### Result
{One paragraph: what the test produced, in numbers.}

### Verdict
{Survived / Killed / Inconclusive / Blocked — one word, bolded.}

### Interpretation
{One paragraph: what this means for V1's conclusion.}

### Consequence
{What happens next: Phase B action, or drop from scope, or V1 amendment.}

### Amends V1?
{Yes (which document, which claim, dated note location) / No.}
```

**Rules for the report:**

- The report is a single file. Hypotheses are not reported separately.
- Verdicts are written only after all six tests complete.
- Non-findings use the same format and the same length as findings.
- The report is dated and versioned (`v2_falsification.md` v1.0).
- Every number in the report traces to a metric defined in §5.

---

## 8. Verdicts and Stop Criteria

Every hypothesis receives exactly one of the following verdicts. This
matches `falsification_plan.md` §5, with the H3 exception noted below.

| Verdict | Meaning | Consequence |
|---|---|---|
| **Survived** | Kill criterion not met | Conditional protocol doc; Phase B eligible |
| **Killed** | Kill criterion met | Non-finding; dropped from scope; V1 amendment if applicable |
| **Inconclusive** | Result near threshold or sample-size-limited | Reported; not eligible for Phase B; specifies what would resolve it |
| **Blocked** | Test could not run | Diagnosed before report; not a verdict |

**H3 exception.** H3's verdict is binary: **Confirmed** or **Amended**.
This is documented in `falsification_plan.md` §3 and is not an extension
of the standard four-verdict format.

**V2 overall success.** As defined in `problem_framing.md` §6.1:

- All six hypotheses tested with their documented cheapest tests
- All six have a verdict
- Verdicts written to `reports/v2_falsification.md`
- At least one hypothesis confirms or falsifies a V1 claim
- V1's headline either unchanged or explicitly amended
- No hypothesis silently dropped

---

## 9. Forbidden Practices in V2

In addition to all forbidden practices in V1's
`docs/evaluation_protocol.md` §15:

- **Modifying kill criteria after seeing results.** Corrections to a
  criterion are recorded as dated amendments to `falsification_plan.md`,
  not silent edits.
- **Re-using V1's frozen test window for new modeling.** Analysis only.
  Any new classifier, new policy, or new threshold requires a new split.
- **Reporting a V2 finding on a metric not defined in §5.** Undefined
  metrics are amended into §5 before the test runs.
- **Comparing V2 numbers to V1 numbers without labeling conditions.**
  "Under V1 conditions" and "under V2 conditions" are not
  interchangeable.
- **Presenting a non-finding as ambiguous.** A result is either a survivor
  or a kill. Inconclusive is reserved for sample-size-limited cases
  defined in §8.
- **Adding a V2 hypothesis to scope without a pre-registered kill
  criterion** in `falsification_plan.md` §3.
- **Applying causal machinery before H6's diagnostic shows it's needed.**
  IPW and doubly robust estimation are Phase B work, gated on H6 being
  killed.
- **Reporting a capacity finding at a capacity level below 2%** of test
  volume. The kill criterion explicitly excludes these levels.

---

## 10. Definition of Done for This Document

- [x] Relationship to V1's evaluation protocol defined (§2)
- [x] Preserved V1 discipline restated (§4)
- [x] Re-analysis vs. new-experiment distinction defined (§4.1)
- [x] Six new metric categories defined (§5)
- [x] Per-hypothesis evaluation framework defined for H1–H6 (§6)
- [x] Reporting format defined (§7)
- [x] Verdicts and stop criteria defined (§8)
- [x] V2-specific forbidden practices defined (§9)
- [x] §5.1 ranking rule aligned with the 2026-10-03 H1 amendment

**Downstream (not blockers for this doc):**

- [ ] `docs/v2/documentation_map.md` — V1→V2 doc status table
- [ ] `docs/v2/README.md` — reading order for the folder
- [ ] `docs/v2/cut_list.md` — written at Phase D
- [x] Run Phase A tests (2026-10-03; six verdicts recorded in
      `falsification_plan.md` §12)
- [ ] Write `reports/v2_falsification.md`
- [ ] Conditional protocol docs — written only after survivors are known
- [ ] V1 amendments — if any hypothesis killed

---

## 11. Guiding Rules

> V1's `evaluation_protocol.md` is the standard. V2 extends it. In any
> conflict, V1 wins and V2 is amended.

> No V2 metric is introduced without being defined in §5.

> Re-analysis of V1's frozen test artifacts is not a new use of the test
> window. Retraining on a different split is a new experiment with its own
> pre-registered protocol.

> Every V2 number is compared to a labeled condition. "Under V1
> conditions" and "under V2 conditions" are not interchangeable.

> A non-finding is reported at the same length as a finding. Verdicts are
> not softened.

> Kill criteria are pre-registered in `falsification_plan.md` and are not
> modified after results are seen.

> Phase B code is not written until `reports/v2_falsification.md` exists.

---

## 12. Changelog

| Date | Change | Reason |
|---|---|---|
| 2026-10-02 | v2.0-draft — initial V2 evaluation framework; six new metric categories defined; per-hypothesis evaluation specified for H1–H6; re-analysis vs. new-experiment distinction added; verdict format and reporting format defined; V2-specific forbidden practices listed | Derived from `docs/v2/problem_framing.md` §5–§6 and `docs/v2/falsification_plan.md` §3; extends V1's `docs/evaluation_protocol.md` without replacement |
| 2026-10-03 | v2.0.1 — §5.1 ranking rule aligned with the 2026-10-03 H1 amendment in `falsification_plan.md` §11; §5.1 review-band savings distribution updated to the same formula; §10 DoD updated for Phase A completion | Correct a stale formula that contradicted the pre-registered amendment; record Phase A completion |
