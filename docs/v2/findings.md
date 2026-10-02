# V2 Findings

> **Repository:** `delayed-label-fraud-decisioning`  
> **Branch:** `v2`  
> **Purpose:** Portfolio / resume — operational extension of the V1 final-project system  
> **Document:** V2 Findings — consolidated data and results reference  
> **Status:** v1.0 — Phase A complete; consolidated reference for the assembled report  
> **Last updated:** 2026-10-03

---

## 0. Purpose and Non-Duplication

This document consolidates **every number produced by V2's Phase A** in a
single reference. It is the document a paper writer, a reviewer, or a
LinkedIn reader cites when they want a specific value.

**Rule:** This document is a **reference**, not a source of truth. The
source of truth for each number is the intermediate JSON file listed in §6.

**Rule:** This document does **not** restate the pre-registration. Kill
criteria live in `falsification_plan.md` §3. Verdicts live in
`falsification_plan.md` §12. The **formal audit trail** — one section per
hypothesis in the evaluation framework §7 format — is
`reports/v2_falsification.md`. This document is the consolidated numbers
view of the same evidence.

**Rule:** Every number in this document traces to a JSON file under
`reports/v2/intermediate/`. If a number is not in the JSON, it does not
appear here.

---

## 1. Executive Summary

V2 tested six falsifiable hypotheses about whether V1's 57.91% cost
advantage survives operational reality. Three survived, one confirmed
(with a fragility note), and two were killed as non-findings.

**Headline result:** V1's headline is **not overturned** by any V2 test.
It is **strengthened** by H1 (capacity-robust) and H2 (delay-robust),
**confirmed-with-fragility** by H3, and **challenged-but-not-broken** by
H4. Two proposed concerns (H5, H6) were tested and dismissed.

**Phase B is bounded by H1 and H4.** Two builds earn Phase B scope:
capacity-aware policy and drift detector. **Phase C is skipped** — H6's
materiality check bounds the bias on V1's headline to ~2.1%, below the 5%
threshold that authorizes causal machinery.

---

## 2. The Six Verdicts

| ID | Hypothesis | Verdict | Key number |
|---|---|---|---|
| H1 | Policy advantage stays >5% at plausible review capacity | **survived** | 44.25% advantage at K=4,550 (2% capacity) |
| H2 | Policy advantage stays >5% at 2-month delay | **survived** | 58.08% advantage, CI [56.35%, 59.72%] |
| H3 | LR still wins under rolling monthly retraining | **confirmed** (fragile) | LR both steps; gap 4.25% / 4.17% (V1: 1.07%) |
| H4 | Feature drift measurable month-over-month | **survived** | max PSI 3.94; 23/28 features drift |
| H5 | Block rate differs >5pp across protected groups | **killed** | max block-rate disparity 2.26pp < 5pp |
| H6 | Direct cost estimate not materially confounded | **killed** (immaterial) | block stratum ECE 0.0600; bias ~2.1% |

---

## 3. Consolidated Numbers

Every V2 number in one table. Sources identified by hypothesis ID.

### 3.1 V1 Reference Numbers

| Quantity | Value | Source |
|---|---:|---|
| V1 policy cost/txn (unconstrained, 1-month delay) | 0.007491 | V1 `decision_backtest.md` |
| V1 strongest baseline (LGBM+0.5, unconstrained) | 0.017798 | V1 `decision_backtest.md` |
| V1 advantage | 57.91% | V1 `decision_backtest.md` |
| V1 bootstrap CI | [53.95%, 62.13%] | V1 `bootstrap.md` |
| V1 aggregate ECE (validation) | 0.0033 | V1 `calibration.py` |
| V1 classifier selection gap (LGBM vs. LR) | 1.07% | V1 `cv_results.json` |
| V1 test-window rows | 227,491 | V1 `decision_backtest.md` |
| V1 review band size | 21,371 (9.39%) | V1 `action_log.parquet` |
| V1 action distribution | 205,395 / 21,371 / 725 | V1 `decision_backtest.md` |

### 3.2 H1 — Capacity-Constrained Decisioning

| Quantity | Value |
|---|---:|
| Test-window rows | 227,491 |
| Unconstrained policy cost/txn (reference) | 0.007491 |
| Review band size | 21,371 (9.39%) |
| Strongest baseline (LGBM+0.5) | 0.017798 |
| Kill zone threshold | K ≥ 4,550 |
| Advantage at K=2,275 (1%) | 41.88% |
| Advantage at K=4,550 (2%, kill zone begins) | **44.25%** |
| Advantage at K=11,375 (5%) | 53.11% |
| Advantage at K=22,750 (10%) | 57.91% (unconstrained) |
| Advantage at K=45,499 (20%) | 57.91% (unconstrained) |
| Minimum advantage in kill zone | 44.25% |
| Margin above kill threshold | 39.25pp |

### 3.3 H2 — Multi-Regime Delay (2 months)

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
| Bootstrap CI | [53.95%, 62.13%] | **[56.35%, 59.72%]** |
| ECE (validation) | 0.0033 | 0.0035 |
| Brier (validation) | — | 0.008426 |

**Per-algorithm best validation cost (H2):**

| Algorithm | Config | Val cost |
|---|---|---:|
| Logistic Regression | cfg#3 (`C=10.0`) | 0.006287 |
| Random Forest | cfg#2 (400 trees) | 0.006783 |
| LightGBM | cfg#3 (500 trees, lr=0.05) | 0.006105 |

Selection: LR (non-finding, top gap 2.97%, below 5% noise band).

### 3.4 H3 — Rolling Retraining

**Step 1 — target month 5 (train 0–3, val 4):**

| Algorithm | Best config | Val cost |
|---|---|---:|
| Logistic Regression | cfg#0 (`C=0.01`) | 0.007411 |
| Random Forest | cfg#2 (400 trees) | 0.007623 |
| LightGBM | cfg#3 (500 trees, lr=0.05) | 0.007109 |

- Top gap: 0.000302 → **4.25% relative**
- Selected: LR (non-finding, below 5%)
- Target cost, rolling LR: 0.007284
- Target cost, V1 static LR: 0.007296
- Rolling advantage over V1: +0.16%

**Step 2 — target month 6 (train 0–4, val 5):**

| Algorithm | Best config | Val cost |
|---|---|---:|
| Logistic Regression | cfg#0 (`C=0.01`) | 0.007241 |
| Random Forest | cfg#2 (400 trees) | 0.007425 |
| LightGBM | cfg#2 (300 trees, lr=0.05) | 0.006951 |

- Top gap: 0.000290 → **4.17% relative**
- Selected: LR (non-finding, below 5%)
- Target cost, rolling LR: 0.007955
- Target cost, V1 static LR: 0.008078
- Rolling advantage over V1: +1.52%

**Comparison of top gaps:**

| Split | LGBM-vs-LR gap |
|---|---:|
| V1 static | 1.07% |
| H3 step 1 (m=5) | 4.25% |
| H3 step 2 (m=6) | 4.17% |
| Noise-band threshold | 5.00% |

Both rolling steps sit within 0.75pp of the flip threshold.

### 3.5 H4 — Feature Drift

**Max PSI per month pair:**

| Pair | Max PSI | Feature |
|---|---:|---|
| 0→1 | 3.9429 | `velocity_4w` |
| 1→2 | 0.5107 | `velocity_4w` |
| 2→3 | 3.0454 | `velocity_4w` |
| 3→4 | 0.9611 | `velocity_4w` |
| 4→5 | 1.6714 | `velocity_4w` |
| 5→6 | 0.5549 | `velocity_4w` |
| 6→7 | 3.3890 | `velocity_4w` |

Max PSI overall: **3.9429** (`velocity_4w`, months 0→1).

**Distributional shift of `velocity_4w` (months 0→1):**

| Statistic | Month 0 | Month 1 | Change |
|---|---:|---:|---:|
| Mean | 6,189.18 | 5,392.22 | −796.96 |
| Median | 6,343.59 | 5,446.32 | −897.27 |
| p10 | 5,592.52 | 5,145.66 | −446.86 |
| p90 | 6,757.85 | 5,664.64 | −1,093.21 |
| KS statistic | — | — | 0.825 |
| Unique values | 132,383 | 127,549 | — |

**Feature drift classification:**

- 23 of 28 features have PSI ≥ 0.1 in at least one adjacent month pair
- Drift classification: 3 significant (`velocity_4w`, `velocity_24h`,
  `credit_risk_score`, `zip_count_4w` — 4 total), remainder moderate

**Drift vs. feature importance (LR coefficients):**

| Feature | Importance share | Max PSI | Drifted | Drift month pair |
|---|---:|---:|---|---|
| `housing_status` | 19.02% | 0.0857 | no | — |
| `device_os` | 15.00% | 0.0337 | no | — |
| `employment_status` | 14.38% | 0.0247 | no | — |
| `payment_type` | 14.19% | 0.1730 | **yes (moderate)** | 0→1 |
| `source` | 13.10% | 0.0038 | no | — |
| `has_other_cards` | 2.95% | 0.0000 | no | — |
| `phone_home_valid` | 2.82% | 0.0000 | no | — |
| `prev_address_months_count` | 2.16% | 0.0430 | no | — |
| `keep_alive_session` | 2.00% | 0.0000 | no | — |
| `income` | 1.86% | 0.0535 | no | — |
| `name_email_similarity` | 1.84% | 0.1893 | **yes** | 6→7 |
| `email_is_free` | 1.77% | 0.0000 | no | — |
| `credit_risk_score` | 1.44% | 0.2896 | **yes (significant)** | 2→3 |
| `customer_age` | 1.44% | 0.0355 | no | — |
| `bank_months_count` | 1.10% | 0.0923 | no | — |
| `device_distinct_emails_8w` | 1.07% | 0.0232 | no | — |
| `date_of_birth_distinct_emails_4w` | 0.90% | 0.0889 | no | — |
| `zip_count_4w` | 0.53% | 0.2827 | **yes (significant)** | 6→7 |
| `phone_mobile_valid` | 0.52% | 0.0000 | no | — |
| `foreign_request` | 0.52% | 0.0000 | no | — |
| `velocity_4w` | 0.49% | **3.9429** | **yes** | 0→1 |
| `days_since_request` | 0.27% | 0.0478 | no | — |
| `current_address_months_count` | 0.23% | 0.1108 | **yes** | 6→7 |
| `intended_balcon_amount` | 0.18% | 0.0775 | no | — |
| `session_length_in_minutes` | 0.10% | 0.0756 | no | — |
| `velocity_6h` | 0.075% | 0.1657 | **yes** | 0→1 |
| `velocity_24h` | 0.031% | 0.3272 | **yes** | 6→7 |
| `bank_branch_count_8w` | 0.010% | 0.1122 | **yes** | 0→1 |

**Summary:**

- Drifted features combined importance share: 18.84%
- Top-5 importance features drifted: 1 of 5
- Non-top-5 drifted importance share: 4.65%
- Largest-magnitude drift (`velocity_4w`, PSI 3.94) has 0.49% importance
- Largest-importance drifted feature (`payment_type`) is moderate (0.17)

### 3.6 H5 — Group Disparity

**`customer_age` groupings:**

| Group | n | Block rate | Review rate | Fraud rate |
|---|---:|---:|---:|---:|
| [0–25) | 60,685 | 0.0002 | 0.0327 | 0.0057 |
| [25–35) | 65,618 | 0.0010 | 0.0689 | 0.0100 |
| [35–45) | 59,351 | 0.0031 | 0.1201 | 0.0138 |
| [45–55) | 31,764 | 0.0088 | 0.1873 | 0.0213 |
| [55–65) | 7,796 | 0.0165 | 0.1797 | 0.0345 |
| [65+) | 2,277 | 0.0228 | 0.1717 | 0.0417 |

- Block-rate disparity: **2.26pp**
- Review-rate disparity: 15.46pp

**`employment_status` groupings:**

| Group | n | Block rate | Review rate | Fraud rate |
|---|---:|---:|---:|---:|
| CA | 174,600 | 0.0034 | 0.1059 | 0.0137 |
| CB | 24,762 | 0.0006 | 0.0597 | 0.0086 |
| CC | 7,879 | 0.0136 | 0.1310 | 0.0268 |
| CD | 4,329 | 0.0000 | 0.0252 | 0.0028 |
| CE | 5,860 | 0.0000 | 0.0196 | 0.0019 |
| CF | 9,972 | 0.0001 | 0.0136 | 0.0019 |
| CG | 89 | 0.0000 | 0.1573 | 0.0112 |
| *Sample-size guard excluded* | | | | CG |

- Block-rate disparity: **1.36pp**
- Review-rate disparity: 11.73pp

**`housing_status` groupings:**

| Group | n | Block rate | Review rate | Fraud rate |
|---|---:|---:|---:|---:|
| BA | 40,070 | 0.0176 | 0.3477 | 0.0419 |
| BB | 66,113 | 0.0001 | 0.0425 | 0.0066 |
| BC | 71,727 | 0.0002 | 0.0441 | 0.0073 |
| BD | 7,609 | 0.0007 | 0.1024 | 0.0083 |
| BE | 41,594 | 0.0000 | 0.0159 | 0.0038 |
| BF | 333 | 0.0000 | 0.0691 | 0.0000 |
| BG | 45 | 0.0000 | 0.0889 | 0.0000 |
| *Sample-size guard excluded* | | | | BF, BG |

- Block-rate disparity: **1.76pp**
- Review-rate disparity: 33.18pp

**Max block-rate disparity overall: 2.26pp** (`customer_age`).

### 3.7 H6 — Stratified Calibration

**Aggregate reference:**

| Quantity | Value |
|---|---:|
| Test-window rows | 227,491 |
| Aggregate ECE | 0.0025 |
| Aggregate Brier | 0.011506 |

**Per-stratum:**

| Stratum | n | Base rate | p_mean | ECE | Brier |
|---|---:|---:|---:|---:|---:|
| `approve` | 205,395 | 0.6894% | 0.005936 | **0.0011** | 0.006644 |
| `review` | 21,371 | 5.6525% | 0.042183 | **0.0144** | 0.051303 |
| `block` | 725 | 32.6897% | 0.279414 | **0.0600** | 0.215916 |

- Max stratum ECE: **0.0600** (`block`)
- Ratio max stratum / aggregate: **24.02×**
- Kill criterion: any stratum ECE ≥ 0.05 (met by `block`)
- Block stratum as share of test window: **0.32%**
- Block stratum as share of total policy cost: ~2.86%
- Worst-case bias on V1's 57.91% advantage: **~2.1%**
- Materiality threshold for causal machinery: 5%

---

## 4. V1 Headline Status

V1's headline — 57.91% advantage, CI [53.95%, 62.13%] — is **not
overturned** by any V2 test.

| Condition | Advantage | Change vs. V1 |
|---|---:|---:|
| V1 baseline (unconstrained, 1-month delay) | 57.91% | — |
| 2% review capacity (H1) | 44.25% | −13.66pp |
| 5% review capacity (H1) | 53.11% | −4.80pp |
| 10%+ review capacity (H1) | 57.91% | unchanged |
| 2-month delay (H2) | 58.08% | +0.17pp |
| Rolling retraining (H3, rolling LR) | — | LR still selected |

**Interpretation:**

- **Strengthened** by H1: the advantage survives a 4.7× reduction in
  review capacity.
- **Strengthened** by H2: doubling the delay does not degrade the
  advantage; it marginally widens it.
- **Confirmed-with-fragility** by H3: LR still selected, but the
  LGBM-vs-LR gap (4.25% / 4.17%) is 4× larger than V1's single split
  (1.07%). The selection stands but is closer to flipping.
- **Challenged-but-not-broken** by H4: drift exists, but is concentrated
  on low-importance features for the LR classifier. The one drifted
  top-5 feature (`payment_type`) shows only moderate drift.

---

## 5. Cross-Hypothesis Observations

These patterns span multiple hypotheses and are relevant to the paper and
the Phase B builds.

### 5.1 LGBM Validation-Cost Pattern

In every test where all three classifiers were evaluated on a validation
window (H2, H3 steps 1 and 2), LightGBM had the lowest validation
realized cost. In every case, the noise-band guard selected LR by
simplicity tiebreak.

| Test | LGBM val cost | LR val cost | Gap |
|---|---:|---:|---:|
| V1 static split | 0.005852 | 0.005915 | 1.07% |
| H2 (2-month delay) | 0.006105 | 0.006287 | 2.97% |
| H3 step 1 (m=5) | 0.007109 | 0.007411 | 4.25% |
| H3 step 2 (m=6) | 0.006951 | 0.007241 | 4.17% |

**Observation:** LGBM's validation-cost advantage over LR is larger under
rolling retraining than under V1's static split. Neither rolling step
crosses the 5% flip threshold, but both sit within 0.75pp of it.

**Implication:** V1's simplicity-tiebreak selection of LR holds, but the
margin is thinner than the single static split suggested. This is
recorded as a fragility note in V1's paper, not a verdict change.

### 5.2 H5 Pre-Registration Limitation

The pre-registered kill criterion used **absolute block-rate disparity**.
Because the policy blocks only 0.32% of test-window transactions, the
maximum possible absolute block-rate disparity is bounded by 0.32pp×
group count.

Review-rate disparity — reported as supporting evidence, not the
pre-registered metric — is materially larger (15.46pp / 11.73pp /
33.18pp across the three groupings).

**The kill criterion was applied as written.** H5 is killed. The review-
rate observation is recorded as a pre-registration limitation for future
work.

### 5.3 H6 Pre-Registration Limitation

The pre-registered kill criterion applies at the stratum level without a
sample-size correction. The `block` stratum is 725 rows (0.32% of the
test window). ECE computed on 10 quantile bins over 725 rows has per-bin
sampling noise of roughly ±5pp. The measured ECE (0.0600) sits within
that noise band of the 0.05 threshold.

**The kill criterion was applied as written.** H6 is killed. The
materiality check bounds the bias on V1's headline to ~2.1%, below the 5%
threshold for causal machinery. No Phase C work is authorized.

### 5.4 H1 Monotone Cost-Capacity Curve

Policy cost is monotone in capacity with no discontinuity: 0.010344 →
0.009923 → 0.008346 → 0.007491 → 0.007491 as K increases. The policy
degrades gracefully as review tightens.

### 5.5 H1 Diminishing Returns

Marginal cost reduction per additional review:

| K range | Reviews added | Cost reduction |
|---|---:|---:|
| 2,275 → 4,550 | +2,275 | ~4% |
| 4,550 → 11,375 | +6,825 | ~16% |
| 11,375 → 22,750 | +11,375 | ~10% |
| 22,750 → 45,499 | +22,749 | 0% |

Above ~9.4% capacity (the unconstrained review band size), further
capacity adds no value.

---

## 6. Evidence Map

Every number in this document traces to one of the six intermediate JSON
files. This table maps claims to files.

| Hypothesis | JSON file | Contents |
|---|---|---|
| H1 | `reports/v2/intermediate/h1_capacity.json` | Per-capacity cost, advantage, verdict, baselines, kill criterion |
| H2 | `reports/v2/intermediate/h2_delay_2m.json` | 2-month split sizes, per-algorithm val cost, policy cost, baselines, bootstrap CI, ECE |
| H3 | `reports/v2/intermediate/h3_rolling_retrain.json` | Per-step selections, per-algorithm costs, target-month results, fragility gap |
| H4 | `reports/v2/intermediate/h4_drift.json` | Per-feature PSI, per-pair PSI, KS statistics, drift classification |
| H4 | `reports/v2/intermediate/h4_importance_crossref.json` | Drift vs. feature importance |
| H5 | `reports/v2/intermediate/h5_fairness.json` | Per-group block/review/fraud rates, disparities, groupings |
| H6 | `reports/v2/intermediate/h6_stratified_calibration.json` | Per-stratum ECE, Brier, reliability tables, verdict |

---

## 7. What V2 Did Not Find

Two hypotheses were **killed as non-findings**. Both were concerns that,
on investigation, did not require remediation.

### 7.1 No Material Group Disparity in Block Rate

Block-rate disparity across all three tested groupings (customer_age,
employment_status, housing_status) is below the 5pp threshold. The policy
does not produce disparate outcomes above the pre-registered threshold.

### 7.2 No Material Confounding in the Direct Cost Estimate

The stratified calibration check identifies a miscalibration in the
`block` stratum (ECE 0.0600), but the stratum is 0.32% of the test
window and the bounded bias on V1's headline (~2.1%) is below the 5%
materiality threshold. The direct estimate is not materially confounded.

---

## 8. What V2 Changed in V1's Claims

Per `falsification_plan.md` §7, V1 amendments are dated and recorded.

| H | Amendment | V1 paper location | Type |
|---|---|---|---|
| H1 | Bounds stated: advantage survives 2% review capacity (44.25%), 5% (53.11%), unconstrained (57.91%) | Limitations | Strengthening note |
| H2 | Bounds stated: advantage survives 2-month delay (58.08%) | Limitations | Strengthening note |
| H3 | Fragility note: LGBM-vs-LR gap is 4.25%/4.17% under rolling vs. 1.07% under static; selection stands but margin is thinner | Classifier selection subsection | Caveat |
| H4 | Drift note: 23 of 28 features drift; concentrated on low-importance features; one top-5 feature (`payment_type`) shows moderate drift | Limitations | Caveat |
| H5 | Non-finding note: block-rate disparity below 5pp across tested groupings; review-rate disparity is larger but not pre-registered | Limitations | Non-finding |
| H6 | Non-finding note: block-stratum ECE 0.0600; bias bounded below materiality threshold | Limitations | Non-finding |

**No amendment overturns V1's headline.** Two amendments strengthen it,
two record caveats, two record non-findings.

---

## 9. Implications for Phase B and Phase C

### 9.1 Phase B (Depth on Survivors)

Bounded by H1 and H4. Two builds:

1. **Capacity-aware policy** — `docs/v2/protocols/decision_policy_capacity.md`
   then `src/policy/decide_capacity.py` and `configs/policy.yaml`.
2. **Drift detector** — `docs/v2/protocols/monitoring.md` then
   `src/monitoring/drift_detector.py`.

H3 is not in Phase B scope (confirmed, not a build). H5 and H6 are not in
Phase B scope (killed).

### 9.2 Phase C (Causal Evaluation) — Skipped

H6 was killed by its pre-registered criterion, but the materiality check
required by §3 H6's "If killed" clause bounds the bias on V1's headline
to ~2.1%, below the 5% threshold. No IPW, doubly robust, or randomized
logging work is authorized.

### 9.3 Phase D (Communication)

V1's paper receives one V2 subsection summarizing the six verdicts and
the headline-status table in §4 above. `docs/v2/cut_list.md` records what
V2 does not do and why. The two pre-registration limitations (§5.2, §5.3)
are candidates for future-work notes.

---

## 10. Definition of Done for This Document

- [x] All six verdicts recorded (§2)
- [x] Every V2 number consolidated (§3)
- [x] V1 headline status stated with condition-by-condition deltas (§4)
- [x] Cross-hypothesis observations recorded (§5)
- [x] Evidence map to JSON files (§6)
- [x] Non-findings documented (§7)
- [x] V1 amendment summary (§8)
- [x] Phase B / C implications stated (§9)

**Downstream (not blockers for this doc):**

- [ ] `reports/v2_falsification.md` — formal per-hypothesis audit trail
- [ ] `docs/v2/documentation_map.md` — V1→V2 doc status
- [ ] `docs/v2/README.md` — reading order for the folder
- [ ] `docs/v2/cut_list.md` — written at Phase D
- [ ] Phase B builds: capacity-aware policy, drift detector

---

## 11. Changelog

| Date | Change | Reason |
|---|---|---|
| 2026-10-03 | v1.0 — initial findings reference; consolidated all Phase A numbers; cross-hypothesis observations added; V1 amendment summary added; evidence map added | Provide a single reference document for all Phase A numbers, distinct from the per-hypothesis audit trail in `reports/v2_falsification.md` |
