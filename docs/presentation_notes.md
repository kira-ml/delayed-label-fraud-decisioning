# Presentation Notes — Delayed-Label Fraud Decisioning

> **Course:** Introduction to Machine Learning — Final Group Project
> **Institution:** National University Philippines
> **Instructor:** Ken Oliver Caparros
> **Format:** Thesis-defense style, PowerPoint, live system demo required
> **Deadline:** October 17, 2026

---

## How to Use This File

Each slide below has three parts:

1. **Slide Content** — the exact bullets to place on the slide. Keep these short. No paragraphs.
2. **Speaker Notes** — what the presenter says. Not written on the slide.
3. **Visual** — what to show, if anything. Tables count as visuals; no need to build charts.

Presenter slots are marked `[Presenter: ___]` — fill these once the group decides.

**Do not put paragraphs on slides.** The professor's guideline is explicit. Bullets only.

---

## The Four Numbers to Know Cold

Every group member should be able to say these without looking:

| Number | Meaning |
|---|---|
| **57.91%** | Cost reduction vs strongest baseline |
| **[53.95%, 62.13%]** | 95% bootstrap confidence interval |
| **96,843** | Censored labels (month 7) |
| **9.68%** | Censored fraction of the dataset |

Two more worth knowing:

| Number | Meaning |
|---|---|
| **0.007491** | Policy cost per transaction |
| **0.017798** | Strongest baseline cost per transaction |

---

## Forbidden Claims

Do not say any of these. They are false or unsupported, and the professor's guideline #6 requires consistency with the submitted paper.

| Do NOT say | Say instead |
|---|---|
| "High accuracy" | "57.91% cost reduction" |
| "The model is production-ready" | "This is a controlled backtest on synthetic data" |
| "It works on real bank data" | "It is evaluated on the BAF synthetic benchmark" |
| "It handles all delay regimes" | "It is evaluated under a one-month delay regime" |
| "The classifier is the best" | "The classifier comparison was a non-finding" |
| "Real-time performance verified" | (omit — no latency was measured) |

---

# SLIDE 1 — Title

**Slide Content**

- Cost-Sensitive Fraud Decisioning Under Delayed and Censored Labels
- A Temporal Backtest on the Bank Account Fraud Dataset
- Group members: Ken Ira Lacson Talingting, Lawrence Abad, John Kelly Nogales, Smith Albert Surio
- College of Computing and Information Technologies
- National University Philippines
- October 17, 2026

**Speaker Notes**

Open with one sentence: "This project asks how a fraud system should decide — approve, review, or block — before the label arrives." Then hand off to the next presenter.

**Visual:** None. Clean title slide.

`[Presenter: ___]`

---

# SLIDE 2 — The Research Problem

**Slide Content**

- Payment transactions must be authorized **before** anyone knows if they are fraudulent
- Fraud labels arrive weeks to months later
- Some fraud is never reported — the label is **censored**, not negative
- The real question is not "is this fraud?" but "**what action should we take now?**"

**Speaker Notes**

Explain the structural fact: in real-time payments, the decision happens at time `t`, but the label arrives at `t + Δ`, where Δ is often 30 to 120 days. This is not a modeling choice — it is the shape of the domain. Then state the consequence: a model trained on settled disputes learns from labels that are late and sometimes missing. The operational question is not classification accuracy. It is which action to take under uncertainty.

**Visual:** One simple timeline diagram:
```
Decision  ───────────────────►  Label
   t                              t + Δ
         (gap: 30–120 days)
```
Keep it to two arrows and a label. No color needed.

`[Presenter: ___]`

---

# SLIDE 3 — Objectives

**Slide Content**

- Frame fraud detection as a **decision problem**, not a classification problem
- Evaluate a cost-sensitive policy end-to-end on a delayed-label dataset
- Compare three traditional classifiers **as inputs to the policy**
- Measure the result with a cost metric, a confidence interval, and a sensitivity sweep
- Report censored labels honestly rather than treating them as negatives

**Speaker Notes**

Read the objectives in order. Emphasize the third one: the classifiers are not the product — they are inputs. This is the framing shift the paper is built on. Note that the objectives are measurable, not vague.

**Visual:** None needed. Bullets only.

`[Presenter: ___]`

---

# SLIDE 4 — Methodology: The Decision Policy

**Slide Content**

- Three actions: `approve`, `review`, `block`
- Policy chooses the action that minimizes expected cost:

```
E[cost(approve)] = p × fraud_loss(amount)
E[cost(review)]  = review_cost + p × residual_loss
E[cost(block)]   = (1 − p) × false_positive_cost
```

- `p` = calibrated fraud probability from the classifier
- Cost matrix frozen before modeling:
  - `fraud_loss = 1.0`, `false_positive_cost = 0.1`
  - `review_cost = 0.02`, `residual_fraud_loss = 0.3`
- Amount scaling: larger transactions carry larger fraud loss

**Speaker Notes**

Explain that the policy is the object of study. The classifier feeds it a probability. The policy uses that probability, the transaction amount, and a fixed cost matrix to pick one of three actions. The argmin rule is the source of truth. Amount scaling matters because a ₱10,000 fraudulent transfer should be treated differently from a ₱10 one.

**Visual:** The three-equation block above is enough. No diagram needed.

`[Presenter: ___]`

---

# SLIDE 5 — Methodology: Classifiers, Calibration, and Data Split

**Slide Content**

- Three classifiers compared as policy inputs:
  - Logistic Regression
  - Random Forest
  - LightGBM
- Calibration gate: **ECE < 0.05** on validation, or reject
- Chronological split (no shuffling):
  - Train: months 0–2 (397,039 rows)
  - Validation: months 3–4 (278,627 rows)
  - Test: months 5–6 (227,491 rows)
  - Censored: month 7 (**96,843 rows, 9.68%**)
- Delay regime: 1 month (`label_time = month + 1`)
- Test window used exactly once

**Speaker Notes**

Explain why calibration is a gate, not an option: the policy's expected costs are linear in `p`, so an uncalibrated score produces wrong decisions. Then explain the split: no random split, ever. Month 7 is censored because its label would arrive after the dataset ends. Those 96,843 rows are excluded and reported, not treated as legitimate.

**Visual:** The split table above. This is one of the two most important slides.

`[Presenter: ___]`

---

# SLIDE 6 — System Development: Architecture

**Slide Content**

- One pipeline, eight steps:
  - `load → simulate_delay → split → train_compare → evaluate_compare → score → decide → backtest`
- Inputs: BAF `Base.csv` (1,000,000 rows, 32 columns)
- Processes:
  - Simulate 1-month delay
  - Chronological split
  - Train and compare three classifiers
  - Apply calibration gate
  - Route each transaction by argmin expected cost
- Outputs:
  - Trained classifier + preprocessing pipeline
  - Action log per transaction
  - Backtest report with cost, CI, and sensitivity

**Speaker Notes**

Walk through the pipeline left to right. Emphasize: there is one pipeline, not two. The classifier comparison is a step inside the decision pipeline — it exists to answer "which classifier, when fed into the policy, produces the lowest realized cost?" The outputs feed the paper and the deployed app.

**Visual:** The flowchart from `mvp_architecture.md` §2. Reproduce it as a horizontal flow:
```
Base.csv → load → delay → split → compare → calibration → policy → backtest
```
One row. Clean. No clutter.

`[Presenter: ___]`

---

# SLIDE 7 — System Demonstration (LIVE)

**Slide Content**

- Deployed decision-support application:
  - URL: `delayed-label-fraud-decisioning-gefp9s9mbkfdyzhhvescdm.streamlit.app`
- What it shows:
  - Predicted fraud probability (`p_fraud`)
  - Routed action: `approve`, `review`, or `block`
  - Cost reasoning behind the action
- How to use:
  - Manual input form, or
  - CSV upload for batch scoring

**Speaker Notes**

This is the live demonstration slide. Do not just describe it — open the URL and show it running. Enter one transaction with a low amount (should route to approve) and one with a high amount (should route to review). Point out that the app loads the exact classifier and preprocessing pipeline reported in the paper. If the network fails, fall back to the screenshots prepared in advance.

**Visual:** Live browser window. Backup: two screenshots — one approve case, one review case.

`[Presenter: ___]`

---

# SLIDE 8 — Results: The Main Finding

**Slide Content**

- Policy cost per transaction: **0.007491**
- Strongest baseline (LightGBM + static 0.5): **0.017798**
- **Cost reduction: 57.91%**
- 95% bootstrap confidence interval: **[53.95%, 62.13%]**
- CI excludes zero → the result is a **finding**, not noise

| Baseline | Cost/txn |
|---|---:|
| Random | 0.047484 |
| Approve-all | 0.018928 |
| Block-all | 0.098742 |
| LR + static 0.5 | 0.018737 |
| RF + static 0.5 | 0.018928 |
| LGBM + static 0.5 (strongest) | 0.017798 |
| **Cost-sensitive policy** | **0.007491** |

**Speaker Notes**

This is the headline result. Say the two numbers slowly: policy 0.007491, strongest baseline 0.017798. That is a 57.91% reduction. The bootstrap CI is [53.95%, 62.13%] — it does not include zero, so the result is statistically supported. Then point at the table: the three static-threshold baselines all perform near approve-all. A well-calibrated classifier with a fixed 0.5 cut is not a decision rule at this base rate. That is the paper's key methodological point.

**Visual:** The table above. This is the most important slide.

`[Presenter: ___]`

---

# SLIDE 9 — Results: Robustness and the Non-Finding

**Slide Content**

**Sensitivity sweep (2× on each cost parameter):**

- Minimum advantage across all variations: **47.76%**
- Even at the worst case, the policy retains nearly half the baseline cost reduction

**Classifier comparison — reported as a non-finding:**

- LightGBM won the CV comparison by only 1.07% relative
- The pre-registered threshold for a finding was 5%
- 1.07% is inside the noise band → non-finding
- Logistic Regression selected by **simplicity**, not superiority

**Speaker Notes**

Two honest results here. First: the finding is robust. Varying each cost parameter by 2× still leaves the policy ahead by at least 47.76%. Second: the classifier comparison is a non-finding. The gap between the top two classifiers was 1.07%, far below the 5% threshold that was set before modeling. So the group reports it as a non-finding and picks the simpler model. This is the kind of honest reporting that the professor asked for.

**Visual:** The sensitivity table from the paper (7 rows). Add a one-line callout: "minimum advantage = 47.76%."

`[Presenter: ___]`

---

# SLIDE 10 — Discussion: Why the Policy Works

**Slide Content**

- The 57.91% comes from the **decision rule**, not the classifier
- All three classifiers were well-calibrated (ECE well below 0.05)
- All three static-0.5 baselines performed near approve-all
- The argmin rule uses **amount scaling**: large transactions route to review even when `p` is unchanged
- Same classifier, different decision rule → different result

**Speaker Notes**

This is the "so what" slide. Explain that the win does not come from a better model. It comes from using the model's probabilities correctly. The amount scaling is the mechanism: when the fraud-loss term grows with transaction amount, the argmin routes large transactions to review. Under a constant-loss assumption, those same transactions would have been approved.

**Visual:** None. Bullets only.

`[Presenter: ___]`

---

# SLIDE 11 — Limitations

**Slide Content**

- Single delay regime (1 month only)
- Synthetic dataset (BAF); not a production estimate
- Amount proxy: `proposed_credit_limit`, not a true transaction amount
- No capacity constraint on the review queue
- No feedback-loop modeling
- Classifier comparison was a non-finding — selection by simplicity, not performance

**Speaker Notes**

State the limitations plainly. The professor's guideline says all claims must be consistent with the paper. The paper names these limitations explicitly. Naming them here builds credibility rather than weakening the presentation.

**Visual:** Bullets only.

`[Presenter: ___]`

---

# SLIDE 12 — Conclusion

**Slide Content**

- Fraud detection is a **decision problem**, not a classification problem
- The argmin-of-expected-cost policy reduced cost by **57.91%**
- 95% CI **[53.95%, 62.13%]** — excludes zero
- Result is robust (minimum advantage **47.76%**)
- **96,843** censored labels (9.68%) reported, not hidden
- Classifier comparison was a non-finding — reported honestly

**Speaker Notes**

Close with the one-line takeaway: "The decision rule, not the model, does the work." Then offer the floor for questions.

**Visual:** The four preserved numbers in a single box. Nothing else.

`[Presenter: ___]`

---

# SLIDE 13 — Thank You / Q&A

**Slide Content**

- Thank you
- Questions?

**Speaker Notes**

Have the URL to the repository and the deployed app visible on the slide if possible. Be ready to answer questions about: why Logistic Regression was selected, why static thresholds fail at 1.26% base rate, and what the censored 9.68% means.

**Visual:** Repository URL + Streamlit URL.

`[Presenter: ___]`

---

## Presenter Assignment (Fill In)

Distribute slides so all four members speak. A balanced split:

| Presenter | Slides | Topic |
|---|---|---|
| Member 1 | 1, 2, 3 | Title, Problem, Objectives |
| Member 2 | 4, 5 | Methodology (policy + setup) |
| Member 3 | 6, 7 | System Development + **Live Demo** |
| Member 4 | 8, 9, 10, 11, 12, 13 | Results, Discussion, Limitations, Conclusion |

If the demo is long, give the demo to a different member to balance speaking time.

---

## Pre-Presentation Checklist

- [ ] Every slide has bullets only — no paragraphs
- [ ] The four numbers (57.91%, [53.95%, 62.13%], 96,843, 9.68%) are consistent everywhere
- [ ] No forbidden claims used ("high accuracy," "production-ready," etc.)
- [ ] App URL opens and returns predictions
- [ ] Two backup screenshots of the app ready (approve case, review case)
- [ ] Each presenter has rehearsed their own slides
- [ ] Presentation runs within the time limit
- [ ] Someone has tested the projector/laptop combination in advance

---

## Rehearsal Notes

- Time a full run at least twice before the actual presentation
- The demo slide (Slide 7) is the highest-risk section — rehearse the fallback
- Slide 8 (main result) and Slide 9 (robustness) should be the smoothest part of the talk
- Do not read bullets from the slide — the bullet is a memory prompt, not a script

---

*End of presentation notes.*
