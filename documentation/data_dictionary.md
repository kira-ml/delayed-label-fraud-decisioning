# Data Dictionary

> **Repository:** `delayed-label-fraud-decisioning`  
> **Course:** Introduction to Machine Learning - Final Group Project  
> **Institution:** National University Philippines  
> **Instructor:** Ken Oliver Caparros  
> **Document:** Data Dictionary  
> **Status:** v1.0  
> **Last updated:** 2026-09-23

---

## 1. Purpose

This document is the authoritative reference for every column in the BAF
`Base.csv` dataset as used in this project. It documents column names,
types, allowed values, units, source-time availability, and whether the
column is used as a model feature.

It supplements [`docs/data_card.md`](../docs/data_card.md), which describes
the dataset at a higher level: source, license, splits, delay simulation,
and leakage risks.

**Rule:** If a column's meaning or source-time availability is not in this
document, it is not defined for this project.

---

## 2. Dataset

| Field | Value |
|---|---|
| Name | Bank Account Fraud (BAF) Suite |
| Version | v1 (NeurIPS 2022) |
| Source | Jesus et al., "Turning the Tables: Biased, Imbalanced, Dynamic Tabular Datasets for ML Evaluation," NeurIPS 2022 |
| Source URL | https://arxiv.org/abs/2211.13358 |
| Dataset URL | https://www.kaggle.com/datasets/sgpjesus/bank-account-fraud-dataset-neurips-2022 |
| License | CC BY 4.0 |
| Raw file | `data/original/Base.csv` |
| Rows | 1,000,000 |
| Raw columns | 32 (including target) |
| Unit of analysis | One row = one account application transaction |
| Target | `fraud_bool` |

---

## 3. Column Reference

The table below lists every column in the raw dataset, its dtype, a short
description, its source-time availability, and whether it is used as a
model feature.

**Source-time legend:**
- **Decision** - available when the fraud decision must be made
- **Post-decision** - only known after the decision
- **Derived** - created by the project, not in the raw data

**Feature legend:**
- **Yes** - used by all three primary models
- **No (reason)** - explicitly excluded

### 3.1 Target

| # | Column | Type | Description | Allowed values | Source time | Feature |
|---|---|---|---|---|---|---|
| 1 | `fraud_bool` | int64 | Ground-truth fraud label | 0 = legitimate, 1 = fraud | Post-decision | No (target) |

### 3.2 Applicant and account features

| # | Column | Type | Description | Allowed values | Source time | Feature |
|---|---|---|---|---|---|---|
| 2 | `income` | float64 | Applicant income percentile | 0.1-0.9 | Decision | Yes |
| 3 | `name_email_similarity` | float64 | Similarity between applicant name and email | 0-1 | Decision | Yes |
| 4 | `prev_address_months_count` | int64 | Months at previous address; -1 if unknown | -1 to ~380 | Decision | Yes |
| 5 | `current_address_months_count` | int64 | Months at current address; -1 if unknown | -1 to ~420 | Decision | Yes |
| 6 | `customer_age` | int64 | Applicant age in years | 10-90 (project validates 0-120) | Decision | Yes |
| 7 | `days_since_request` | float64 | Days since the application request | non-negative | Decision | Yes |
| 8 | `intended_balcon_amount` | float64 | Intended balance on the account | can be negative | Decision | Yes |
| 9 | `zip_count_4w` | int64 | Applications from the same ZIP in 4 weeks | non-negative integer | Decision | Yes |
| 10 | `bank_branch_count_8w` | int64 | Transactions at the same branch in 8 weeks | non-negative integer | Decision | Yes |
| 11 | `date_of_birth_distinct_emails_4w` | int64 | Distinct emails linked to the DOB in 4 weeks | non-negative integer | Decision | Yes |
| 12 | `credit_risk_score` | int64 | Internal credit risk score | integer, typically 0-400 | Decision | Yes |
| 13 | `bank_months_count` | int64 | Months with a bank account; -1 if unknown | -1 or non-negative | Decision | Yes |
| 14 | `proposed_credit_limit` | float64 | Requested credit limit | positive float | Decision | No (used as cost input) |

### 3.3 Contact and device features

| # | Column | Type | Description | Allowed values | Source time | Feature |
|---|---|---|---|---|---|---|
| 15 | `email_is_free` | int64 | Whether the applicant email is from a free provider | 0 or 1 | Decision | Yes |
| 16 | `phone_home_valid` | int64 | Whether the home phone number is valid | 0 or 1 | Decision | Yes |
| 17 | `phone_mobile_valid` | int64 | Whether the mobile phone number is valid | 0 or 1 | Decision | Yes |
| 18 | `has_other_cards` | int64 | Whether the applicant has other cards | 0 or 1 | Decision | Yes |
| 19 | `foreign_request` | int64 | Whether the request originated from a foreign IP | 0 or 1 | Decision | Yes |
| 20 | `device_os` | object | Device operating system | `windows`, `macintosh`, `linux`, `other` | Decision | Yes (categorical) |
| 21 | `device_distinct_emails_8w` | int64 | Distinct emails from the device in 8 weeks | non-negative integer | Decision | Yes |
| 22 | `device_fraud_count` | int64 | Number of past fraud events from the device | non-negative integer | Post-decision | No (post-decision risk) |

### 3.4 Behavioral velocity features

| # | Column | Type | Description | Allowed values | Source time | Feature |
|---|---|---|---|---|---|---|
| 23 | `velocity_6h` | float64 | Transaction velocity over the last 6 hours | non-negative float | Decision | Yes |
| 24 | `velocity_24h` | float64 | Transaction velocity over the last 24 hours | non-negative float | Decision | Yes |
| 25 | `velocity_4w` | float64 | Transaction velocity over the last 4 weeks | non-negative float | Decision | Yes |
| 26 | `session_length_in_minutes` | float64 | Length of the application session | non-negative float | Decision | Yes |
| 27 | `keep_alive_session` | int64 | Whether the session used keep-alive | 0 or 1 | Decision | Yes |

### 3.5 Categorical application features

| # | Column | Type | Description | Allowed values | Source time | Feature |
|---|---|---|---|---|---|---|
| 28 | `payment_type` | object | Payment method type | `AA`, `AB`, `AC`, `AD`, `AE` | Decision | Yes (categorical) |
| 29 | `employment_status` | object | Employment status | `CA`, `CB`, `CC`, `CD`, `CE`, `CF`, `CG` | Decision | Yes (categorical) |
| 30 | `housing_status` | object | Housing status | `BA`, `BB`, `BC`, `BD`, `BE`, `BF`, `BG` | Decision | Yes (categorical) |
| 31 | `source` | object | Application source | `INTERNET`, `TELEAPP` | Decision | Yes (categorical) |

### 3.6 Time index

| # | Column | Type | Description | Allowed values | Source time | Feature |
|---|---|---|---|---|---|---|
| 32 | `month` | int64 | Month index of the application | 0-7 | Decision | No (splits only) |

---

## 4. Derived Columns

These columns are created by the project pipeline. They are not in the raw
`Base.csv` file.

### 4.1 `transaction_id`

| Field | Value |
|---|---|
| Type | int64 |
| Created by | `src/data/load.py` |
| Formula | Original row index in `Base.csv` (0 to 999,999) |
| Purpose | Join key across artifacts |
| Used as feature | No (identifier) |

### 4.2 `amount_proxy`

| Field | Value |
|---|---|
| Type | float64 |
| Created by | `src/data/load.py` |
| Formula | Copy of `proposed_credit_limit` |
| Purpose | Cost input for the supplementary policy; not a model feature |
| Used as feature | No (reserved for cost scaling) |
| Note | Real transaction amount is not available in BAF. `proposed_credit_limit` is used as a proxy and documented as a limitation. |

### 4.3 `label_month`

| Field | Value |
|---|---|
| Type | int64 |
| Created by | `src/data/simulate_delay.py` |
| Formula | `month + 1` |
| Purpose | Supplementary delay simulation only |
| Used as feature | No (encodes label delay) |

### 4.4 `observed`

| Field | Value |
|---|---|
| Type | bool |
| Created by | `src/data/simulate_delay.py` |
| Formula | `label_month <= 7` |
| Purpose | Supplementary delay simulation only; marks censored labels |
| Used as feature | No (encodes delay simulation) |

---

## 5. Excluded Columns

The following columns exist in one or more artifacts but are **never** used
as model features. The exclusion list is enforced in code via
`FEATURE_EXCLUDE` in `src/common.py`.

| Column | Reason |
|---|---|
| `transaction_id` | Row identifier; no generalizable signal |
| `fraud_bool` | Target variable |
| `month` | Time index; using it would leak the split |
| `label_month` | Derived from `month`; same leakage risk |
| `observed` | Derived; encodes the delay simulation, not the transaction |
| `amount_proxy` | Reserved as a cost input |
| `proposed_credit_limit` | Duplicate of `amount_proxy`; reserved as a cost input |
| `device_fraud_count` | Post-decision risk field; may include future fraud events |

---

## 6. Final Feature Set

After all exclusions, the model is trained on **28 features**:

- **23 numeric:** `income`, `name_email_similarity`, `prev_address_months_count`, `current_address_months_count`, `customer_age`, `days_since_request`, `intended_balcon_amount`, `zip_count_4w`, `bank_branch_count_8w`, `date_of_birth_distinct_emails_4w`, `credit_risk_score`, `bank_months_count`, `email_is_free`, `phone_home_valid`, `phone_mobile_valid`, `has_other_cards`, `foreign_request`, `device_distinct_emails_8w`, `velocity_6h`, `velocity_24h`, `velocity_4w`, `session_length_in_minutes`, `keep_alive_session`
- **5 categorical:** `payment_type`, `employment_status`, `housing_status`, `source`, `device_os`

Encoding and scaling per algorithm is documented in
[`docs/data_card.md`](../docs/data_card.md) section 11.

---

## 7. Units and Semantics

| Column | Unit |
|---|---|
| `income` | percentile (0.1-0.9) |
| `name_email_similarity` | normalized score (0-1) |
| `prev_address_months_count` | months |
| `current_address_months_count` | months |
| `customer_age` | years |
| `days_since_request` | days |
| `intended_balcon_amount` | currency units (synthetic) |
| `velocity_6h` | transaction count per 6 hours |
| `velocity_24h` | transaction count per 24 hours |
| `velocity_4w` | transaction count per 4 weeks |
| `session_length_in_minutes` | minutes |
| `proposed_credit_limit` | currency units (synthetic) |
| `device_distinct_emails_8w` | distinct emails |
| `bank_branch_count_8w` | transaction count |
| `zip_count_4w` | application count |
| `date_of_birth_distinct_emails_4w` | distinct emails |
| `month` | index (0-7), not a date |

---

## 8. Source and License

- **Dataset:** Bank Account Fraud (BAF) Suite, v1.
- **Paper:** Jesus et al., "Turning the Tables: Biased, Imbalanced, Dynamic
  Tabular Datasets for ML Evaluation," NeurIPS 2022.
- **Source URL:** https://arxiv.org/abs/2211.13358
- **Kaggle URL:** https://www.kaggle.com/datasets/sgpjesus/bank-account-fraud-dataset-neurips-2022
- **License:** CC BY 4.0 (Creative Commons Attribution 4.0 International).
  Academic and non-commercial use permitted with attribution.

---

## 9. Consistency Notes

Two counts in `docs/data_card.md` do not match the code:

| Source | Claimed | Actual |
|---|---|---|
| `data_card.md` section 4.3 | Numeric = 26 | Numeric = 23 |
| `data_card.md` section 11.4 | 29 features | 28 features |

The data card's counts treat `proposed_credit_limit` as a feature and
double-count derived columns. This data dictionary reflects the actual
`FEATURE_EXCLUDE` list in `src/common.py`, which is the source of truth.

To align the data card, update:
- `docs/data_card.md` section 4.3: Numeric `26` -> `23`
- `docs/data_card.md` section 11.4: `29 features` -> `28 features`

---

## 10. Guiding Rule

> If a column is used as a model input but is not documented here as
> decision-time available, the model is relying on data it would not have
> in production. No such column exists in the current build.
