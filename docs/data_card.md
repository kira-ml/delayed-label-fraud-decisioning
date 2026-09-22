# Data Card

> **Repository:** `delayed-label-fraud-decisioning`  
> **Course:** Introduction to Machine Learning — Final Group Project  
> **Institution:** National University Philippines  
> **Instructor:** Ken Oliver Caparros  
> **Document:** Data Card  
> **Status:** v0.3 — aligned with course requirements and three-algorithm comparison  
> **Last updated:** YYYY-MM-DD

---

## 1. Purpose

This document describes the dataset used in the project, its schema, how the
primary classification split is constructed, how label delay is simulated for
the supplementary analysis, and which biases and leakage risks exist.

It exists so that:

- The dataset source, license, and unit of analysis are **explicit**
- The primary classification split is **documented before modeling**
- The supplementary delay simulation assumptions are **falsifiable**
- Leakage risks are **named, not discovered later**
- Any reviewer can reproduce the exact data setup
- Results can be interpreted with the correct caveats

**Rule:** No model result is valid unless the data used to produce it is
documented here.

The complete feature-by-feature schema — names, types, units, allowed values,
and descriptions — is documented in
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
| Storage | `data/original/Base.csv` (course-required layout; legacy path `data/raw/baf/Base.csv` is also accepted) |

**Why chosen:**

- Public, citable, licensed for academic use (CC BY 4.0)
- Designed specifically for fraud detection research (NeurIPS 2022)
- Tabular with mixed numeric and categorical features
- Contains a temporal ordering (`month`) suitable for chronological evaluation
- Manageable size for a student project (1M rows, 32 features)
- Realistic class imbalance (~1.1% fraud)

**Known limitations:**

- Synthetic, not real bank data
- Fraud rate may not match production distributions
- No real chargeback timestamps — delay must be simulated for the
  supplementary analysis
- Month-level granularity only (no day-level timestamps)
- Fraud patterns in the test window drift slightly upward relative to the
  train window (see §6.4)

### 2.2 Secondary Dataset — Not Used

The IEEE-CIS Fraud Detection dataset was considered as an optional secondary
source but is **not used** in this submission. BAF alone is sufficient for the
three-algorithm comparison and the supplementary decision analysis.

---

## 3. Primary Classification Framing

This is the framing used for the course-required three-algorithm comparison.

### 3.1 Prediction Task

```text
Given X_t (features available at transaction time),
predict y_t ∈ {0, 1}   where 1 = fraud
```

This is a standard supervised binary classification problem on tabular data.

### 3.2 Unit of Analysis

One row = one transaction. Each transaction has a unique `transaction_id`
(assigned at load time as the original row index in `Base.csv`).

### 3.3 Intended Users

A fraud operations team that needs a ranked list of high-risk transactions.
The model output (`p_fraud`) is used to prioritize manual review and, in the
supplementary analysis, to drive an automated `approve` / `review` / `block`
decision.

### 3.4 Why Machine Learning Is Appropriate

- The relationship between transaction features and fraud is non-linear and
  involves many weak signals that interact.
- Rule-based systems require constant manual maintenance and do not adapt to
  drift.
- The dataset is large enough (1M rows) to train and validate traditional
  classifiers reliably.
- Prior work in fraud detection has demonstrated that traditional ML models
  (logistic regression, tree ensembles, gradient boosting) achieve strong
  performance on tabular fraud data.

---

## 4. Schema

### 4.1 Post-Load Schema

After `src/data/load.py`, every transaction has this canonical schema.

| Column | Type | Available at decision time? | Role | Notes |
|---|---|---|---|---|
| `transaction_id` | int | Yes | Join key | Original row index in `Base.csv` |
| `month` | int | Yes | Time index | Values 0–7; used for splits only, never as a feature |
| `fraud_bool` | int | No | Target | Ground truth fraud label |
| `amount_proxy` | float | Yes | Cost input | `proposed_credit_limit`; used as a transaction amount proxy |
| `feature_*` | mixed | Yes | Model inputs | Remaining BAF features |
| `label_month` | int | No | Derived | `month + 1`; used only in the supplementary delay analysis |
| `observed` | bool | No | Derived | `label_month <= 7`; used only in the supplementary delay analysis |

### 4.2 Excluded Columns

The following columns are **never** used as model features.

| Column | Reason |
|---|---|
| `transaction_id` | Row identifier; carries no generalizable signal |
| `fraud_bool` | The target |
| `month` | Time index; using it would leak the split |
| `label_month` | Derived from `month`; same leakage risk |
| `observed` | Derived; encodes the delay simulation, not the transaction |
| `amount_proxy` | Reserved as a cost input for the supplementary analysis |
| `device_fraud_count` | Post-decision risk field; may include future fraud events |

The exclusion list is enforced in code via `FEATURE_EXCLUDE` in
`src/common.py`.

### 4.3 Feature Types

| Type | Count | Handling |
|---|---|---|
| Numeric | 26 | Used as-is; scaling applied for Logistic Regression only |
| Categorical | 5 | Encoded per algorithm (see `docs/data_card.md` §11) |
| Identifier | 1 | `transaction_id` excluded |
| Target | 1 | `fraud_bool` excluded from features |
| Time/derived | 4 | `month`, `label_month`, `observed`, `amount_proxy` excluded |

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

Per-split summary statistics are documented in §5.

---

## 5. Primary Classification Split

### 5.1 Split Strategy

The course requires an 80/20 training/testing split unless a justified
alternative is provided. A **chronological split** is used here, which is a
documented justified alternative because:

- Fraud data is temporal; random splits leak future information.
- The dataset includes a `month` index, so chronological ordering is
  available.
- The course explicitly requires chronological splits for time-ordered data:
  "Time ordered data must use a chronological split rather than random
  shuffling."

### 5.2 Split Boundaries

The chronological split is defined as:

| Split | Months | Approximate share | Purpose |
|---|---|---|---|
| Train | 0, 1, 2, 3, 4, 5 | ~80% | Fit model, cross-validation, model selection |
| Test | 6, 7 | ~20% | Final evaluation only, once |

Exact row counts are documented in §5.4.

### 5.3 Cross-Validation

Model selection and hyperparameter tuning use **5-fold time-series
cross-validation** on the training data.

- Folds are contiguous in time (no shuffling).
- Each fold's validation set is strictly after its training set.
- Mean and variability across folds are reported for all three algorithms.
- Preprocessing is fit **within** each fold's training portion to prevent
  leakage.

### 5.4 Row Counts

| Split | Months | Rows | Fraud rate |
|---|---|---:|---:|
| Train | 0, 1, 2, 3, 4, 5 | TBD | TBD |
| Test | 6, 7 | TBD | TBD |
| **Total** | | **1,000,000** | **1.1029%** |

*Rows per month are approximately uniform. Exact counts will be filled in
after the EDA notebook produces the month-by-month breakdown.*

### 5.5 Test Set Discipline

The test set is used **exactly once**, after the best model is selected on
validation. No tuning, threshold selection, or feature decisions are made on
the test set.

---

## 6. Supplementary Label Delay Simulation

This section applies to the supplementary cost-sensitive decision analysis,
not to the primary three-algorithm comparison. It exists to document the
delay simulation used in `reports/mvp_backtest.md`.

### 6.1 Simulation Rule

For each transaction:

```text
decision_time = month
label_time    = month + Δ
```

Δ is fixed per regime, not sampled per transaction.

### 6.2 Delay Regime

BAF exposes month-level granularity only. Day-based regimes (7 / 30 / 90 days)
are not supported by the data. The delay regime is therefore **1 month**.

| Regime | Δ | Purpose |
|---|---|---|
| MVP | 1 month | Single regime run in the current build |

Multiple delay regimes (2-month, 3-month) are documented as future work.

### 6.3 Censoring Rule

A label is **observed** only if:

```text
label_time <= evaluation_end
```

Labels whose `label_time` falls after the cutoff are treated as **censored**,
not as negative.

Treatment of censored labels:

- Excluded from training
- Excluded from evaluation
- Count reported
- Never treated as `y = 0`

### 6.4 Supplementary Split

Under the delay simulation, the split is:

| Split | Months | Rows | Fraud rate |
|---|---|---:|---:|
| Train | 0, 1, 2 | 397,039 | ~1.10% |
| Validation | 3, 4 | 278,627 | 1.0207% |
| Test | 5, 6 | 227,491 | 1.2576% |
| Censored (month 7, never observed) | 7 | 96,843 | — |
| **Observed total** | | **903,157** | |
| **Grand total** | | **1,000,000** | **1.1029%** |

An assertion in `src/data/split.py` verifies
`train + val + test == observed` to guard against off-by-one month boundaries.

**Observed drift:** the test window fraud rate (1.2576%) is slightly higher
than the train window (~1.10%). This is documented as a limitation, not
corrected — correction would amount to tuning on the test set.

### 6.5 Delay Assumptions

- Fraud and non-fraud labels share the same fixed Δ within a regime
- Non-fraud labels are assumed fully observed after `label_time`
- Fraud labels are assumed correct once observed
- Delay is independent of features
- Delay is independent of model decisions

**These assumptions are known to be unrealistic.** They are documented so
the sensitivity of results to each can be tested later. None are resolved
in the current build.

### 6.6 Granularity Verification (Completed)

BAF exposes **month-level granularity only** — no day-level timestamp. Per
`docs/evaluation_protocol.md` §6.3, the delay regime uses the month-based
fallback (1 month). This was resolved before modeling; no day-based regime
is claimed anywhere in the docs.

---

## 7. Leakage Risks

Explicitly named to prevent accidental misuse. Both the primary classification
task and the supplementary decision task are subject to these risks.

| Risk | Description | Mitigation |
|---|---|---|
| Future features | Any feature computed using data after decision time | Feature builder uses only decision-time fields |
| Post-decision fields | Columns that only exist after a decision (e.g. `device_fraud_count`) | Excluded in `FEATURE_EXCLUDE` |
| Target leakage | Columns highly correlated with `fraud_bool` | Audited in EDA; excluded if suspicious |
| Label leakage via delay | Using a label before `label_time` | Enforced by split rules |
| Split leakage | Train/test overlap in time | Chronological split enforced |
| Duplicate leakage | Same transaction appearing in train and test | Deduplicated by `transaction_id` |
| ID leakage | Model memorizes `transaction_id` | `transaction_id` excluded from features |
| Preprocessing leakage | Scaling or encoding statistics computed on test | Preprocessing fit on training folds only |
| Cross-validation leakage | CV folds that mix time boundaries | Time-series CV with contiguous folds |

### 7.1 Feature Audit Checklist

Before any model is trained:

- [ ] Every feature has a documented source time
- [ ] No feature uses `fraud_bool`
- [ ] No feature uses derived delay columns (`label_month`, `observed`)
- [ ] No feature uses post-decision data (`device_fraud_count`)
- [ ] No feature is a proxy for `fraud_bool`
- [ ] `transaction_id` and `month` are excluded
- [ ] Preprocessing is fit on training folds only

---

## 8. Known Biases

| Bias | Description | Impact on Project |
|---|---|---|
| Class imbalance | Fraud is ~1.1% of rows | Metrics must be imbalance-aware (Macro F1) |
| Synthetic data bias | BAF is synthetic | Patterns may not match real fraud |
| Censored labels (supplementary) | Some fraud never reported | Underestimates fraud rate |
| Unreported fraud | Customer does not dispute | Label noise |
| Investigation bias | Investigators focus on certain segments | Labels biased by past policy |
| Selection bias | Only some transactions reach review | Training distribution differs from population |
| Feedback loop | Model decisions change future labels | Observed labels depend on past policy |
| Temporal shift | Fraud patterns change over time | Static splits may overestimate performance |

None of these are solved in the current build. They are named so results can
be interpreted honestly.

---

## 9. Feature Groups

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
| Derived (cost) | `amount_proxy` | Yes | No (reserved for supplementary cost input) |

### 9.1 Amount Usage

`amount_proxy` (derived from `proposed_credit_limit`) is a decision-time
field. It is used in two ways:

- **Supplementary cost input:** to scale `fraud_loss` in the cost-sensitive
  decision policy.
- **Not used as a model feature** in the current build, to keep the
  comparison between the primary classification and the supplementary policy
  clean.

If `amount_proxy` is later added as a feature, this document must be updated
first and the three-algorithm comparison re-run.

---

## 10. Class Imbalance Handling

Fraud is 1.1029% of transactions. This imbalance is addressed through:

### 10.1 Metric Choice

- **Primary metric:** Macro F1 — treats both classes equally and reflects
  the operational cost of both false positives and false negatives
- **Supporting metrics:** per-class precision, recall, F1; confusion matrix;
  ROC-AUC (informational)
- **Forbidden:** raw accuracy as the sole success criterion

### 10.2 Algorithm-Level Handling

| Algorithm | Handling |
|---|---|
| Logistic Regression | `class_weight='balanced'` |
| Random Forest | `class_weight='balanced_subsample'` |
| LightGBM | `is_unbalance=True` (or equivalent scale_pos_weight) |

Exact hyperparameter values are documented in `reports/model_comparison.md`.

### 10.3 Resampling

No oversampling or SMOTE is applied. Class imbalance is handled via class
weights and metric choice. If resampling is added, it must respect time
order and be fit on training folds only.

### 10.4 Threshold Selection

The default classification threshold is 0.5 for the primary comparison. A
non-default threshold may be reported as a sensitivity analysis, but the
default is used for the head-to-head model comparison so that all three
algorithms are evaluated under identical conditions.

---

## 11. Preprocessing Rules

Preprocessing is fit on training data only and applied unchanged to
validation and test data. These rules apply to the primary three-algorithm
comparison.

### 11.1 Missing Values

BAF `Base.csv` has no missing values in the raw data. If missing values are
introduced by downstream processing (e.g. category mismatch), they are
handled per column and documented here.

### 11.2 Categorical Encoding

| Algorithm | Encoding |
|---|---|
| Logistic Regression | One-hot encoding |
| Random Forest | Ordinal encoding (tree splits on categories) |
| LightGBM | Native categorical handling (pandas `category` dtype) |

Category mappings are fit on training folds only.

### 11.3 Numeric Scaling

| Algorithm | Scaling |
|---|---|
| Logistic Regression | StandardScaler (fit on training folds) |
| Random Forest | None required |
| LightGBM | None required |

### 11.4 Feature Selection

All 29 features (32 raw minus 3 excluded: `transaction_id`, `month`,
`fraud_bool`; plus `device_fraud_count`, `amount_proxy`, `label_month`,
`observed` excluded) are retained by default. Feature importance is reported
for tree-based algorithms and may motivate documented removal, but no
feature is dropped without an EDA finding that justifies it.

### 11.5 Pipeline Persistence

The complete preprocessing pipeline (encoders, scalers, feature list) is
saved alongside the best model so that the Streamlit app applies the exact
same transformations used at training time.

---

## 12. Storage and Versioning

| Layer | Path | Committed? |
|---|---|---|
| Raw | `data/raw/baf/Base.csv` | No (gitignored) |
| Interim | `data/interim/` | No (gitignored) |
| Processed | `data/processed/` | No (gitignored) |
| Model | `models/best_model.pkl` | No (gitignored) |
| Preprocessing pipeline | `models/preprocessing.pkl` | No (gitignored) |
| Configs | `configs/` | Yes |
| Split definitions | Documented in this file | Yes |

Raw and processed data are never committed to GitHub. Only code, configs,
documentation, and reports are tracked.

---

## 13. Reproducibility

Every data artifact must be reproducible from:

```text
raw dataset + configs + random seed
```

Requirements:

- Fixed random seed (42) for all stochastic operations
- Fixed split cutoffs
- Fixed cross-validation folds
- Documented library versions
- One command to rebuild all data artifacts

```bash
python -m src.pipeline
```

---

## 14. Definition of Done

### Primary (Course Requirement)

- [ ] BAF dataset downloaded to `data/raw/baf/Base.csv`
- [ ] Dataset source and license documented
- [ ] Data dictionary complete (`documentation/data_dictionary.md`)
- [ ] Chronological 80/20 split defined and saved
- [ ] 5-fold time-series CV folds defined
- [ ] Class imbalance handling documented per algorithm
- [ ] Preprocessing rules documented
- [ ] Leakage audit checklist completed
- [ ] EDA produces summary statistics and month-by-month counts
- [ ] Feature audit completed
- [ ] Data build reproducible with one command

### Supplementary (Project Depth)

- [x] BAF timestamp granularity verified (month-level only)
- [x] Delay regime finalized as month-based (1 month)
- [x] Delay simulator implemented (`simulate_delay.py`)
- [x] Supplementary split produces chronological train / val / test
- [x] Censored label count reported (96,843 / 9.68%)
- [x] Cost config saved to `configs/costs.yaml`

---

## 15. Changelog

| Date | Change | Reason |
|---|---|---|
| YYYY-MM-DD | Initial data card | Project start |
| YYYY-MM-DD | Fixed delay per regime; added granularity check; added per-regime censored reporting | Align with Week 1 MVP |
| YYYY-MM-DD | Reframed primary task as classification with 3-algorithm comparison; added §3, §5, §10; separated primary and supplementary splits; pointed to data dictionary; documented class imbalance handling per algorithm | Align with course requirements |

---

## 16. References

- Jesus et al., "Turning the Tables: Biased, Imbalanced, Dynamic Tabular
  Datasets for ML Evaluation," NeurIPS 2022. *(BAF dataset)*
- Elkan, "The Foundations of Cost-Sensitive Learning," IJCAI 2001.
  *(Cost-sensitive learning)*
- Elkan & Noto, "Learning Classifiers from Only Positive and Unlabeled
  Data," KDD 2008. *(PU learning)*
- Pedregosa et al., "Scikit-learn: Machine Learning in Python," JMLR 2011.
- Ke et al., "LightGBM: A Highly Efficient Gradient Boosting Decision Tree,"
  NeurIPS 2017.

---

## 17. Guiding Rule

> If a dataset property, a split boundary, a feature definition, or a leakage
> risk is not documented here or in the data dictionary, it does not exist in
> this project.
