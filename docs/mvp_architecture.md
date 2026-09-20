# MVP Architecture: 2-Week Deliverable

> **Repository:** `delayed-label-fraud-decisioning`  
> **Document:** MVP architecture for the 2-week build  
> **Status:** v0.1 — active build reference  
> **Last updated:** YYYY-MM-DD

---

## 1. Purpose

Define the **minimum end-to-end pipeline** required to produce the deliverable described in `mvp_2_weeks.md`.

This document is a **strict subset** of `architecture.md` v0.3. It drops every component that is not required to produce the MVP report. Anything not listed here is out of scope for the 2-week build.

**Rule:** If a file, schema, or component is not in this document, it is not part of the MVP pipeline.

---

## 2. Pipeline Overview

```mermaid
flowchart LR
    A[Base.csv] --> B[load.py]
    B --> C[transactions.parquet]
    C --> D[simulate_delay.py]
    D --> E[labeled.parquet]
    E --> F[split.py]
    F --> G[train.parquet]
    F --> H[val.parquet]
    F --> I[test.parquet]
    G --> J[train_baseline.py]
    H --> J
    J --> K[model.txt]
    I --> L[score.py]
    K --> L
    L --> M[scored_test.parquet]
    M --> N[decide.py]
    N --> O[action_log.parquet]
    O --> P[backtest.py]
    I --> P
    P --> Q[mvp_backtest.md]
```

That is the entire MVP. Nine scripts, six data artifacts, one model file, one report.

---

## 3. Repository Layout (MVP Only)

```text
delayed-label-fraud-decisioning/
├── README.md
├── docs/
│   ├── mvp_2_weeks.md
│   └── mvp_architecture.md          <- this file
├── configs/
│   └── costs.yaml
├── data/
│   ├── raw/
│   │   └── baf/
│   │       └── Base.csv             # gitignored
│   ├── interim/
│   │   ├── transactions.parquet     # gitignored
│   │   └── labeled.parquet          # gitignored
│   └── processed/
│       ├── train.parquet            # gitignored
│       ├── val.parquet              # gitignored
│       ├── test.parquet             # gitignored
│       ├── scored_test.parquet      # gitignored
│       └── action_log.parquet       # gitignored
├── artifacts/
│   └── model.txt                    # gitignored
├── reports/
│   └── mvp_backtest.md              # committed
└── src/
    ├── pipeline.py
    ├── data/
    │   ├── load.py
    │   ├── simulate_delay.py
    │   └── split.py
    ├── models/
    │   ├── train_baseline.py
    │   └── score.py
    ├── policy/
    │   └── decide.py
    └── evaluation/
        └── backtest.py
```

No `tests/` folder is required for the MVP. If you have time on Day 7, add one test for the policy argmin edge cases.

---

## 4. Data Artifacts and Schemas

Every artifact is a Parquet file except the model and the report. Schemas are frozen for the MVP.

### 4.1 `data/interim/transactions.parquet`

Produced by `load.py`.

| Column | Type | Notes |
|---|---|---|
| `transaction_id` | int | Row index from Base.csv, unique |
| `month` | int | 0–7 |
| `fraud_bool` | int | 0/1 label |
| `amount_proxy` | float | `proposed_credit_limit` (documented proxy) |
| `feature_*` | mixed | All raw BAF features except excluded ones |

**Excluded from features:** `device_fraud_count` (post-decision risk), `fraud_bool` (label), `month` (time index used for splits).

### 4.2 `data/interim/labeled.parquet`

Produced by `simulate_delay.py`. Adds one column to 4.1.

| Column | Type | Notes |
|---|---|---|
| `label_month` | int | `month + 1` |
| `observed` | bool | `label_month <= 7` |

Rows with `observed == False` are censored.

### 4.3 `data/processed/{train,val,test}.parquet`

Produced by `split.py`. Same schema as 4.2, filtered by `month`:

| Split | Months |
|---|---|
| train | 0, 1, 2 |
| val | 3, 4 |
| test | 5, 6 |

Censored rows (`observed == False`) are excluded from all three.

### 4.4 `data/processed/scored_test.parquet`

Produced by `score.py`. Adds one column to test.parquet.

| Column | Type | Notes |
|---|---|---|
| `p_fraud` | float | Model output, in [0, 1] |

### 4.5 `data/processed/action_log.parquet`

Produced by `decide.py`.

| Column | Type | Notes |
|---|---|---|
| `transaction_id` | int | Join key |
| `month` | int | For grouping |
| `p_fraud` | float | Model output |
| `action` | string | `approve` / `review` / `block` |
| `expected_cost_approve` | float | For audit |
| `expected_cost_review` | float | For audit |
| `expected_cost_block` | float | For audit |
| `chosen_expected_cost` | float | Min of the three |
| `reason` | string | Which action won |

Labels are **not** in this file. They are joined in the backtest.

### 4.6 `artifacts/model.txt`

LightGBM model saved via `booster.save_model()`. No pickle. No wrapper.

---

## 5. Configuration

Only one config file is required for the MVP.

### `configs/costs.yaml`

```yaml
fraud_loss: 1.0
false_positive_cost: 0.1
review_cost: 0.02
residual_fraud_loss: 0.3
```

No split config. No delay config. The MVP uses hardcoded values documented here and in `mvp_2_weeks.md`:

- Delay: 1 month
- Split: train 0–2, val 3–4, test 5–6
- Static threshold baseline: 0.5

If you change any of these, update this document first.

---

## 6. Component Specifications

Each component is a single script. Each has one job.

### 6.1 `src/data/load.py`

- **Input:** `data/raw/baf/Base.csv`
- **Output:** `data/interim/transactions.parquet`
- **Does:**
  - Reads Base.csv
  - Adds `transaction_id` = row index
  - Renames nothing; keeps BAF column names
  - Adds `amount_proxy` = `proposed_credit_limit`
  - Sorts by `month` (stable)
  - Writes Parquet
- **Does not:** drop features, impute, encode, split, or model

### 6.2 `src/data/simulate_delay.py`

- **Input:** `data/interim/transactions.parquet`
- **Output:** `data/interim/labeled.parquet`
- **Does:**
  - Adds `label_month = month + 1`
  - Adds `observed = label_month <= 7`
  - Writes Parquet
- **Does not:** sample delay, model delay, join labels

### 6.3 `src/data/split.py`

- **Input:** `data/interim/labeled.parquet`
- **Outputs:** `data/processed/{train,val,test}.parquet`
- **Does:**
  - Filters `observed == True`
  - Train: `month in {0,1,2}`
  - Val: `month in {3,4}`
  - Test: `month in {5,6}`
  - Writes Parquet
  - Prints censored count and rate
- **Does not:** shuffle, resample, or stratify

### 6.4 `src/models/train_baseline.py`

- **Inputs:** `train.parquet`, `val.parquet`
- **Output:** `artifacts/model.txt`
- **Does:**
  - Trains LightGBM binary classifier with defaults
  - Early stopping on validation
  - Saves `booster.save_model('artifacts/model.txt')`
  - Prints train/val AUC and logloss
- **Does not:** tune, ensemble, calibrate

### 6.5 `src/models/score.py`

- **Inputs:** `test.parquet`, `artifacts/model.txt`
- **Output:** `scored_test.parquet`
- **Does:**
  - Loads model
  - Computes `p_fraud`
  - Writes Parquet with `p_fraud` appended
- **Does not:** threshold, decide, log

### 6.6 `src/policy/decide.py`

- **Inputs:** `scored_test.parquet`, `configs/costs.yaml`
- **Output:** `action_log.parquet`
- **Does:**
  - For each row, computes three expected costs
  - Selects argmin
  - Writes action log with all three costs and chosen action
- **Does not:** use thresholds, tune, or apply capacity

### 6.7 `src/evaluation/backtest.py`

- **Inputs:** `action_log.parquet`, `test.parquet`, `configs/costs.yaml`
- **Output:** `reports/mvp_backtest.md`
- **Does:**
  - Joins on `transaction_id`
  - Computes realized cost for the policy
  - Computes realized cost for random, approve-all, block-all, static-0.5
  - Computes precision@1%, recall@1%
  - Computes Brier score on `p_fraud`
  - Reports censored count and rate
  - Writes the report
- **Does not:** bootstrap, sensitivity, calibration curves

### 6.8 `src/pipeline.py`

- **Input:** none
- **Output:** all of the above
- **Does:** runs each step in order with one command

---

## 7. The One Command

```bash
python -m src.pipeline
```

It runs, in order:

1. `load`
2. `simulate_delay`
3. `split`
4. `train_baseline`
5. `score`
6. `decide`
7. `backtest`

If any step fails, the pipeline fails loudly. Do not swallow errors.

---

## 8. Baseline Implementation Details

The four baselines are implemented in `backtest.py`. They use the same `test.parquet` and the same cost matrix.

| Baseline | Implementation |
|---|---|
| Random | `action = random.choice(['approve','review','block'])` per row, seeded |
| Approve-all | `action = 'approve'` for every row |
| Block-all | `action = 'block'` for every row |
| LightGBM + static 0.5 | `action = 'block' if p_fraud >= 0.5 else 'approve'` |

Realized cost per action uses the same cost matrix as the policy:

```text
fraud:   approve -> fraud_loss,    review -> review_cost + residual_fraud_loss,  block -> 0
legit:   approve -> 0,             review -> review_cost,                        block -> false_positive_cost
```

---

## 9. What This MVP Architecture Does Not Include

- No `tests/` folder (optional on Day 7)
- No `configs/splits.yaml`, `configs/delay.yaml`, `configs/policy.yaml`
- No action logging of `cost_config_hash`
- No calibration step
- No amount-scaled cost
- No capacity simulation
- No rolling evaluation
- No config framework, plugin system, or service layer
- No MLflow, DVC, or W&B

Each of these exists in the full `architecture.md` v0.3 and can be added after the presentation.

---

## 10. Build Order

Follow this order. Do not skip ahead.

| Step | Script | Verify |
|---|---|---|
| 1 | `load.py` | `transactions.parquet` has 1,000,000 rows, 33 columns |
| 2 | `simulate_delay.py` | `labeled.parquet` has 2 new columns, observed count printed |
| 3 | `split.py` | train/val/test sizes add to observed total |
| 4 | `train_baseline.py` | val AUC reasonable (> 0.6), model file exists |
| 5 | `score.py` | `scored_test.parquet` has `p_fraud` in [0,1] |
| 6 | `decide.py` | `action_log.parquet` has all three actions present |
| 7 | `backtest.py` | `mvp_backtest.md` has five rows in the table |
| 8 | `pipeline.py` | One command reproduces everything from scratch |

Test each step manually before moving to the next. Do not build all seven and then debug.

---

## 11. Definition of Done (MVP Architecture)

- [ ] `configs/costs.yaml` exists with the four cost keys
- [ ] `src/data/load.py` writes `transactions.parquet`
- [ ] `src/data/simulate_delay.py` writes `labeled.parquet`
- [ ] `src/data/split.py` writes train / val / test parquets
- [ ] `src/models/train_baseline.py` writes `artifacts/model.txt`
- [ ] `src/models/score.py` writes `scored_test.parquet`
- [ ] `src/policy/decide.py` writes `action_log.parquet`
- [ ] `src/evaluation/backtest.py` writes `reports/mvp_backtest.md`
- [ ] `src/pipeline.py` runs all of the above with one command
- [ ] `reports/mvp_backtest.md` contains the five-row comparison table
- [ ] Censored-label count is reported
- [ ] Brier score is reported

When all boxes are checked, the MVP is complete.

---

## 12. Relationship to the Full Architecture

| MVP (`mvp_architecture.md`) | Full (`architecture.md` v0.3) |
|---|---|
| 9 scripts | More components |
| 1 delay regime | 2–3 regimes |
| 5 baselines | 6 baselines |
| Brier only | Brier + ECE + calibration |
| No sensitivity | Sensitivity on costs |
| No stop criteria | Section 9 defines them |
| Hardcoded split | `configs/splits.yaml` |
| No `cost_config_hash` | Full action log schema |

The MVP is a strict subset. Nothing in the MVP contradicts the full architecture; it simply does less.

---

## 13. Guiding Rule

> Build the smallest correct loop. Ship it. Then expand.

If a component is not required to produce `reports/mvp_backtest.md`, it is not in the MVP.
