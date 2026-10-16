# Application Guide

> **Repository:** `delayed-label-fraud-decisioning`  
> **Course:** Introduction to Machine Learning - Final Group Project  
> **Institution:** National University Philippines  
> **Instructor:** Ken Oliver Caparros  
> **Document:** Application Guide  
> **Status:** v2.0 (Fraud Decision Desk redesign)  
> **Last updated:** 2026-10-17

---

## 1. Purpose

This guide explains how to use the deployed **Fraud Decision Desk**, the
decision-support app for the Bank Account Fraud (BAF) cost-sensitive policy.
It covers:

- The deployed URL and local run command
- The four tabs: Check one application, Check a batch, How it decides, Study results
- How each decision is explained: stamp, risk scale, and cost slip
- Cost-sensitive routing: why the action is not a 0.5 threshold
- Input validation: widget-level and Python-level
- Worked examples using the app's three built-in example applications
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
| Streamlit version | 1.45 or newer (`requirements.txt`) |

Open the URL in any modern browser. No login is required. Fonts are bundled
with the app (`app/static/fonts/`), so it renders the same without internet
access to font services.

### 2.2 Local Run

From the repository root:

```bash
streamlit run app/streamlit_app.py
```

The app opens at `http://localhost:8501`.

**Prerequisites:** `requirements.txt` must be installed in an active virtual
environment. See [`documentation/technical_documentation.md`](technical_documentation.md).

### 2.3 Required Files

The app loads these files at startup. If a model artifact is missing, the app
shows a red error and stops.

| File | Purpose |
|---|---|
| `models/best_model.pkl` | Selected LogisticRegression classifier |
| `models/preprocessing.pkl` | Fitted preprocessing pipeline |
| `models/feature_columns.json` | Training-time feature order |
| `models/feature_defaults.json` | Median/mode per feature (loaded; not used by the current UI) |
| `models/feature_importances.json` | Top-feature chart in the model card |
| `configs/costs.yaml` | Cost matrix for the decision policy |
| `reports/cv_results.json` | 3-algorithm CV comparison in the model card |
| `sample_500.csv` | The three example applications and the 500-application batch sample |
| `app/static/fonts/` | Bundled fonts (Public Sans, JetBrains Mono, Barlow Condensed) |

---

## 3. Layout

The page has a navy header band with the app name and a one-line summary, then
four tabs. A collapsed sidebar holds the advanced **Cost settings** (Section 6.3).

| Tab | What it is for |
|---|---|
| Check one application | Score one application and see why the desk decided as it did |
| Check a batch | Score a CSV (or the built-in 500-application sample) and get a worklist |
| How it decides | The decision steps in plain words, the formulas, amount-dependent thresholds, and the model card |
| Study results | The paper's results: cost comparison, robustness, and limits |

Every decision is shown as an ink stamp: **APPROVED** (green), **FOR REVIEW**
(ochre), or **BLOCKED** (red). The decision is always written as a word, never
carried by colour alone.

---

## 4. Check One Application Tab

### 4.1 Purpose

Score a single application and explain the decision to a non-technical viewer.

### 4.2 Inputs

1. **Pick an application.** Three real rows from `sample_500.csv`:

   | Example | Row | Application ID | Description |
   |---|---:|---:|---|
   | Everyday | 6 | 903126 | A typical application with a low fraud risk |
   | Unusual | 17 | 903152 | Some warning signs; starts at credit limit 200 |
   | Suspicious | 295 | 795269 | Strong warning signs; labelled fraud in the synthetic dataset |

   All 28 model features come from that real row, so no values are imputed.

2. **Set the requested credit limit.** A slider from 200 to 2,500 in steps of 50.
   The credit limit stands in for the amount at risk (`amount_proxy`).

3. **More application details** (optional, collapsed). Customer age (0–120) and
   the five categorical features (`payment_type`, `employment_status`,
   `housing_status`, `source`, `device_os`). Category codes are anonymised in the
   dataset, so they appear as letter codes.

### 4.3 Output

The right-hand panel shows, top to bottom:

| Element | Meaning |
|---|---|
| Stamp | The decision: APPROVED, FOR REVIEW, or BLOCKED, with today's date. It animates only when the decision changes. |
| Application line | Application ID and the credit limit used |
| Plain-language reason | One sentence explaining the decision with the fraud risk and credit limit |
| Risk-zone scale | The fraud-risk ranges that map to each action **for this credit limit**, with a marker at this application's risk. A zone too narrow to label is named in a note under the scale. |
| Switch note | "Same risk, bigger limit: above about X, this application would be …" when a higher limit would change the action |
| Cost slip | Expected loss of each option (Let it through / Send for a manual check / Block it), in cost units. The cheapest row is marked **CHEAPEST** and is the decision. |

**Cost unit:** 1 unit is the loss from one fraudulent application of average
size (credit limit ≈ 521, from the training months).

---

## 5. Check a Batch Tab

### 5.1 Purpose

Score many applications at once and get a prioritised worklist.

### 5.2 Input

Either:

- Click **Use the 500-application sample** (a slice of the test months with known
  outcomes), or
- Upload a CSV in the format of the study's synthetic BAF data.

Two CSV formats are accepted:

- **Format A, raw BAF `Base.csv`:** contains `proposed_credit_limit`. The app creates
  `amount_proxy` from it before scoring.
- **Format B, preprocessed:** contains `amount_proxy` directly.

Required columns: the 28 model features (plus `proposed_credit_limit` for
Format A). The app lists any missing columns.

### 5.3 Output Sections

1. **Decision mix.** "N sample applications checked", a stacked bar of approved /
   for review / blocked, and a legend with counts and percentages.
2. **Expected loss on this batch (model estimate).** A ledger with the expected
   loss if everyone were approved, the expected loss with the desk, and the
   estimated saving versus approving everyone. These are model estimates; the
   measured study result is on the Study results tab.
3. **Out-of-distribution note.** Shown if the batch's average fraud risk is more
   than three times the training-window fraud rate (~1.03%).
4. **Worklist.** Top 50 applications sorted by expected saving. Columns: Rank,
   Application ID, Decision, Fraud risk, Credit limit, Saving vs approving.
5. **Download all decisions (CSV).** All rows with `fraud_risk`, `decision`,
   `expected_saving`, the three expected costs, `chosen_expected_cost`, and
   `prediction`.
6. **Analyst tools** (collapsed):
   - **Review capacity:** a slider for K, showing the share of total expected
     saving captured by acting on the top K. This is a ranking view and does not
     re-run the policy.
   - **Decisions by segment:** pick a categorical feature to see applications,
     average risk, and the decision mix per segment.

For the 500-application sample under the default costs: **450 approved, 46 for
review, 4 blocked**.

---

## 6. Cost-Sensitive Policy

The app does not classify with a fixed 0.5 threshold. It routes each
application to the action with the lowest expected cost.

### 6.1 Formula

For each application, with predicted fraud probability `p`:

```
E[cost(approve)] = p * fraud_loss
E[cost(review)]  = review_cost + p * residual_fraud_loss
E[cost(block)]   = (1 - p) * false_positive_cost

action = argmin over {approve, review, block}
```

When `amount_scaled: true` (the default), `fraud_loss` is per-row:

```
fraud_loss(amount) = amount_proxy * fraud_loss_rate
fraud_loss_rate    = 1 / 521.1626 = 0.0019187869
```

The **How it decides** tab shows the same formulas under "Show the formulas",
with the current cost values.

### 6.2 Amount-Dependent Thresholds (Diagnostic View)

Because fraud loss grows with the amount, the risk ranges for each action
depend on the credit limit. The **How it decides** tab computes them live from
the cost settings. Under the default costs:

| Credit limit | Let through if risk below | Check if risk between | Block if risk above |
|---:|---:|---:|---:|
| 200 | 20.7% | no check zone | 20.7% |
| 500 | 3.0% | 3.0% to 20.0% | 20.0% |
| 1,000 | 1.2% | 1.2% to 20.0% | 20.0% |
| 1,500 | 0.8% | 0.8% to 20.0% | 20.0% |
| 2,000 | 0.6% | 0.6% to 20.0% | 20.0% |

**This table is a diagnostic view, not the decision rule.** The argmin in §6.1
is the source of truth; the table is computed by evaluating that same argmin
over a grid of probabilities.

### 6.3 Cost Settings (Advanced, Sidebar)

Open the sidebar (arrow at the top left) to adjust:

| Slider | Config key | Default |
|---|---|---:|
| Cost of wrongly blocking a genuine customer | `false_positive_cost` | 0.1 |
| Cost of one manual check | `review_cost` | 0.02 |
| Share of the loss still suffered after a check | `residual_fraud_loss` | 0.3 |

These are what-ifs only. The study froze the cost matrix before modelling;
changing it here is not a new result. All tabs, including the thresholds
table, update live.

### 6.4 Why This Matters

A model with good AUC can still make poor operational decisions with a fixed
0.5 threshold. At a ~1% fraud rate, the model almost never outputs more than
0.5, so a 0.5 cut-off approves nearly everything. The cost-sensitive policy
ties the decision to the actual trade-off between fraud loss, review cost, and
turning away genuine customers.

Worked example 8.2 demonstrates this: the same application, with the same
fraud risk, is approved at a small credit limit and sent for review at a
larger one.

---

## 7. Input Validation

The app has two layers of validation.

### 7.1 Widget-Level

- The credit-limit slider only allows 200 to 2,500.
- **Customer age** (under "More application details") only accepts 0 to 120.
  Out-of-range typed values are rejected by the widget and never reach the model.
- Categorical fields are drop-downs of the values present in the sample data.

### 7.2 Python-Level (`validate_input`)

The `validate_input` function in `app/streamlit_app.py` checks:

1. The DataFrame is not empty
2. All required feature columns are present
3. Categorical columns have no missing values
4. `customer_age` is within `[0, 120]`

This runs on every CSV upload and on every single-application check. If
validation fails, the app shows a red error and does not predict.

### 7.3 What the User Sees

| Failure | Message |
|---|---|
| Unreadable file | `Could not read that file as a CSV: …` |
| Missing feature column | `This file can't be scored yet. Fix these and upload again:` then `Missing required columns: ['payment_type']` |
| Empty input | `Input contains no rows.` |
| Missing categorical value | `Categorical column 'payment_type' contains missing values.` |
| Age out of range | `N rows have customer_age outside [0, 120].` |
| Scoring error | `Scoring failed: <ErrorType>: <message>` |

The app never displays a Python traceback.

---

## 8. Worked Examples

All values below use the default cost settings.

### 8.1 Everyday (Approve)

| Field | Value |
|---|---|
| Example | Everyday (application 903126) |
| Credit limit | 200 |

**Result:** stamp **APPROVED**, fraud risk **1.3%**.

| Option | Expected loss |
|---|---:|
| Let it through | **0.0051** (cheapest) |
| Send for a manual check | 0.0240 |
| Block it | 0.0987 |

The switch note reads: *above about 950, this application would be sent for review.*

### 8.2 Unusual, Then Raise the Limit (Approve → Review)

| Field | Value |
|---|---|
| Example | Unusual (application 903152) |
| Credit limit | 200, then 1,000 |

**At 200:** stamp **APPROVED**, fraud risk **12.5%**. Expected losses: let
through 0.0481 (cheapest), check 0.0576, block 0.0875. The switch note says the
decision changes above about 240.

**At 1,000:** stamp **FOR REVIEW**, fraud risk still **12.5%**.

| Option | Expected loss |
|---|---:|
| Let it through | 0.2404 |
| Send for a manual check | **0.0576** (cheapest) |
| Block it | 0.0875 |

**Why:** the fraud risk does not change. A five-times-larger credit limit makes
the possible loss five times larger, so a manual check becomes cheaper than
letting it through. **This is the primary demonstration of cost-sensitive
routing.**

### 8.3 Suspicious (Block)

| Field | Value |
|---|---|
| Example | Suspicious (application 795269, labelled fraud in the synthetic dataset) |
| Credit limit | 1,500 |

**Result:** stamp **BLOCKED**, fraud risk **29.8%**. Expected losses: let through
0.8570, check 0.1093, block **0.0702** (cheapest).

### 8.4 Batch Sample

Click **Use the 500-application sample** on the Check a batch tab.

**Result:** 450 approved (90.0%), 46 for review (9.2%), 4 blocked (0.8%).

### 8.5 Boundary and Invalid Inputs

| Input | Result |
|---|---|
| Customer age 120 | Accepted; scored normally |
| Customer age -1 or 150 | Rejected by the widget; nothing is scored; no crash |
| CSV missing `payment_type` | `Missing required columns: ['payment_type']`; nothing is scored |

---

## 9. Limitations

The app inherits every limitation of the underlying model and dataset.

| Limitation | Detail |
|---|---|
| Synthetic data | BAF is a synthetic dataset. Results are not production estimates. |
| Amount proxy | `proposed_credit_limit` stands in for the transaction amount. It is not a true transaction amount. |
| Single delay regime | The study assumes a 1-month label delay. The deployed classifier does not model delay. |
| Recall at 0.5 | At threshold 0.5, fraud recall is 0.0063. The cost-sensitive policy routes more fraud to review/block by minimising expected cost rather than applying a fixed threshold. |
| Drift | The test window has a slightly higher fraud rate (1.2576%) than the training window (0.9813%). The batch tab shows a note when a batch's average risk is far from the training rate. |
| No recalibration | The ECE on validation is 0.0033, so no calibration step was applied. If the model is retrained, recalibration may be warranted. |
| Batch estimates are model-based | The batch tab's saving is estimated from predicted probabilities, not from recorded outcomes. The measured result is on the Study results tab. |

---

## 10. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Red error "Missing artifact: models/best_model.pkl" on startup | Model file not present | Run `python -m src.pipeline` locally, or push the model files to GitHub for cloud deployment |
| "Example applications are unavailable" | `sample_500.csv` missing | Restore `sample_500.csv` at the repository root |
| Red error "Missing required columns" on upload | CSV lacks a feature | Check the CSV against the 28 features in `documentation/data_dictionary.md` |
| Plain system fonts instead of the app's fonts | `app/static/fonts/` not deployed | Confirm `git ls-files app/static/fonts` lists the three `.woff2` files |
| App shows the old design after a push | Streamlit Cloud has not rebuilt yet | Wait for the rebuild, or reboot the app from the Streamlit Cloud dashboard |
| Streamlit Cloud build fails | Missing package or Python version mismatch | Check `requirements.txt` (Streamlit ≥ 1.45, Altair ≥ 5). The deployed app requires Python 3.11. |
| App runs locally but not on Streamlit Cloud | Missing artifact on GitHub | Confirm `git ls-files models/` lists all 5 files |
| Batch upload is slow on 100k+ rows | Model scoring is CPU-bound | Split the CSV into chunks if necessary |

---

## 11. Data Flow Summary

```
                    +----------------------+
                    |  Example application |
                    |  or CSV / sample     |
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
                    |  stamp + reason +    |
                    |  cost slip / worklist|
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
| [`DESIGN.md`](../DESIGN.md) | Visual design system of the app |

---

## 13. Guiding Rule

> The app is a decision-support tool, not an autonomous decision-maker. Every
> output should be read together with its stated reason, the cost settings,
> and the limitations in Section 9.
