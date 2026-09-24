# Data Card

> **Repository:** `delayed-label-fraud-decisioning`  
> **Course:** Introduction to Machine Learning — Final Group Project  
> **Institution:** National University Philippines  
> **Instructor:** Ken Oliver Caparros  
> **Document:** Data Card  
> **Status:** v1.0 — first-principles revision; single decision pipeline  
> **Last updated:** 2026-09-24

---

## 0. Derivation From Problem Framing

This document describes the dataset and the data artifacts that the pipeline
in `docs/problem_framing.md` §7 consumes and produces.

**Rule:** No model result is valid unless the data used to produce it is
documented here.

**Rule:** If a dataset property, a split boundary, a feature definition, or a
leakage risk is not documented here or in
`documentation/data_dictionary.md`, it does not exist in this project.

This revision replaces v0.3, which documented two separate splits — a
"primary classification split" (months 0–5 / 6–7) and a "supplementary delay
split" (months 0–2 / 3–4 / 5–6 / censored 7). That separation was inherited
from course deliverables, not from the problem. It is reversed here. There
is **one** split: the chronological, delay-aware split required by
`problem_framing.md` §8.3 and evaluated by `docs/evaluation_protocol.md`
v1.0 §4.

---

## 1. Purpose

This document exists so that:

- The dataset source, license, and unit of analysis are **explicit**
- The single chronological split is **documented before modeling**
- The delay simulation assumptions are **falsifiable**
- Leakage risks are **named, not discovered later**
- Any reviewer can reproduce the exact data setup
- Results can be interpreted with the correct caveats

The complete feature-by-feature schema — names, types, units, allowed
values, and descriptions — is documented in
[`documentation/data_dictionary.md`](../documentation/data_dictionary.md).
This data card focuses on the modeling-relevant subset and the evaluation
design.

---

## 2. Dataset

### 2.1 Primary Dataset — Bank Account Fraud (BAF) Suite

| Field | Value |
|---|---|
| Name | Bank Account Fraud (BAF) Suite |
| Version | v1 (NeurIPS 2022) |
| Source | Jesus et al., "Turning the Tables: Biased, Imbalanced, Dynamic Tabular Datasets for ML Evaluation," NeurIPS 2022 |
| Source URL | https://arxiv.org/abs/2211.13358 |
| Dataset URL | https://www.kaggle.com/datasets/sgpjesus/bank-account-fraud-dataset-neurips-2022 |
| License | CC BY 4.0 |
| Format | CSV |
| Rows | 1,000,000 |
| Raw columns | 32 (including target) |
| Post-load columns | 34 (after adding `transaction_id` and `amount_proxy`) |
| Target | `fraud_bool` (binary: 0 = legitimate, 1 = fraud) |
| Time column | `month`, integer, values 0–7 |
| Time granularity | **Month-level only** — no day-level timestamp |
| Overall fraud rate | 1.1029% |
| Storage | `data/original/Base.csv` (course-required layout) |

**Why chosen, from first principles:**

- It is **temporal** (`month`), which is required for the delay-aware
  evaluation in `problem_framing.md` §8.2.
- It is **imbalanced** (~1.1%), which is realistic for fraud and forces the
  cost asymmetry to matter.
- It is **tabular with mixed types**, matching the domain.
- It has a **legitimate license** (CC BY 4.0) and a **citable source**.
- It is **small enough** to iterate on and **large enough** to train
  reliably.

**Known limitations, named in advance:**

- Synthetic, not real bank data.
- Fraud rate may not match production distributions.
- No real chargeback timestamps. The 1-month delay is simulated.
- Month-level granularity only. Day-based delay regimes are not possible.
- Fraud patterns drift slightly upward across months (documented in §5.3).

### 2.2 Secondary Dataset — Not Used

The IEEE-CIS Fraud Detection dataset was considered as an optional secondary
source but is **not used** in this submission. BAF alone is sufficient for
the classifier comparison and the decision-policy evaluation.

---

## 3. Framing

This section derives from `docs/problem_framing.md` §2. It replaces the
former "Primary Classification Framing" section, which framed the dataset
around a classification task rather than around the decision that the
project exists to make.

### 3.1 Prediction Task

The classifier produces `p = P(fraud | X_t)` at decision time:

```text
Given X_t (features available at transaction time),
produce p_t = P(y_t = 1 | X_t)   where 1 = fraud
```

The classifier is an **input** to the decision policy
(`docs/decision_policy.md`), not the project's product.

### 3.2 Unit of Analysis

One row = one transaction. Each transaction has a unique `transaction_id`
(assigned at load time as the original row index in `Base.csv`).

### 3.3 Intended Users

A fraud operations team that must decide `approve` / `review` / `block` in
real time. The classifier output `p_fraud` feeds a cost-sensitive policy
that produces one action per transaction. The evaluation is of the policy,
not of the classifier alone.

### 3.4 Why Machine Learning Is Appropriate

- The relationship between transaction features and fraud is non-linear and
  involves many weak signals that interact.
- Rule-based systems require constant manual maintenance and do not adapt to
  drift.
- The dataset is large enough (1M rows) to train and validate traditional
  classifiers reliably.
- Prior work in fraud detection has demonstrated that traditional ML models
  (logistic regression, tree ensembles, gradient boosting) achieve strong
  ranking and calibration performance on tabular fraud data.

---

## 4. Schema

### 4.1 Post-Load Schema

After `src/data/load.py`, every transaction has this canonical schema.

| Column | Type | Available at decision time? | Role | Notes |
|---|---|---|---|---|
| `transaction_id` | int | Yes | Join key | Original row index in `Base.csv` |
| `month` | int | Yes | Time index | Values 0–7; used for splits only, never as a feature |
| `fraud_bool` | int | No | Target | Ground truth fraud label |
| `amount_proxy` | float | Yes | Cost input | `proposed_credit_limit`; used as the transaction amount |
| `feature_*` | mixed | Yes | Classifier inputs | Remaining BAF features |
| `label_month` | int | No | Derived | `month + 1`; used only for the delay simulation |
| `observed` | bool | No | Derived | `label_month <= 7`; used only for the delay simulation |

### 4.2 Excluded Columns

The following columns are **never** used as classifier features.

| Column | Reason |
|---|---|
| `transaction_id` | Row identifier; carries no generalizable signal |
| `fraud_bool` | The target |
| `month` | Time index; using it would leak the split |
| `label_month` | Derived from `month`; same leakage risk |
| `observed` | Derived; encodes the delay simulation, not the transaction |
| `amount_proxy` | Reserved as a cost input for the decision policy |
| `proposed_credit_limit` | Duplicate of `amount_proxy`; reserved as a cost input |
| `device_fraud_count` | Post-decision risk field; may include future fraud events |

The exclusion list is enforced in code via `FEATURE_EXCLUDE` in
`src/common.py` and verified by tests.

### 4.3 Feature Types

| Type | Count | Handling |
|---|---|---|
| Numeric | 23 | Used as-is; scaling applied for Logistic Regression only |
| Categorical | 5 | Encoded per classifier (see §10.2) |
| Identifier | 1 | `transaction_id` excluded |
| Target | 1 | `fraud_bool` excluded from features |
| Time / derived / cost | 4 | `month`, `label_month`, `observed`, `amount_proxy` excluded |

The five categorical columns are:

- `payment_type`
- `employment_status`
- `housing_status`
- `source`
- `device_os`

### 4.4 Feature Definitions

The complete feature-by-feature definitions, including units, allowed values,
and source-time availability, are documented in
[`documentation/data_dictionary.md`](../documentation/data_dictionary.md).

The data dictionary is a **required deliverable** and is the authoritative
reference for feature definitions. This section lists only the
modeling-relevant subset.

### 4.5 Summary Statistics

| Statistic | Value |
|---|---|
| Total rows | 1,000,000 |
| Total raw columns | 32 |
| Total post-load columns | 34 |
| Fraud rows | 11,029 (1.1029%) |
| Non-fraud rows | 988,971 (98.8971%) |
| Months | 0–7 (8 values) |
| Rows per month | Approximately 125,000 (uniform) |

Per-split summary statistics are documented in §5.2.

---

## 5. The Single Chronological Split

There is **one** split for the entire project. It is the split required by
`problem_framing.md` §8.3.

### 5.1 Delay Simulation Rule

The split depends on the label delay rule. BAF exposes month-level
granularity only, so the delay regime is fixed at **1 month**:

```text
decision_time = month
label_time    = month + 1
observed      = (label_time <= 7)
```

A transaction in month 7 has `label_time = 8`, which is beyond the dataset.
It is **censored**, not negative.

### 5.2 Split Boundaries

| Split | Months | Rows | Fraud rate | Purpose |
|---|---|---:|---:|---|
| Train | 0, 1, 2 | 397,039 | ~1.10% | Fit classifier and preprocessing |
| Validation | 3, 4 | 278,627 | 1.0207% | Calibration gate, hyperparameter selection |
| Test | 5, 6 | 227,491 | 1.2576% | Policy evaluation, backtest |
| Censored | 7 | 96,843 | — | Excluded from training and evaluation |
| **Observed total** | | **903,157** | | |
| **Grand total** | | **1,000,000** | **1.1029%** | |

An assertion in `src/data/split.py` verifies
`train + val + test == observed`, which guards against off-by-one month
boundaries leaking rows.

### 5.3 Observed Drift

The test-window fraud rate (1.2576%) is slightly higher than the training
window (~1.10%). This is documented as a limitation, not corrected.
Correcting it would amount to tuning on the test window.

### 5.4 Cross-Validation on the Training Window

Hyperparameter selection and diagnostics use **5-fold expanding-window
cross-validation by month** on the training window (train months 0..k,
validate month k+1).

- Folds are contiguous in time (no shuffling).
- Each fold's validation set is strictly after its training set.
- Preprocessing is fit **within** each fold's training portion.
- The selection criterion is **validation realized cost after the policy**
  (`docs/evaluation_protocol.md` §8), not macro F1.

### 5.5 Test-Window Discipline

The test window is used **exactly once**, after the classifier and the
decision policy are frozen. No tuning, threshold selection, calibration, or
feature decision is made on the test window.

---

## 6. Leakage Risks

Explicitly named to prevent accidental misuse.

| Risk | Description | Mitigation |
|---|---|---|
| Future features | Any feature computed using data after decision time | Feature builder uses only decision-time fields |
| Post-decision fields | Columns that only exist after a decision (e.g. `device_fraud_count`) | Excluded in `FEATURE_EXCLUDE` |
| Target leakage | Columns highly correlated with `fraud_bool` | Audited in EDA; excluded if suspicious |
| Label leakage via delay | Using a label before `label_time` | Enforced by split rules |
| Split leakage | Train/validation/test overlap in time | Chronological split enforced |
| Duplicate leakage | Same transaction appearing in more than one split | Deduplicated by `transaction_id` |
| ID leakage | Model memorizes `transaction_id` | `transaction_id` excluded from features |
| Preprocessing leakage | Scaling or encoding statistics computed on validation or test | Preprocessing fit on training folds only |
| Cross-validation leakage | CV folds that mix time boundaries | Expanding-window CV by month only |
| Calibration leakage | Calibration fit on test window | Calibration fit on validation only |
| Cost-rate leakage | `fraud_loss_rate` derived from test-window amounts | Rate derived from training-window amounts only (`docs/decision_policy.md` §7.1) |

### 6.1 Feature Audit Checklist

Before any classifier is trained:

- [ ] Every feature has a documented source time
- [ ] No feature uses `fraud_bool`
- [ ] No feature uses derived delay columns (`label_month`, `observed`)
- [ ] No feature uses post-decision data (`device_fraud_count`)
- [ ] No feature is a proxy for `fraud_bool`
- [ ] `transaction_id` and `month` are excluded
- [ ] Preprocessing is fit on training folds only

---

## 7. Known Biases

| Bias | Description | Impact on Project |
|---|---|---|
| Class imbalance | Fraud is ~1.1% of rows | Evaluation is cost-based; macro F1 reported only as supporting evidence |
| Synthetic data bias | BAF is synthetic | Patterns may not match real fraud |
| Censored labels | Some fraud is never reported | Underestimates fraud rate in the test window |
| Unreported fraud | Customer does not dispute | Label noise |
| Investigation bias | Investigators focus on certain segments | Labels biased by past policy |
| Selection bias | Only some transactions reach review | Training distribution differs from population |
| Feedback loop | Model decisions change future labels | Observed labels depend on past policy |
| Temporal shift | Fraud patterns change over time | Static splits may overestimate performance |

None of these are solved in the current build. They are named so results can
be interpreted honestly.

---

## 8. Feature Groups

| Group | Examples | Available at decision time | Used as feature? |
|---|---|---|---|
| Transaction | `proposed_credit_limit`, `payment_type` | Yes | Yes |
| Customer | `customer_age`, `employment_status` | Yes | Yes |
| Account | `housing_status`, `income` | Yes | Yes |
| Device | `device_os`, `device_fraud_count` | Mixed | `device_os` only; `device_fraud_count` excluded |
| Behavioral | `velocity_*`, `foreign_request` | Yes | Yes |
| Identity | `transaction_id` | Yes | No (excluded) |
| Time | `month` | Yes | No (excluded; used for splits) |
| Outcome | `fraud_bool` | No | No (target) |
| Derived (delay) | `label_month`, `observed` | No | No (excluded) |
| Derived (cost) | `amount_proxy` | Yes | No (reserved as policy cost input) |

### 8.1 Amount Usage

`amount_proxy` (derived from `proposed_credit_limit`) is a decision-time
field. It is used in exactly one way:

- **Cost input:** to scale `fraud_loss` in the decision policy
  (`docs/decision_policy.md` §7).

It is **not used as a classifier feature**. This keeps the classifier's
input free of the cost structure, so the classifier and the policy can be
evaluated independently.

If `amount_proxy` is later added as a feature, this document must be updated
first and the classifier comparison re-run.

---

## 9. Class Imbalance

Fraud is 1.1029% of transactions. The response is:

### 9.1 Metric Choice

- **Primary metric:** realized cost per transaction, after the decision
  policy (`docs/evaluation_protocol.md` §10). This is the project's
  objective.
- **Supporting metrics:** macro F1, per-class precision / recall / F1,
  confusion matrix, ROC-AUC, Brier, ECE. These are reported for context and
  for cross-classifier comparison.
- **Forbidden:** accuracy as the sole success criterion; macro F1 as the
  selection criterion.

### 9.2 Classifier-Level Handling

| Classifier | Handling |
|---|---|
| Logistic Regression | `class_weight='balanced'` |
| Random Forest | `class_weight='balanced_subsample'` |
| LightGBM | **None** — cost asymmetry is handled by the policy, not the training objective |

**Rule:** any weighting that materially distorts calibrated probabilities is
rejected. The decision policy depends on `p` being a real probability, not a
reweighted score (`docs/decision_policy.md` §9). If a weighting improves
ranking but worsens ECE past the gate, the weighting is dropped.

### 9.3 Resampling

No oversampling or SMOTE is applied. Resampling distorts calibration and
complicates temporal validity. If resampling is ever added, it must respect
time order and be fit on training folds only.

### 9.4 Threshold Selection

There is **no classifier threshold**. The classifier produces `p`; the
decision policy produces an action via the argmin rule
(`docs/decision_policy.md` §5.4). The threshold view in
`docs/decision_policy.md` §6 is a diagnostic derived from the cost matrix,
not a tuned parameter.

A static-0.5 baseline is reported for comparison only
(`docs/evaluation_protocol.md` §12). It is not the deployed policy.

---

## 10. Preprocessing Rules

Preprocessing is fit on the training window only and applied unchanged to
validation and test. These rules apply to every classifier in the
comparison.

### 10.1 Missing Values

BAF `Base.csv` has no missing values in the raw data. If missing values are
introduced by downstream processing (e.g. category mismatch), they are
handled per column and documented here.

### 10.2 Categorical Encoding

| Classifier | Encoding |
|---|---|
| Logistic Regression | One-hot encoding |
| Random Forest | Ordinal encoding (tree splits on categories) |
| LightGBM | Native categorical handling (pandas `category` dtype) |

Category mappings are fit on training folds only.

### 10.3 Numeric Scaling

| Classifier | Scaling |
|---|---|
| Logistic Regression | StandardScaler (fit on training folds) |
| Random Forest | None required |
| LightGBM | None required |

### 10.4 Feature Selection

All 28 features (32 raw minus 8 excluded: `transaction_id`, `month`,
`fraud_bool`, `label_month`, `observed`, `amount_proxy`,
`proposed_credit_limit`, `device_fraud_count`) are retained by default.

Feature importance is reported for tree-based classifiers and may motivate a
documented removal, but no feature is dropped without an EDA finding that
justifies it.

### 10.5 Pipeline Persistence

The complete preprocessing pipeline (encoders, scalers, feature list) is
saved alongside the selected classifier so that the Streamlit app applies
the exact same transformations used during training.

---

## 11. Storage and Versioning

| Layer | Path | Committed? |
|---|---|---|
| Raw | `data/original/Base.csv` | No (gitignored) |
| Interim | `data/interim/` | No (gitignored) |
| Processed | `data/processed/` | No (gitignored) |
| Classifier | `models/best_model.pkl` | Yes (whitelisted for Streamlit Cloud) |
| Preprocessing pipeline | `models/preprocessing.pkl` | Yes (whitelisted) |
| Feature metadata | `models/feature_*.json` | Yes (whitelisted) |
| Configs | `configs/` | Yes |
| Split definitions | Documented in this file | Yes |

Raw and processed data are never committed to GitHub. Only code, configs,
documentation, reports, and the specific model artifacts required by the
deployed app are tracked.

---

## 12. Reproducibility

Every data artifact must be reproducible from:

```text
raw dataset + configs + random seed
```

Requirements:

- Fixed random seed (42) for all stochastic operations
- Fixed split cutoffs (defined in §5.2)
- Fixed expanding-window CV folds on the training window
- Documented library versions
- One command to rebuild all data artifacts

```bash
python -m src.pipeline --primary
```

---

## 13. Definition of Done

### 13.1 Data Layer (Implemented)

- [x] BAF dataset downloaded to `data/original/Base.csv`
- [x] Dataset source and license documented
- [x] Data dictionary complete (`documentation/data_dictionary.md`)
- [x] Timestamp granularity verified (month-level only)
- [x] Delay regime finalized as month-based (1 month)
- [x] Delay simulator implemented (`simulate_delay.py`)
- [x] Single chronological split produces train / val / test
- [x] Censored-label count reported (96,843 / 9.68%)
- [x] Split assertion verifies `train + val + test == observed`
- [x] Class imbalance handling documented per classifier
- [x] Preprocessing rules documented
- [x] Leakage audit checklist completed
- [x] Feature audit completed
- [x] Cost config saved to `configs/costs.yaml`
- [x] Data build reproducible with one command

### 13.2 Downstream (Tracked Elsewhere)

- [ ] EDA produces summary statistics and month-by-month counts — tracked
      in `docs/roadmap.md`
- [ ] Calibration gate (ECE < 0.05) run per classifier — tracked in
      `docs/evaluation_protocol.md`
- [ ] Classifier selection by validation realized cost — tracked in
      `docs/evaluation_protocol.md`
- [ ] Final test-window evaluation once — tracked in
      `docs/evaluation_protocol.md`

---

## 14. Changelog

| Date | Change | Reason |
|---|---|---|
| 2026-09-22 | v0.3 — reframed primary task as classification; separated primary and supplementary splits | Align with course deliverables |
| 2026-09-24 | v1.0 — first-principles revision; two-layer split removed; single chronological split (0-2 / 3-4 / 5-6 / censored 7) adopted; macro F1 demoted to supporting evidence; calibration and cost-rate leakage risks added; class imbalance section rewritten around cost-based evaluation; §3 reframed from classification to decision-input role; storage section updated to reflect whitelisted model artifacts; DoD consolidated into Data Layer and Downstream | Derive from `problem_framing.md` v1.0, `evaluation_protocol.md` v1.0, and `decision_policy.md` v1.0 |

---

## 15. References

- Jesus et al., "Turning the Tables: Biased, Imbalanced, Dynamic Tabular
  Datasets for ML Evaluation," NeurIPS 2022. (BAF dataset)
- Elkan, "The Foundations of Cost-Sensitive Learning," IJCAI 2001.
- Elkan & Noto, "Learning Classifiers from Only Positive and Unlabeled
  Data," KDD 2008.
- Pedregosa et al., "Scikit-learn: Machine Learning in Python," JMLR 2011.
- Ke et al., "LightGBM: A Highly Efficient Gradient Boosting Decision
  Tree," NeurIPS 2017.

---

## 16. Guiding Rule

> If a dataset property, a split boundary, a feature definition, or a
> leakage risk is not documented here or in the data dictionary, it does not
> exist in this project.

> There is one split. It is chronological. It is delay-aware. The test
> window is touched once.
