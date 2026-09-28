# MVP: 2-Week Deliverable

> **Repository:** `delayed-label-fraud-decisioning`  
> **Document:** MVP plan for course presentation and submission  
> **Status:** v0.1 — active build plan  
> **Last updated:** 2026-09-22

---
> **Superseded.** This document is the original 2-week MVP plan (v0.1).
> The MVP was built with three deviations: (1) amount-scaled `fraud_loss`
> was adopted instead of deferred; (2) the baseline set is 5 (rule-based
> threshold deferred) rather than 4; (3) ECE, bootstrap CIs, and full cost
> sensitivity were run beyond the original MVP scope. The as-built
> architecture is `mvp_architecture.md` v0.2. This file is retained as the
> original plan and is not the source of truth for what exists in the repo.

## 1. Purpose

This document defines the **minimum viable version** of the project that can be built, evaluated, and presented in **under two weeks**.

It is intentionally smaller than the full project described in `problem_framing.md`, `data_card.md`, `decision_policy.md`, `evaluation_protocol.md`, `architecture.md`, and `roadmap.md`. Those documents remain the plan for the **post-presentation portfolio version**.

**Rule:** If a task is not listed in this document, it is not part of the 2-week MVP.

---

## 2. What This MVP Is

A complete, honest, end-to-end loop:

```text
load BAF → simulate 1-month delay → chronological split → LightGBM
        → cost-sensitive decision policy → cost-based backtest → report
```

The deliverable is a **single comparison table** showing that the cost-sensitive policy produces lower realized cost per transaction than the baselines, under a chronological split with delayed labels.

If the policy does **not** beat the baselines, that is still a valid MVP result and is reported honestly.

---

## 3. Scope

### In scope for the 2-week MVP

- Bank Account Fraud (BAF) Base dataset
- One delay regime: **1 month**
- Chronological train / validation / test split by `month`
- LightGBM binary classifier, default parameters
- Cost-sensitive decision policy with three actions: `approve`, `review`, `block`
- One fixed cost matrix
- Cost-based backtest
- Four baselines
- Censored-label count reported
- Calibration: Brier score only
- One Markdown report
- One command to reproduce the pipeline

### Out of scope for the 2-week MVP

- Multiple delay regimes
- Amount-scaled fraud loss sensitivity
- Capacity simulation
- Rolling evaluation
- Feature engineering beyond raw columns
- Hyperparameter tuning
- Calibration beyond Brier score
- Sensitivity analysis on cost matrix values
- Dashboards
- Streaming infrastructure
- Online learning, PU learning, delayed-label correction
- Deployment of any kind

Each of these is documented as future work in the full project plan. None is required for the presentation.

---

## 4. Dataset

**File:** `data/raw/baf/Base.csv`

**Confirmed properties (verified on load):**

| Property | Value |
|---|---|
| Rows | 1,000,000 |
| Columns | 32 |
| Label | `fraud_bool` |
| Time column | `month`, `int64`, values `0–7` |
| Granularity | Month-level (no day-level timestamps) |
| Fraud rate | ~1.1% |

**Amount-scaled cost sensitivity is not performed** because BAF has no clean transaction amount column. `intended_balcon_amount` contains negative values and cannot be used directly. This is documented as a limitation in the report.

---

## 5. Delay Regime

**Single regime: 1 month.**

Rule:

```text
decision_month = month
label_month    = month + 1
```

A transaction's label is **observed** only if `label_month <= 7` (the last month in the dataset).

Consequences:

- Transactions in month 7 have `label_month = 8`, which is beyond the dataset. These are **censored**, not negative.
- Censored transactions are excluded from training and evaluation.
- Censored count is reported in the final report.

---

## 6. Chronological Split

Train / validation / test by `month`, respecting label maturation:

| Split | Decision month | Label matured by | Notes |
|---|---|---|---|
| Train | 0, 1, 2 | month 3 | 3 months of data |
| Validation | 3, 4 | month 5 | 2 months of data |
| Test | 5, 6 | month 7 | 2 months of data |
| Censored | 7 | never | Excluded, reported |

Rules:

- No shuffling
- No random split
- No oversampling before splitting
- No cross-validation across time boundaries

---

## 7. Model

- **Algorithm:** LightGBM binary classifier
- **Parameters:** library defaults
- **Training:** on train split, early stopping on validation split
- **Output:** `p_fraud` per test transaction
- **Feature set:** all raw columns except `fraud_bool` and `month`

**Excluded features (must be verified during EDA):**

- `device_fraud_count` — may include future fraud events; exclude unless verified as decision-time safe
- Any column that is not available at decision time

**No tuning.** No ensembles. No deep learning.

---

## 8. Decision Policy

Three actions: `approve`, `review`, `block`.

For each transaction, given `p = p_fraud`:

```text
E[cost(approve)] = p * fraud_loss
E[cost(review)]  = review_cost + p * residual_fraud_loss
E[cost(block)]   = (1 - p) * false_positive_cost

action = argmin over {approve, review, block}
```

Fixed cost matrix (relative units):

```yaml
fraud_loss: 1.0
false_positive_cost: 0.1
review_cost: 0.02
residual_fraud_loss: 0.3
```

Derived thresholds (diagnostic only, argmin is the source of truth):

```text
p_review = 0.0286
p_block  = 0.20
```

---

## 9. Baselines

Four baselines. All use the same split, delay regime, and cost matrix.

| # | Baseline |
|---|---|
| 1 | Random decision |
| 2 | Approve-all |
| 3 | Block-all |
| 4 | LightGBM + static threshold (threshold = 0.5) |
| 5 | **Cost-sensitive policy** (the system under test) |

---

## 10. Metrics

Report exactly these. Nothing more.

| Metric | Definition |
|---|---|
| Cost per transaction | Mean realized cost |
| Total cost | Sum of realized cost |
| Fraud dollars saved | Fraud loss avoided vs approve-all |
| Precision@1% | Fraud fraction in top 1% of scores |
| Recall@1% | Fraud captured in top 1% of scores |
| Brier score | Probability calibration |
| Censored-label count | Transactions with `label_month > 7` |
| Censored-label rate | Censored ÷ total test-window transactions |

AUC may be reported but is not the success criterion.

---

## 11. Deliverables

- `reports/mvp_backtest.md` — one comparison table, one interpretation paragraph, one limitations paragraph
- Reproducible pipeline: one command runs data load → training → policy → backtest → report
- Slides for the presentation

No dashboard. No service. No config hash reporting. No stop-criteria appendix.

---

## 12. Day-by-Day Plan

Ten days. Three days of slack.

| Day | Task |
|---|---|
| 1 | Load BAF, confirm schema, write `src/data/load.py` |
| 2 | Simulate 1-month delay, split, verify censored counts |
| 3 | Train LightGBM, save model, score test |
| 4 | Decision policy and action log |
| 5 | Backtest and baselines |
| 6 | Write `reports/mvp_backtest.md` |
| 7 | Buffer — fix whatever broke |
| 8 | Slides: problem → pain point → ML formulation → results → limitations |
| 9 | Practice walkthrough, refine slides |
| 10 | Freeze code, present |

**Rule:** Do not touch code after Day 10. If something is not done by Day 10, it is deferred to post-presentation work.

---

## 13. What "Done" Looks Like at Presentation

You show one table:

| Baseline | Cost/txn | Fraud $ saved | Precision@1% | Recall@1% | Brier |
|---|---|---|---|---|---|
| Random | | | | | |
| Approve-all | | | | | |
| Block-all | | | | | |
| LightGBM + static | | | | | |
| **Cost-sensitive policy** | | | | | |

You then say:

> Fraud decisions must be made before labels arrive. I framed this as a cost-sensitive decision problem, not a classification problem. Under a 1-month delayed-label regime with a chronological split, the cost-sensitive policy achieves a 56.9% reduction in realized cost per transaction vs. the strongest baseline (LightGBM + static 0.5), with a 95% bootstrap CI of [52.8%, 60.9%]. The result survives full cost sensitivity across a 2× range on each cost parameter. Limitations: single delay regime, amount scaling uses `proposed_credit_limit` as a proxy, synthetic data, censored labels excluded. Next steps: additional delay regimes, capacity-aware policy, rule-based baseline.

That is the entire presentation. It is enough.

---

## 14. Success Criteria

The MVP is a success if:

- The pipeline runs end-to-end from one command
- The cost-sensitive policy produces **lower realized cost per transaction** than every baseline
- The result is reported honestly, including:
  - Censored-label counts
  - Brier score
  - Limitations

If the policy does **not** beat all baselines, the MVP is still successful if:

- The pipeline runs
- The result is reported honestly
- The reason for underperformance is explained

A null result reported honestly is a valid final project.

---

## 15. Post-Presentation Expansion

After the presentation and submission, the full project plan resumes:

- Add a second delay regime (2 months)
- Add amount-scaled cost sensitivity (using a proxy column, with caveats)
- Add capacity simulation as a separate experiment
- Add sensitivity analysis on cost matrix values
- Add rolling evaluation
- Add one improvement (calibration, cost-sensitive training, or another measured failure)

The full documentation for these is in:

- `problem_framing.md`
- `data_card.md`
- `decision_policy.md`
- `evaluation_protocol.md`
- `architecture.md` (including stop criteria)
- `roadmap.md`

The MVP does **not** delete these. It defers them.

---

## 16. Relationship to Other Documents

| Document | MVP relationship |
|---|---|
| `problem_framing.md` | Pain point and ML formulation are unchanged. Scope is narrowed. |
| `data_card.md` | MVP uses a subset: one regime, one split. All assumptions remain valid. |
| `decision_policy.md` | MVP uses the full policy as written. |
| `evaluation_protocol.md` | MVP uses a subset of metrics and baselines. |
| `architecture.md` | MVP uses a subset of components. Stop criteria apply only as internal guidance. |
| `roadmap.md` | MVP is Week 1 of the roadmap, further reduced. |

No document is deleted. The MVP is a **strict subset** of the full project.

---

## 17. Guiding Rule

> Build the smallest honest loop that shows the pain point matters, evaluated correctly.  
> Expand only after the presentation.

The MVP is not a compromise. It is the smallest correct version of the project.
