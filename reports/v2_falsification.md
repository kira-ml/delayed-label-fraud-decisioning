# V2 Falsification Report — Phase A

> **Repository:** `delayed-label-fraud-decisioning`
> **Branch:** `v2`
> **Document:** V2 Falsification Report — Phase A assembled audit trail
> **Status:** v1.0 — Phase A exit artifact
> **Last updated:** 2026-10-03
> **Sources of truth:** `reports/v2/intermediate/*.json`
> **Governing documents:** `docs/v2/falsification_plan.md`,
> `docs/v2/evaluation_framework.md`, `docs/v2/stop_criteria.md`

---

## 0. Purpose

This is the assembled Phase A report. It contains one section per
hypothesis, in execution order from `falsification_plan.md` §4
(H4 → H5 → H1 → H6 → H3 → H2).

Every number in this report traces to an intermediate JSON file under
`reports/v2/intermediate/`. No number is invented. No verdict is
re-decided. Verdicts are transcribed from `falsification_plan.md` §12.

Per `stop_criteria.md` §4.1 and `evaluation_framework.md` §11, this file
is the sole remaining Phase A exit item and the gate to Phase B. No
Phase B code is written until this file exists.

---

## 1. Method

Six hypotheses were pre-registered in `falsification_plan.md` §3, each
with a cheapest test and a numeric kill criterion written before the
test ran. Phase A executed on 2026-10-03. No kill criterion was modified
after results were seen. The single amendment to H1's ranking formula
(`falsification_plan.md` §11, 2026-10-03) was made before H1 executed.

Verdicts use the format in `falsification_plan.md` §5, with H3's
documented binary exception (`evaluation_framework.md` §8): H3 is
**Confirmed** or **Amended**, not Survived/Killed.

Non-findings are reported at the same length and rigor as findings
(`falsification_plan.md` §6).

---

## 2. Verdict Summary

| ID | Hypothesis | Verdict | Key number | Evidence |
|---|---|---|---|---|
| H1 | Policy advantage stays >5% at plausible review capacity | **survived** | 44.25% at K=4,550 | `h1_capacity.json` |
| H2 | Policy advantage stays >5% at 2-month delay | **survived** | 58.08%, CI [56.35%, 59.72%] | `h2_delay_2m.json` |
| H3 | LR still wins under rolling monthly retraining | **confirmed** (fragile) | gap 4.25% / 4.17% (V1: 1.07%) | `h3_rolling_retrain.json` |
| H4 | Feature drift measurable month-over-month | **survived** | max PSI 3.94; 23/28 drift | `h4_drift.json`, `h4_importance_crossref.json` |
| H5 | Block rate differs >5pp across protected groups | **killed** | max disparity 2.26pp < 5pp | `h5_fairness.json` |
| H6 | Direct cost estimate not materially confounded | **killed** (immaterial) | block stratum ECE 0.0600; bias below materiality | `h6_stratified_calibration.json` |

**V1 headline status:** not overturned. Strengthened by H1 and H2,
confirmed-with-fragility by H3, challenged-but-not-broken by H4, and
two proposed concerns (H5, H6) dismissed as non-findings.

**Phase B scope:** exactly two builds — capacity-aware policy (H1) and
drift detector (H4). **Phase C:** skipped per `stop_criteria.md` §4.3.

---

## H4 — Feature Drift — SURVIVED

### Setup

- **Evaluation window:** full transaction timeline (all 8 months)
- **Data:** raw features from `data/interim/transactions.parquet`
- **Comparison:** adjacent month pairs (0→1, 1→2, ..., 6→7)
- **Pre-registered kill criterion:** max PSI < 0.1 across all features
  and all adjacent month pairs

### Metrics

| Metric | Value |
|---|---:|
| Max PSI overall | **3.9429** |
| Feature at max PSI | `velocity_4w` |
| Month pair at max PSI | 0→1 |
| Features with PSI ≥ 0.1 in ≥1 adjacent pair | **23 of 28** |
| Drift classification of max-PSI feature | significant (≥ 0.25) |
| KS statistic (`velocity_4w`, 0→1) | 0.825 |
| Importance share of drifted features | 18.84% |
| Top-5 importance features that drifted | 1 of 5 |

Per-pair max PSI:

| Pair | Max PSI | Feature |
|---|---:|---|
| 0→1 | 3.9429 | `velocity_4w` |
| 1→2 | 0.5107 | `velocity_4w` |
| 2→3 | 3.0454 | `velocity_4w` |
| 3→4 | 0.9611 | `velocity_4w` |
| 4→5 | 1.6714 | `velocity_4w` |
| 5→6 | 0.5549 | `velocity_4w` |
| 6→7 | 3.3890 | `velocity_4w` |

### Result

Feature drift is measurable month-over-month and large. The maximum
PSI is 3.9429 on `velocity_4w` between months 0 and 1, far above the
0.1 kill threshold. 23 of 28 features cross PSI ≥ 0.1 in at least one
adjacent pair. The cross-reference against the V1 classifier's LR
importances shows drift is concentrated on low-importance features:
the drifted features together carry 18.84% of importance, only 1 of
the top-5 importance features (`payment_type`, PSI 0.1730) drifted, and
the largest-magnitude drift (`velocity_4w`, PSI 3.94) carries 0.49%
importance.

### Verdict

**SURVIVED.**

### Interpretation

The static-split assumption is challenged but not broken. Drift is
real and measurable; the features the LR classifier relies on most are
the least drifted. A monitoring component has signal to detect.

### Consequence

Drift detection enters Phase B scope. `docs/v2/protocols/monitoring.md`
is written before `src/monitoring/drift_detector.py` (per
`falsification_plan.md` §3 H4 "If survives").

### Amends V1?

**Yes — Limitations section.** A drift note is added recording 23/28
features drifted, concentrated on low-importance features, one top-5
feature (`payment_type`) with moderate drift.

---

## H5 — Group Disparity — KILLED

### Setup

- **Evaluation window:** V1's frozen `action_log.parquet` (test window)
- **Data:** V1's frozen decisions joined with grouping attributes
- **Groupings tested:** `customer_age` (pre-registered bins),
  `employment_status`, `housing_status`
- **Sample-size guard:** groups with n < 500 excluded from disparity
  calculation
- **Pre-registered kill criterion:** max block-rate disparity < 5
  percentage points

### Metrics

| Grouping | Block-rate disparity | Review-rate disparity |
|---|---:|---:|
| `customer_age` | **2.26pp** | 15.46pp |
| `employment_status` | 1.36pp | 11.73pp |
| `housing_status` | 1.76pp | 33.18pp |

Max block-rate disparity overall: **2.26pp** (`customer_age`).

`customer_age` per-group detail:

| Group | n | Block rate | Review rate | Fraud rate |
|---|---:|---:|---:|---:|
| [0–25) | 60,685 | 0.0002 | 0.0327 | 0.0057 |
| [25–35) | 65,618 | 0.0010 | 0.0689 | 0.0100 |
| [35–45) | 59,351 | 0.0031 | 0.1201 | 0.0138 |
| [45–55) | 31,764 | 0.0088 | 0.1873 | 0.0213 |
| [55–65) | 7,796 | 0.0165 | 0.1797 | 0.0345 |
| [65+) | 2,277 | 0.0228 | 0.1717 | 0.0417 |

Groups excluded by the sample-size guard: `CG` (`employment_status`,
n=89), `BF` and `BG` (`housing_status`, n=333 and n=45).

### Result

No grouping produces a block-rate disparity above the 5pp threshold.
The maximum is 2.26pp (`customer_age`). Review-rate disparities are
materially larger (15.46pp / 11.73pp / 33.18pp) but are not the
pre-registered metric and are reported as supporting evidence only.

### Verdict

**KILLED.**

### Interpretation

V1's policy does not produce block-rate disparity above the
pre-registered threshold on any tested grouping. Fairness constraints
are not justified by this diagnostic.

### Consequence

H5 is dropped from scope. No fairness constraint is built. A limitations
note is added to V1's paper. The review-rate observation is recorded as
a pre-registration limitation for future work.

### Amends V1?

**Yes — Limitations section.** A non-finding note is added recording
block-rate disparity below 5pp across all tested groupings, with the
review-rate disparity noted as larger but not pre-registered.

---

## H1 — Capacity-Constrained Decisioning — SURVIVED

### Setup

- **Evaluation window:** V1's frozen test window (227,491 rows)
- **Classifier:** V1's frozen LR (`C=10.0`, `max_iter=1000`); no
  retrain
- **Policy:** V1's argmin policy with capacity constraint applied
- **Ranking rule inside the review band:** descending by
  `min(c_approve, c_block) - c_review` (per the amendment in
  `falsification_plan.md` §11, dated 2026-10-03, before H1 executed)
- **Comparison:** each capacity level vs. strongest V1 baseline
  (LGBM + static 0.5 = 0.017798)
- **Pre-registered kill criterion:** advantage < 5% at any K ≥ 4,550
  (2% of test volume)

### Metrics

| Capacity (K) | K fraction | Policy cost/txn | Advantage | In kill zone | Verdict |
|---:|---:|---:|---:|---|---|
| 2,275 | 1% | — | 41.88% | no | below threshold (excluded from kill) |
| 4,550 | 2% | — | **44.25%** | yes | pass |
| 11,375 | 5% | — | 53.11% | yes | pass |
| 22,750 | 10% | — | 57.91% | yes | pass |
| 45,499 | 20% | — | 57.91% | yes | pass |

Reference numbers: unconstrained policy cost/txn = 0.007491; review band
size = 21,371 (9.39%); strongest baseline = 0.017798.

Minimum advantage in the kill zone: **44.25%**. Margin above the kill
threshold: **39.25pp**.

### Result

The policy advantage remains above 5% at every tested capacity in the
kill zone. At the smallest tested kill-zone capacity (2%, K=4,550) the
advantage is 44.25%. Above ~9.4% capacity the unconstrained advantage
(57.91%) is recovered in full. The policy degrades gracefully:
monotone cost-capacity curve, no discontinuity.

### Verdict

**SURVIVED.**

### Interpretation

V1's unconstrained-review assumption is not load-bearing for the
headline. The advantage survives a 4.7× reduction in review capacity
below the observed band size.

### Consequence

Capacity-aware policy enters Phase B scope.
`docs/v2/protocols/decision_policy_capacity.md` is written before
`src/policy/decide_capacity.py` (per `falsification_plan.md` §3 H1
"If survives"). `configs/policy.yaml` is added with
`capacity_per_window`. `docs/decision_policy.md` §8 moves from
"specification, deferred" to "implemented".

### Amends V1?

**Yes — Limitations section.** A strengthening note records the
advantage envelope: survives 2% capacity (44.25%), 5% (53.11%),
unconstrained (57.91%).

---

## H6 — Stratified Calibration — KILLED

### Setup

- **Evaluation window:** V1's frozen test window
- **Data:** `scored_test.parquet` joined with `action_log.parquet` and
  observed labels
- **Comparison:** per-stratum ECE vs. aggregate ECE
- **Binning:** 10 quantile bins per stratum; equal-width fallback if a
  stratum has < 100 rows with `p_fraud > 0.01`
- **Pre-registered kill criterion:** any action stratum ECE ≥ 0.05

### Metrics

Aggregate reference:

| Quantity | Value |
|---|---:|
| Test-window rows | 227,491 |
| Aggregate ECE | 0.0025 |
| Aggregate Brier | 0.011506 |

Per-stratum:

| Stratum | n | Base rate | p_mean | ECE | Brier |
|---|---:|---:|---:|---:|---:|
| `approve` | 205,395 | 0.6894% | 0.005936 | 0.0011 | 0.006644 |
| `review` | 21,371 | 5.6525% | 0.042183 | 0.0144 | 0.051303 |
| `block` | 725 | 32.6897% | 0.279414 | **0.0600** | 0.215916 |

Max stratum ECE: **0.0600** (`block`).
Ratio max-stratum / aggregate: **24.02×**.
Block stratum as share of test window: **0.32%** (725 / 227,491).

The materiality check — required by `falsification_plan.md` §3 H6's
"If killed" clause — is documented in `findings.md` §3.7 and §5.3. It
bounds the plausible bias on V1's headline advantage below the 5%
threshold that gates causal machinery. The check is not stored in
`h6_stratified_calibration.json`; it is recorded in the findings
reference.

### Result

The block stratum shows ECE = 0.0600, above the 0.05 kill criterion.
The stratum is 725 rows (0.32% of the test window). The materiality
check — required by `falsification_plan.md` §3 H6's "If killed" clause
— is documented in `findings.md` §3.7 and §5.3. It bounds the
plausible bias on V1's headline advantage below the 5% materiality
threshold that would authorize causal machinery.

### Verdict

**KILLED.**

### Interpretation

The direct cost estimate has a measurable miscalibration in the block
stratum, but the stratum is too small for the miscalibration to
materially affect V1's headline. Phase C causal machinery is not
justified.

### Consequence

H6 is dropped from scope. Phase C is skipped per `stop_criteria.md`
§4.3. No IPW, doubly robust, or randomized logging work is authorized.
A limitations note is added to V1's paper. The pre-registration
limitation (no sample-size correction on the stratum-level kill
criterion) is recorded in `docs/v2/cut_list.md` at Phase D.

### Amends V1?

**Yes — Limitations section.** A non-finding note records the block-stratum ECE of 0.0600, the
stratum size, and the bounded-bias conclusion from the materiality
check in `findings.md` §5.3.

---

## H3 — Rolling Retraining — CONFIRMED (FRAGILE)

### Setup

- **Evaluation window:** V1's frozen split structure, months 5 and 6 as
  separate test steps
- **Classifiers:** LR, RF, LGBM retrained at each step
- **Policy:** V1's argmin policy, unchanged
- **Comparison:** classifier selected at each step vs. V1's static LR
- **Pre-registered kill criterion:** model choice flips in either step
- **Verdict format:** binary — Confirmed / Amended
  (`evaluation_framework.md` §8)

### Metrics

Step 1 — target month 5 (train 0–3, val 4):

| Algorithm | Best config | Val cost |
|---|---|---:|
| Logistic Regression | cfg#0 (`C=0.01`) | 0.007411 |
| Random Forest | cfg#2 (400 trees) | 0.007623 |
| LightGBM | cfg#3 (500 trees, lr=0.05) | 0.007109 |

Top gap: 0.000302 → **4.25% relative**. Selected: LR (non-finding,
below 5%). Target cost, rolling LR: 0.007284. Target cost, V1 static
LR: 0.007296. Rolling advantage over V1: **+0.16%**.

Step 2 — target month 6 (train 0–4, val 5):

| Algorithm | Best config | Val cost |
|---|---|---:|
| Logistic Regression | cfg#0 (`C=0.01`) | 0.007241 |
| Random Forest | cfg#2 (400 trees) | 0.007425 |
| LightGBM | cfg#2 (300 trees, lr=0.05) | 0.006951 |

Top gap: 0.000290 → **4.17% relative**. Selected: LR (non-finding,
below 5%). Target cost, rolling LR: 0.007955. Target cost, V1 static
LR: 0.008078. Rolling advantage over V1: **+1.52%**.

Top-gap comparison:

| Split | LGBM-vs-LR gap |
|---|---:|
| V1 static | 1.07% |
| H3 step 1 (m=5) | 4.25% |
| H3 step 2 (m=6) | 4.17% |
| Noise-band threshold | 5.00% |

### Result

LR is selected at both rolling steps. The classifier conclusion is
stable. But the LGBM-vs-LR gap under rolling retraining (4.25% / 4.17%)
is roughly four times larger than V1's single static split (1.07%). Both
rolling steps sit within 0.75pp of the 5% flip threshold.

### Verdict

**CONFIRMED.** The selection stands. The margin is fragile and is
recorded as a fragility note rather than a strong confirmation.

### Interpretation

V1's simplicity-tiebreak selection of LR holds under rolling retraining,
but the margin is thinner than V1's single static split suggested. The
classifier conclusion is stable but closer to flipping than V1 alone
indicated.

### Consequence

H3 is not a Phase B build (`falsification_plan.md` §12.3). A fragility
note is added to V1's classifier-selection subsection.

### Amends V1?

**Yes — Classifier-selection subsection.** A caveat records the
LGBM-vs-LR gap of 4.25% / 4.17% under rolling vs. 1.07% under V1's
static split.

---

## H2 — Multi-Regime Delay (2 Months) — SURVIVED

### Setup

- **Evaluation window:** 2-month delay test window (months 4–5)
- **Classifier:** LR (`C=10.0`, `max_iter=1000`), retrained on the
  2-month training window
- **Policy:** V1's argmin policy, unchanged
- **Comparison:** same baseline set, retrained on the same window
- **Pre-registered kill criterion:** advantage < 5% at 2-month delay

### Metrics

| Quantity | V1 (1-month) | H2 (2-month) |
|---|---:|---:|
| Censoring rate | 9.68% | 20.50% |
| Train rows | 397,039 | 260,060 |
| Val rows | 278,627 | 287,915 |
| Test rows | 227,491 | 247,014 |
| Fraud rate (train) | ~1.10% | 1.0375% |
| Fraud rate (val) | 1.0207% | 0.8996% |
| Fraud rate (test) | 1.2576% | 1.1590% |
| Policy cost/txn | 0.007491 | 0.007289 |
| Strongest baseline | 0.017798 | 0.017386 |
| Advantage | 57.91% | **58.08%** |
| Bootstrap 95% CI | [53.95%, 62.13%] | **[56.35%, 59.72%]** |
| ECE (val) | 0.0033 | 0.0035 |
| Brier (val) | — | 0.008426 |

Per-algorithm best validation cost (H2):

| Algorithm | Config | Val cost |
|---|---|---:|
| Logistic Regression | cfg#3 (`C=10.0`) | 0.006287 |
| Random Forest | cfg#2 (400 trees) | 0.006783 |
| LightGBM | cfg#3 (500 trees, lr=0.05) | 0.006105 |

Selection: LR (non-finding, top gap 2.97% below 5% noise band).

### Result

At 2-month delay, censoring rises from 9.68% to 20.50% and the training
window shrinks from 397,039 to 260,060 rows. The policy advantage is
58.08% with 95% CI [56.35%, 59.72%], above the 5% kill threshold and
marginally wider than V1's 57.91%. The strongest baseline remains
LGBM + static 0.5 (0.017386).

### Verdict

**SURVIVED.**

### Interpretation

Doubling the label delay does not degrade the advantage. The decision-
centric framing is robust to the delay regime tested. V1's single
1-month regime is not load-bearing.

### Consequence

`docs/data_card.md` is extended with multi-regime delay rules. A
robustness subsection is added to V1's paper.

### Amends V1?

**Yes — Limitations section.** A strengthening note records the
delay envelope: the advantage survives a 2-month delay (58.08%).

---

## Appendix A — Cross-Hypothesis Observations

Two patterns span multiple hypotheses and are relevant to V1's paper
and the Phase B builds.

### A.1 LGBM Validation-Cost Pattern

In every test where all three classifiers were evaluated on a validation
window (H2, H3 steps 1 and 2), LightGBM had the lowest validation
realized cost. The noise-band guard selected LR by simplicity tiebreak
in every case.

| Test | LGBM val cost | LR val cost | Gap |
|---|---:|---:|---:|
| V1 static split | 0.005852 | 0.005915 | 1.07% |
| H2 (2-month delay) | 0.006105 | 0.006287 | 2.97% |
| H3 step 1 (m=5) | 0.007109 | 0.007411 | 4.25% |
| H3 step 2 (m=6) | 0.006951 | 0.007241 | 4.17% |

LGBM's validation-cost advantage over LR is larger under rolling
retraining than under V1's static split. Neither rolling step crosses
the 5% flip threshold, but both sit within 0.75pp of it.

### A.2 H5 Pre-Registration Limitation

The pre-registered kill criterion used **absolute block-rate
disparity**. Because the policy blocks only 0.32% of test-window
transactions, the maximum possible absolute block-rate disparity is
bounded. Review-rate disparity — reported as supporting evidence, not
the pre-registered metric — is materially larger. The kill criterion
was applied as written.

### A.3 H6 Pre-Registration Limitation

The pre-registered kill criterion applies at the stratum level without
a sample-size correction. The `block` stratum is 725 rows; ECE over 725
rows with 10 quantile bins has per-bin sampling noise of roughly ±5pp.
The measured ECE (0.0600) sits within that noise band of the 0.05
threshold. The kill criterion was applied as written.

---

## Appendix B — Phase B and Phase C Implications

- **Phase B (depth on survivors).** Bounded by H1 and H4. Two builds:
  capacity-aware policy and drift detector.
- **H3 is not in Phase B scope.** H3 was `confirmed`, which is a paper
  note (fragility margin on classifier selection), not a code build.
- **H5 and H6 are not in Phase B scope.** Both were killed.
- **Phase C is skipped.** H6 was killed, but the materiality check
  documented in `findings.md` §5.3 bounds the bias on V1's headline
  below the 5% threshold that gates causal machinery. No IPW, doubly
  robust, or randomized logging work is authorized.
- **Phase D (communication).** V1's paper receives one V2 subsection;
  `docs/v2/cut_list.md` is written; README is updated; blog post /
  LinkedIn series is published.

---

## Appendix C — V1 Amendment Summary

Per `falsification_plan.md` §7, V1 amendments are dated and recorded.

| H | Amendment | V1 location | Type |
|---|---|---|---|
| H1 | Bounds stated: 44.25% (2% capacity), 53.11% (5%), 57.91% (unconstrained) | Limitations | Strengthening note |
| H2 | Bound stated: 58.08% at 2-month delay | Limitations | Strengthening note |
| H3 | Fragility note: gap 4.25% / 4.17% under rolling vs. 1.07% static | Classifier-selection subsection | Caveat |
| H4 | Drift note: 23/28 drift, concentrated on low-importance; one top-5 (`payment_type`) moderate | Limitations | Caveat |
| H5 | Non-finding note: block-rate disparity < 5pp; review-rate larger but not pre-registered | Limitations | Non-finding |
| H6 | Non-finding note: block-stratum ECE 0.0600; bias bounded below materiality | Limitations | Non-finding |

No amendment overturns V1's headline. Two strengthen it, two record
caveats, two record non-findings.

---

## Appendix D — Definition of Done

- [x] All six hypotheses reported, one section each
- [x] Verdicts transcribed from `falsification_plan.md` §12
- [x] Findings and non-findings reported at the same length
- [x] Every number traces to `reports/v2/intermediate/*.json`
- [x] V1 amendments summarised with dated notes
- [x] Phase B / Phase C implications stated
- [x] No kill criterion modified after results were seen