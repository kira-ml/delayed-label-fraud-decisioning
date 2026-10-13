# Presentation Slides — Delayed-Label Fraud Decisioning

> **Purpose:** This file contains the exact content to place on each PowerPoint slide.
> Copy-paste directly. Do not add paragraphs. Bullets, tables, and diagram
> descriptions only.
>
> **Companion file:** `docs/presentation_notes.md` (speaker notes — not on slides).
>
> **Rule:** Every number here is verified against `docs/main.tex` and the
> pipeline reports. Do not change any figure without re-running the pipeline.

---

## Slide 1 — Title Slide

**Title:**
Cost-Sensitive Fraud Decisioning Under Delayed and Censored Labels

**Subtitle:**
A Temporal Backtest on the Bank Account Fraud Dataset

**Content:**
- Ken Ira Lacson Talingting
- Lawrence Abad
- John Kelly Nogales
- Smith Albert Surio

- College of Computing and Information Technologies
- National University Philippines
- Introduction to Machine Learning — Final Group Project
- October 17, 2026

**Layout:** Centered title slide. No images needed.

---

## Slide 2 — Research Problem

**Title:** The Problem: Decisions Before Labels

**Content (bullets):**
- Payment transactions must be authorized **before** anyone knows if they are fraudulent
- Fraud labels arrive weeks to months later (industry dispute windows: 30–120 days)
- Some fraud is never reported → labels are **censored**, not negative
- Operational question is not "Is this fraud?" but "**What action do we take now?**"
- Most published work reports AUC or PR-AUC — these do not answer the operational question

**Visual:** One timeline diagram below the bullets.

```
Decision (t) ────────────────► Label arrives (t + Δ)
                                    Δ = 30 to 120 days
```

---

## Slide 3 — Research Objectives

**Title:** Research Objectives

**Content (bullets):**
1. Frame fraud detection as a **decision problem**, not a classification problem
2. Evaluate a cost-sensitive policy end-to-end under delayed and censored labels
3. Compare three traditional classifiers **as inputs to the policy**
4. Report realized cost per transaction with a bootstrap confidence interval
5. Test robustness with a sensitivity sweep over cost assumptions
6. Report censored labels honestly rather than treating them as negatives

**Visual:** None. Numbered bullets only.

---

## Slide 4 — Methodology: The Decision Policy

**Title:** Methodology — Decision Policy

**Content (bullets):**
- Three actions available at decision time: `approve`, `review`, `block`
- For each transaction, the policy computes expected cost of each action
- The policy chooses the action with the **minimum expected cost**

**Equations to display:**
```
E[cost(approve)] = p × fraud_loss(amount)
E[cost(review)]  = review_cost + p × residual_fraud_loss
E[cost(block)]   = (1 − p) × false_positive_cost
```

**Where:**
- `p` = calibrated fraud probability from the classifier
- `amount` = transaction amount
- Cost values are frozen **before** any modeling begins

**Visual:** The three equations in a box. Below them, one arrow pointing to: `action* = argmin of the three`.

---

## Slide 5 — Methodology: Cost Matrix & Amount Scaling

**Title:** Methodology — Cost Matrix

**Content — table:**

| Parameter | Value |
|---|---:|
| `fraud_loss` | 1.0 |
| `false_positive_cost` | 0.1 |
| `review_cost` | 0.02 |
| `residual_fraud_loss` | 0.3 |
| `amount_scaled` | true |

**Below the table (bullets):**
- Amount-scaled fraud loss: `fraud_loss(amount) = amount × fraud_loss_rate`
- Rate derived from **training-window amounts only**: `1 / 521.1626 = 0.0019187869`
- **No test-window information** used → no test-set tuning
- Cost matrix frozen before modeling; changing it is a new experiment

**Visual:** Table + two bullets. Do not add charts.

---

## Slide 6 — Methodology: Classifiers & Calibration Gate

**Title:** Methodology — Classifiers and Calibration

**Content (bullets):**
- Three traditional classifiers compared as **policy inputs**:
  - Logistic Regression
  - Random Forest
  - LightGBM
- **Calibration gate:** ECE < 0.05 on the validation window, or the classifier is rejected
- No class weighting applied — it would distort calibrated probabilities
- Cost asymmetry is handled by the **policy**, not the training objective
- The classifier is an **input**; the policy is the **object of study**

**Visual:** Three classifier names in a row, each with a small note:
- Logistic Regression (linear baseline, interpretable)
- Random Forest (non-linear ensemble)
- LightGBM (gradient boosting)

Below the row: "Calibration gate: ECE < 0.05"

---

## Slide 7 — Methodology: Dataset & Temporal Split

**Title:** Methodology — Dataset and Chronological Split

**Content (bullets):**
- **Dataset:** Bank Account Fraud (BAF) Suite v1 — 1,000,000 rows, 32 columns, 1.1029% fraud rate
- **Delay regime:** 1 month (`label_time = month + 1`)
- **No shuffling, no random split** — chronological only
- **Test window used exactly once**, after model and policy are frozen

**Split table:**

| Split | Months | Rows | Fraud rate |
|---|---|---:|---:|
| Train | 0–2 | 397,039 | 0.9813% |
| Validation | 3–4 | 278,627 | 1.0207% |
| Test | 5–6 | 227,491 | 1.2576% |
| **Censored** | **7** | **96,843** | **9.68% of dataset** |

**Visual:** The table above. Highlight the censored row.

---

## Slide 8 — System Development: Architecture

**Title:** System Development — Pipeline Architecture

**Content (bullets):**
- One pipeline, eight steps, single command to run
- Inputs: BAF `Base.csv` (1,000,000 rows × 32 columns)
- Processes: delay simulation, chronological split, classifier comparison, calibration gate, decision policy
- Outputs: trained classifier, action log, backtest report

**Pipeline flow to display:**
```
Base.csv
   ↓
load → simulate_delay → split
   ↓
train_compare → evaluate_compare → score
   ↓
decide (argmin expected cost)
   ↓
backtest → report
```

**Visual:** The pipeline diagram as one clean horizontal or vertical flow. No decorative colors.

---

## Slide 9 — System Development: Inputs, Processes, Outputs

**Title:** System Development — What the System Does

**Content — three-column layout:**

| Inputs | Processes | Outputs |
|---|---|---|
| Transaction features (`X_t`) | Preprocess per classifier | Trained classifier |
| Transaction amount (`amount_proxy`) | Train and compare 3 classifiers | Preprocessing pipeline |
| Frozen cost matrix | Apply calibration gate | `p_fraud` per transaction |
| — | Route each transaction by argmin | Action log (approve/review/block) |
| — | Compute realized cost | Backtest report (cost, CI, sensitivity) |
| — | — | Deployed Streamlit app |

**Visual:** The three-column table. This is the "explain how it works" slide required by the professor.

---

## Slide 10 — System Development: Live Demonstration

**Title:** System Development — Live Demonstration

**Content (bullets):**
- **Deployed decision-support application:**
  - `delayed-label-fraud-decisioning-gefp9s9mbkfdyzhhvescdm.streamlit.app`
- **What it shows:**
  - Predicted fraud probability (`p_fraud`)
  - Routed action: `approve`, `review`, or `block`
  - Cost reasoning behind the action
- **How to use:**
  - Manual input form for a single transaction
  - CSV upload for batch scoring
- **Loads the same classifier and preprocessing pipeline** reported in the paper

**Visual:** Live browser window, or two pre-prepared screenshots:
1. One low-amount transaction → `approve`
2. One high-amount transaction → `review`

**Do NOT just describe the app — open it and demo it.**

---

## Slide 11 — Results: Main Finding

**Title:** Results — Policy vs. Baselines

**Content (bullets):**
- Policy cost per transaction: **0.007491**
- Strongest baseline (LightGBM + static 0.5): **0.017798**
- **Cost reduction: 57.91%**
- 95% bootstrap CI: **[53.95%, 62.13%]** — excludes zero → the result is a **finding**

**Results table:**

| Baseline | Cost/txn |
|---|---:|
| Random decision | 0.047484 |
| Approve-all | 0.018928 |
| Block-all | 0.098742 |
| Logistic Regression + static 0.5 | 0.018737 |
| Random Forest + static 0.5 | 0.018928 |
| LightGBM + static 0.5 (**strongest**) | 0.017798 |
| **Cost-sensitive policy** | **0.007491** |

**Visual:** The table above, with the last row in bold. Add a callout: "**57.91% cost reduction**".

---

## Slide 12 — Results: Robustness

**Title:** Results — Sensitivity and Robustness

**Content (bullets):**
- Each cost parameter varied 2× (one at a time); model **not retrained**
- Minimum advantage across all variations: **47.76%**
- Even at the worst case, the policy retains nearly half the baseline cost reduction
- Cost rate calibrated from training-window amounts only → **no test-set tuning**

**Sensitivity table:**

| Configuration | Policy cost | Advantage |
|---|---:|---:|
| Baseline | 0.007491 | 57.91% |
| `false_positive_cost` = 0.05 | 0.007037 | 60.36% |
| `false_positive_cost` = 0.20 | 0.007625 | 57.38% |
| `review_cost` = 0.01 | 0.006253 | 64.87% |
| `review_cost` = 0.04 | 0.009298 | **47.76%** |
| `residual_fraud_loss` = 0.15 | 0.006588 | 62.99% |
| `residual_fraud_loss` = 0.60 | 0.008700 | 51.12% |

**Visual:** The table above. Highlight the minimum-advantage row.

---

## Slide 13 — Results: Classifier Comparison (Non-Finding)

**Title:** Results — Classifier Comparison Reported as a Non-Finding

**Content (bullets):**
- Cross-validated realized cost after the policy:

| Classifier | Mean cost/txn (CV) |
|---|---:|
| LightGBM | 0.005852 |
| Logistic Regression | 0.005915 |
| Random Forest | 0.006515 |

- Gap between top two (LGBM vs LR): **1.07% relative**
- Pre-registered threshold for a finding: **5%**
- 1.07% < 5% → comparison is a **non-finding**
- Tie broken by **simplicity**: Logistic Regression selected
- Justification: interpretability and speed, not superior performance

**Visual:** Small table above; a horizontal bar showing "1.07% measured" vs "5% threshold."

---

## Slide 14 — Discussion: Why the Policy Works

**Title:** Discussion — Why the Decision Rule Wins

**Content (bullets):**
- The 57.91% comes from the **decision rule**, not the classifier
- All three classifiers were well-calibrated (ECE = 0.0033, well below 0.05)
- All three static-0.5 baselines performed near approve-all
- Mechanism: **amount scaling**
  - High-amount transactions route to `review` even when `p` is unchanged
  - Under constant loss, they would have been approved
- Same classifier probabilities, different decision rule → different result

**Visual:** One small comparison:

```
Classifier + static 0.5   →   ≈ approve-all
Classifier + argmin rule  →   57.91% cost reduction
```

---

## Slide 15 — Limitations & Conclusion

**Title:** Limitations and Conclusion

**Content — Limitations (bullets):**
- Single delay regime (1 month only)
- Synthetic dataset; results are not production estimates
- Amount proxy: `proposed_credit_limit`, not a true transaction amount
- No review-capacity constraint
- No feedback-loop modeling

**Content — Conclusion (bullets):**
- Fraud detection is a **decision problem**, not a classification problem
- The argmin-of-expected-cost policy reduced cost by **57.91%**
- 95% CI **[53.95%, 62.13%]** — excludes zero
- Result is robust: minimum advantage **47.76%**
- **96,843** censored labels (9.68%) reported, not hidden
- Classifier comparison was a non-finding — reported honestly

**Visual:** Two-column layout: Limitations on the left, Conclusion on the right. The four preserved numbers (57.91%, [53.95%, 62.13%], 96,843, 9.68%) bolded.

---

## Slide 16 — Thank You / Q&A

**Title:** Thank You

**Content:**
- Questions?

**Below:**
- Repository: `github.com/kira-ml/delayed-label-fraud-decisioning`
- Deployed app: `delayed-label-fraud-decisioning-gefp9s9mbkfdyzhhvescdm.streamlit.app`

**Visual:** Both URLs on the slide. Keep it clean.

---

## Quick Reference — Do Not Change These Numbers

| Number | Value | Where it appears |
|---|---:|---|
| Policy cost/txn | 0.007491 | Slide 11, 12 |
| Strongest baseline cost/txn | 0.017798 | Slide 11 |
| Cost reduction | 57.91% | Slides 11, 14, 15 |
| Bootstrap CI | [53.95%, 62.13%] | Slides 11, 15 |
| Minimum sensitivity advantage | 47.76% | Slides 12, 15 |
| Censored rows | 96,843 | Slides 7, 15 |
| Censored fraction | 9.68% | Slides 7, 15 |
| ECE | 0.0033 | Slide 14 |
| CV gap (LGBM vs LR) | 1.07% | Slide 13 |
| Test rows | 227,491 | Slide 7 |

---

## Do NOT Put on Any Slide

| Forbidden phrase | Reason |
|---|---|
| "High accuracy" | Accuracy is meaningless at 1.26% base rate |
| "Production-ready" | Synthetic dataset; single delay regime |
| "Real bank data" | BAF is synthetic |
| "Handles all delay regimes" | Only 1-month regime tested |
| "Statistically significant across all variations" | CIs computed only on the main comparison |
| "The model detects fraud with X% accuracy" | Use cost reduction, not accuracy |

---

## Pre-Presentation Checklist

- [ ] Every slide uses bullets or tables — no paragraphs
- [ ] All 10 numbers in the Quick Reference table are consistent everywhere
- [ ] No forbidden phrases anywhere
- [ ] Live demo tested the day before
- [ ] Two backup screenshots of the app ready
- [ ] Each presenter has rehearsed their slides
- [ ] Total run time within the required limit
- [ ] URLs on Slide 16 open successfully
- [ ] Every slide's claims match `docs/main.tex` exactly

---

*End of slide content.*
