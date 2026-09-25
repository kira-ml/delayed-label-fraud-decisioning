# Application Guide

> **Repository:** `delayed-label-fraud-decisioning`  
> **Course:** Introduction to Machine Learning - Final Group Project  
> **Institution:** National University Philippines  
> **Instructor:** Ken Oliver Caparros  
> **Document:** Application Guide  
> **Status:** v1.0  
> **Last updated:** 2026-09-23

---

## 1. Purpose

This guide explains how to use the deployed Bank Account Fraud (BAF)
Classifier. It covers:

- The deployed URL and local run command
- The model card and metrics shown in the app
- Batch CSV upload: expected columns, summary, priority worklist
- Manual input: available fields, defaults, output meaning
- Cost-sensitive routing: why the action is not a 0.5 threshold
- Input validation: widget-level and Python-level
- Worked examples: valid, boundary, and invalid inputs
- Known limitations and troubleshooting

It complements:

- [`documentation/data_dictionary.md`](data_dictionary.md) - feature reference
- [`docs/decision_policy.md`](../docs/decision_policy.md) - policy design
- [`docs/data_card.md`](../docs/data_card.md) - dataset and splits

---

## 2. Access

### 2.1 Deployed Application

| Field | Value |
|---|---|
| URL | https://delayed-label-fraud-decisioning-gefp9s9mbkfdyzhhvescdm.streamlit.app |
| Platform | Streamlit Community Cloud |
| Python version | 3.11 |

Open the URL in any modern browser. No login is required.

### 2.2 Local Run

From the repository root:

```bash
streamlit run app/streamlit_app.py
```

The app opens at `http://localhost:8501`.

**Prerequisites:** `requirements.txt` must be installed in an active virtual
environment. See [`documentation/technical_documentation.md`](technical_documentation.md).

### 2.3 Required Files

The app loads these files at startup. If any is missing, the app shows a
red error and stops.

| File | Purpose |
|---|---|
| `models/best_model.pkl` | Selected LightGBM classifier |
| `models/preprocessing.pkl` | Fitted preprocessing pipeline |
| `models/feature_columns.json` | Training-time feature order |
| `models/feature_defaults.json` | Median/mode per feature for manual input |
| `models/feature_importances.json` | Feature importances for the sidebar plot |
| `configs/costs.yaml` | Cost matrix for the decision policy |
| `reports/cv_results.json` | 3-algorithm CV comparison for the sidebar |

---

## 3. Model Card

The sidebar shows the model that is currently deployed.

| Field | Value |
|---|---|
| Algorithm | LightGBM (`LGBMClassifier`) |
| Training window | Months 0-5 of the BAF dataset |
| Test window | Months 6-7 |
| Features | 28 |
| Macro F1 (test) | 0.5336 |
| ROC-AUC (test) | 0.8766 |
| Precision (fraud) | 0.3096 |
| Recall (fraud) | 0.0424 |
| Calibration ECE | 0.0040 |

The sidebar also shows:

- **Cost what-if** - sliders for `false_positive_cost`, `review_cost`,
  `residual_fraud_loss`
- **Derived thresholds** - live `p_review` and `p_block` given the current
  cost matrix
- **3-algorithm comparison** - CV results for Logistic Regression, Random
  Forest, and LightGBM (read from `reports/cv_results.json`)
- **Top feature importances** - top 15 features by gain

---

## 4. Batch Upload Tab

### 4.1 Purpose

Score many transactions at once and get a prioritized worklist.

### 4.2 Input Format

Upload a CSV. Two accepted formats:

**Format A - raw BAF `Base.csv`:**

Contains `proposed_credit_limit`. The app automatically creates
`amount_proxy` from it before scoring.

**Format B - preprocessed:**

Contains `amount_proxy` directly.

Required columns: the 28 model features plus `proposed_credit_limit` (if
Format A). The app checks this and shows an error listing any missing
columns.

### 4.3 Output Sections

After upload, the app renders five sections:

**1. Batch summary**

| Metric | Meaning |
|---|---|
| Rows scored | Number of CSV rows |
| Predicted fraud | Rows where `model.predict == 1`, plus rate |
| Mean fraud probability | Average `p_fraud` across the batch |
| High-risk (p >= 0.5) | Rows with `p_fraud >= 0.5` |
| Est. approve-all cost | Sum of `p_fraud * fraud_loss` across the batch |
| Est. policy cost | Sum of the argmin expected cost across the batch |
| Est. expected savings | Difference, with percentage |

A **drift banner** appears if the batch mean `p_fraud` is far from the
training-window fraud rate (~1.1%). The banner is informational, not an
error.

**2. Review capacity panel**

A slider selects `K` review slots. The panel shows:

- Savings captured by acting on the top-K rows by expected savings
- How many of the top-K rows are `review` and `block` actions

This is a ranking view. It does not re-run the policy.

**3. Prioritized worklist**

Top 50 rows sorted by expected savings. Columns:

`priority_rank`, `transaction_id`, `fraud_probability`, `action`,
`expected_savings`, `chosen_expected_cost`, `expected_cost_approve`,
`expected_cost_review`, `expected_cost_block`

**4. Full predictions download**

A "Download full predictions CSV" button exports all rows with all columns,
including the three expected costs and expected savings.

**5. Segment breakdown**

A dropdown selects a categorical feature (`payment_type`, `employment_status`,
`housing_status`, `source`, `device_os`). The table shows, per segment:

- Row count
- Mean fraud probability
- Action mix (approve / review / block)

---

## 5. Manual Input Tab

### 5.1 Purpose

Score a single transaction by filling out a form.

### 5.2 Exposed Fields

The form exposes four fields. All other features are filled with
training-time medians (numeric) or modes (categorical) so the model receives
a complete feature vector.

| Field | Type | Range / values |
|---|---|---|
| `proposed_credit_limit` | float | >= 0 |
| `customer_age` | int | 0-120 |
| `payment_type` | dropdown | `AA`, `AB`, `AC`, `AD`, `AE` |
| `employment_status` | dropdown | `CA` ... `CG` |

The dropdown values are read from the saved preprocessor, so they always
match the categories the model was trained on.

### 5.3 Output

After clicking **Predict**, the app shows:

| Field | Meaning |
|---|---|
| Action badge | `APPROVE`, `REVIEW`, or `BLOCK` |
| Prediction | `FRAUD` or `LEGITIMATE` (threshold 0.5) |
| Fraud probability | `p_fraud`, in [0, 1] |
| Expected savings vs approve | Difference between approve expected cost and the chosen action's expected cost |

The action is chosen by the argmin of expected cost, not by a 0.5
probability threshold. See Section 6.

---

## 6. Cost-Sensitive Policy

The app does not classify with a fixed 0.5 threshold. It routes each row by
the action with the lowest expected cost.

### 6.1 Formula

For each transaction, with predicted fraud probability `p`:

```
E[cost(approve)] = p * fraud_loss
E[cost(review)]  = review_cost + p * residual_fraud_loss
E[cost(block)]   = (1 - p) * false_positive_cost

action = argmin over {approve, review, block}
```

When `amount_scaled: true` (the default), `fraud_loss` is per-row:

```
fraud_loss(amount) = amount_proxy * fraud_loss_rate
```

### 6.2 Derived Thresholds

For the constant-loss case, the argmin rule is equivalent to two thresholds
on `p`:

| Condition | Action |
|---|---|
| `p < 0.0286` | approve |
| `0.0286 <= p < 0.2000` | review |
| `p >= 0.2000` | block |

These values are shown live in the sidebar **Derived thresholds** panel.
They change when you move the cost what-if sliders.

When `amount_scaled: true`, the review threshold becomes amount-dependent.
The sidebar shows the constant-loss view as a diagnostic. The argmin remains
the source of truth.

### 6.3 Why This Matters

A model with good AUC can still produce poor operational decisions if the
threshold is fixed at 0.5. The cost-sensitive policy ties the decision to the
actual tradeoff between fraud loss, review cost, and false-positive friction.

The **worked example** in Section 8.2 demonstrates this: the same applicant
with the same `p_fraud` is approved for a small amount and routed to review
for a large amount.

---

## 7. Input Validation

The app has two layers of validation.

### 7.1 Widget-Level (Manual Form)

Streamlit number inputs enforce `min_value` and `max_value` at the widget
level. Typing `-1` or `150` into `customer_age`:

- Shows a red border on the widget
- Prevents the invalid value from being submitted
- Does not crash the app
- Does not re-run the form with the invalid value

This is the first line of defense.

### 7.2 Python-Level (`validate_input`)

The `validate_input` function in `app/streamlit_app.py` checks:

1. The DataFrame is not empty
2. All required feature columns are present
3. Categorical columns have no missing values
4. `customer_age` is within `[0, 120]`

This runs on every CSV upload, and on the manual form after the widget has
already filtered out-of-range inputs.

If validation fails, the app displays a red error and does not attempt to
predict.

### 7.3 What the User Sees

| Failure | Message |
|---|---|
| Missing feature column | `Missing required columns: ['payment_type']` |
| Empty input | `Input contains no rows.` |
| Missing categorical value | `Categorical column 'payment_type' contains missing values.` |
| Age out of range | `N rows have customer_age outside [0, 120].` |

The app never displays a Python traceback. All caught errors are rendered
as readable red messages.

---

## 8. Worked Examples

### 8.1 Valid Input - Default Values (Approve)

| Field | Value |
|---|---|
| proposed_credit_limit | 500.00 |
| customer_age | 30 |
| payment_type | AA |
| employment_status | CA |

**Result:**

```
Action: APPROVE
Prediction: LEGITIMATE
Fraud probability: 0.0041
Expected savings vs approve: 0.0000
```

**Why:** `p = 0.0041` is well below `p_review = 0.0286`, so approve is the
argmin. Expected savings is zero because the chosen action is approve itself.

### 8.2 Valid Input - Large Amount (Review)

| Field | Value |
|---|---|
| proposed_credit_limit | 20000.00 |
| customer_age | 30 |
| payment_type | AA |
| employment_status | CA |

**Result:**

```
Action: REVIEW
Prediction: LEGITIMATE
Fraud probability: 0.0041
Expected savings vs approve: 0.1380
```

**Why:** `p` is unchanged. The amount is now 40x larger, so approve expected
cost `0.0041 * 20000 * 0.0019187869 = 0.157` exceeds the review cost `0.02 +
0.0041 * 0.3 = 0.021`. The argmin flips to review.

**This is the primary demonstration of cost-sensitive routing.** Same
applicant, same probability, different action because of amount.

### 8.3 Boundary Input - Age at Upper Limit

| Field | Value |
|---|---|
| proposed_credit_limit | 500.00 |
| customer_age | 120 |
| payment_type | AA |
| employment_status | CA |

**Result:**

```
Action: APPROVE
Prediction: LEGITIMATE
Fraud probability: 0.0096
```

**Why:** 120 is the maximum allowed value for `customer_age`. The app accepts
it and predicts normally.

### 8.4 Invalid Input - Age Below Zero (Widget Blocked)

| Field | Value |
|---|---|
| customer_age | -1 |

**Result:** the `customer_age` widget shows a red border. The form does not
submit. No crash.

### 8.5 Invalid Input - Age Above 120 (Widget Blocked)

| Field | Value |
|---|---|
| customer_age | 150 |

**Result:** same as 8.4. The widget blocks submission.

### 8.6 Invalid CSV - Missing Required Column

Upload a CSV missing the `payment_type` column.

**Result:**

```
Missing required columns: ['payment_type']
```

The app does not attempt to score. No crash.

---

## 9. Limitations

The deployed app inherits every limitation of the underlying model and
dataset. These are documented here so results are not over-interpreted.

| Limitation | Detail |
|---|---|
| Synthetic data | BAF is a synthetic dataset. Results are not production estimates. |
| Amount proxy | `proposed_credit_limit` is used as a transaction amount proxy. It is not a true transaction amount. |
| Single delay regime | The supplementary analysis assumes a 1-month label delay. The deployed classifier does not model delay. |
| Recall at 0.5 | At threshold 0.5, fraud recall is 0.0424. The cost-sensitive policy catches more fraud by using derived thresholds below 0.5. |
| Drift | The test window has a slightly higher fraud rate (~1.40%) than the training window (~1.03%). The app displays a drift banner when a batch mean `p_fraud` is far from the training rate. |
| No capacity constraint | The review capacity panel ranks rows by expected savings but does not enforce a hard cap on the policy. |
| No recalibration | The ECE on validation is 0.0040, so no calibration step was applied. If the model is retrained, recalibration may be warranted. |
| Manual input uses medians | Manual input fills unexposed features with training-time medians or modes. Predictions for sparse manual entries are approximate. |

---

## 10. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Red error "Missing artifact: models/best_model.pkl" on startup | Model file not present | Run `python -m src.pipeline --primary` locally, or push the model files to GitHub for cloud deployment |
| Red error "Missing required columns" on upload | CSV lacks a feature | Check the CSV against the 28 features in `documentation/data_dictionary.md` |
| Prediction fails with a Python error | Preprocessing failed on an unseen category | Reload the page. If it persists, ensure `models/preprocessing.pkl` matches the deployed model |
| Sidebar shows stale test metrics | `reports/model_comparison.md` was updated but the app was not redeployed | Push the commit; Streamlit Cloud rebuilds automatically |
| Streamlit Cloud build fails | Missing package or Python version mismatch | Check `requirements.txt`. The deployed app requires Python 3.11. Do not pin to Python 3.14; some dependencies lack prebuilt wheels. |
| App runs locally but not on Streamlit Cloud | Missing artifact on GitHub | Confirm `git ls-files models/` lists all 5 files |
| Batch upload is slow on 100k+ rows | Model scoring is CPU-bound | The app handles up to the Streamlit Cloud memory limit. Split the CSV into chunks if necessary. |

---

## 11. Data Flow Summary

```
                    +----------------------+
                    |  CSV upload or       |
                    |  manual form         |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    |  validate_input      |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    |  preprocessing.pkl   |
                    |  (transform)         |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    |  best_model.pkl      |
                    |  (predict_proba)     |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    |  cost-sensitive      |
                    |  policy (argmin)     |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    |  action + savings    |
                    |  + worklist          |
                    +----------------------+
```

---

## 12. Related Documents

| Document | Purpose |
|---|---|
| [`documentation/data_dictionary.md`](data_dictionary.md) | Feature reference |
| [`documentation/technical_documentation.md`](technical_documentation.md) | Install, run, and reproduce |
| [`docs/decision_policy.md`](../docs/decision_policy.md) | Policy design and edge cases |
| [`docs/evaluation_protocol.md`](../docs/evaluation_protocol.md) | Metric definitions |
| [`docs/data_card.md`](../docs/data_card.md) | Dataset and splits |
| [`reports/decision_backtest.md`](../reports/decision_backtest.md) | Cost-sensitive policy results |

---

## 13. Guiding Rule

> The app is a decision-support tool, not an autonomous decision-maker. Every
> output should be interpreted with the model card, the derived thresholds,
> and the limitations in Section 9 in view.
