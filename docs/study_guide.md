# Study Guide: Fraud Decision Desk

> **For:** Ken, Lawrence, John Kelly, Smith · Introduction to Machine Learning, Final Project
> **Use:** study material + presentation script + professor Q&A prep, all in one place.
> **Sources:** `docs/main.tex` (the submitted paper), `docs/paper/reference_sheet.md`,
> `docs/decision_policy.md`, `docs/evaluation_protocol.md`, `docs/data_card.md`,
> `docs/problem_framing.md`, `reports/`, and the code in `src/`. Nothing here is invented;
> where the documents are silent, this guide says so.

**Three kinds of content, tagged throughout:**

| Tag | Meaning | How to study it |
|---|---|---|
| **[MEMORIZE]** | Exact facts and numbers | Say them out loud until you can without looking |
| **[UNDERSTAND]** | Concepts you must be able to explain | Explain each in one sentence to a non-ML friend |
| **[REASON]** | Things you answer by thinking, not recall | Practise the reasoning, not the wording |

---

## How to use this guide (time-boxed)

| If you have... | Read these sections |
|---|---|
| **20 minutes** | §1 (must-know card) → §9 (your own slides in the script) |
| **1 hour** | §1 → §2 → §3 → §9 → the ★ questions in §10 |
| **3 hours** | Everything, then do the self-test in §11 out loud with a partner |

---

## §1. The must-know card ★ [MEMORIZE]

### 1.1 The project in one sentence

> We built a system that decides **approve, review, or block** for each bank-account
> application **before** we know if it is fraud, by choosing the action with the **lowest
> expected cost**. On a fair test it cut cost by **57.91%** compared with the best simple rule.

### 1.2 The four numbers everyone must know

| Number | What it means |
|---|---|
| **57.91%** | Our policy's cost reduction vs the strongest baseline (LightGBM + 0.5 cut-off) |
| **[53.95%, 62.13%]** | 95% bootstrap confidence interval for that reduction (excludes zero → real effect) |
| **47.76%** | The *worst* reduction when we halved/doubled each cost guess (still large) |
| **96,843 (9.68%)** | Rows in month 7 with no label yet ("censored"); set aside, not counted as safe |

### 1.3 The other numbers worth knowing

| Number | Meaning |
|---|---|
| 0.007491 | Our policy's realized cost per application (test window) |
| 0.017798 | Strongest baseline (LightGBM + static 0.5) cost per application |
| 0.018928 | Approve-everyone cost per application |
| 1,000,000 rows · 1.1029% fraud | The full BAF dataset |
| 397,039 / 278,627 / 227,491 | Train (months 0–2) / validation (3–4) / test (5–6) rows |
| 0.9813% / 1.0207% / 1.2576% | Fraud rate in train / validation / test |
| 28 features (23 numeric + 5 categorical) | Model inputs |
| ECE 0.0033 (gate < 0.05) | Calibration error on validation: risk scores behave like real probabilities |
| 1.07% (bar: 5%) | Gap between the top two classifiers in cross-validation → a tie, a "non-finding" |
| 205,395 / 21,371 / 725 | Test-window decisions: approve / review / block |
| Precision 0.0654 · Recall 0.5051 | Of flagged apps, ~1 in 15 is fraud; the policy catches ~half of all fraud |
| 1 / 521.1626 = 0.0019187869 | `fraud_loss_rate`, from the **training** months' average credit limit |
| Costs: 0.1 / 0.02 / 0.3 | Wrongly blocking / one manual check / share of loss still suffered after a check |

### 1.4 Never say (and what to say instead)

| Do NOT say | Why | Say instead |
|---|---|---|
| "High accuracy" | 98.9% of apps are legit; "approve everyone" is ~99% accurate and useless | "57.91% lower cost" |
| "Production-ready" | Synthetic data, one delay regime, proxy amount | "A controlled backtest" |
| "Real bank data" | BAF is synthetic | "A synthetic benchmark built from real anonymized data" |
| "Works for any delay" | Only 1 month tested (in the paper) | "Tested with a one-month delay" |
| "Our model is the best" | The comparison was a tie | "The models tied; the decision rule made the difference" |
| "Capacity-aware" / "real-time verified" | Not modelled / not measured in the paper | Don't claim it |

---

## §2. The project in plain English ★ [UNDERSTAND]

### 2.1 The problem (the "bare fact")

A bank must say yes or no to an application **right now**. But whether it was fraud is only
known **weeks or months later** (industry dispute windows: 30–120 days), and some fraud is
**never reported at all**.

```text
 TODAY                                   30–120 DAYS LATER
 decision must be made  ───────────────► the truth (the "label") arrives
 (no label yet!)          waiting gap      ...or never arrives ("censored")
```

So the real question is **not** "is this fraud?" (we can't know yet).
It is **"what should we do right now, given how likely fraud is?"**

### 2.2 Why "just predict fraud" isn't enough

A fraud model gives a **probability**, e.g. "12.5% chance of fraud". That number alone
doesn't tell you what to do. The right action depends on **what each mistake costs**:

| Mistake | What it costs the bank |
|---|---|
| Approve a fraud (false negative) | The money lost (bigger amount → bigger loss) |
| Block a genuine customer (false positive) | Friction, lost business, an unhappy customer |
| Send for a manual check | The cost of the check, plus whatever fraud still gets through |

### 2.3 Our idea in three steps

```text
 Application ──► [1] Model estimates fraud risk p (e.g. 12.5%)
                 [2] Price each option:
                       approve = p × possible loss (grows with amount)
                       review  = check cost + p × loss a check can't stop
                       block   = (1 − p) × cost of turning away a genuine customer
                 [3] Pick the cheapest  ──►  APPROVED / FOR REVIEW / BLOCKED
```

### 2.4 The headline result

On months the model never saw, the cost-based desk cost **0.007491** per application;
the best simple rule (a model + "block if ≥ 50%") cost **0.017798**. That is **57.91% lower**.

### 2.5 The key insight (the "so what")

> **The decision rule, not the model, does the work.**

All three classifiers with a fixed 50% cut-off were barely better than "approve everyone"
(LightGBM + 0.5 only 5.97% better; Logistic Regression + 0.5 only 1.01%; Random Forest + 0.5
0%). Feeding the **same kind of probabilities** into the cost-based rule gave 57.91%.

---

## §3. Concepts explained from the basics [UNDERSTAND]

Each concept: what it is → why it matters **in our project**.

### 3.1 Classifier and fraud probability (`p`)
- **What:** a model that reads an application's 28 details and outputs `p = P(fraud | details)`,
  a number between 0 and 1.
- **In our project:** the classifier is only an **input**. The policy (§3.4) is the thing being
  studied. *"The classifier is an input; the policy is the object of study; the backtest is the evidence."*

### 3.2 Class imbalance
- **What:** one class is much rarer than the other. Fraud is **1.1%** of rows.
- **Why it matters:** the model rarely outputs more than 50% for anything, so a 50% cut-off
  flags almost nothing. At the 0.5 cut, Logistic Regression caught **18** frauds out of 2,861
  (recall 0.0063) while still showing **98.75% accuracy**. That is the trap.
- **What we did NOT do:** no resampling and no class weights. Both distort the probabilities,
  and our policy needs honest probabilities (§3.3).

### 3.3 Calibration (and ECE)
- **What:** a model is *calibrated* if, among applications it gives 10% risk, about 10% really
  are fraud.
- **ECE (Expected Calibration Error):** sort validation apps into 10 equal-size groups by
  predicted risk; in each group compare average predicted risk with the actual fraud rate;
  average those gaps (weighted by group size). **Ours: 0.0033.**
- **Why it matters:** the policy *multiplies* `p` by costs. If `p` is wrong, every expected
  cost is wrong, so every decision is wrong. That's why calibration is a **gate**
  (ECE < 0.05 or the model is rejected), not just a nice-to-have.
- **Detail worth knowing:** the model slightly **over-estimates** risk in every group (highest
  group: about 8.3% predicted vs 6.8% actual). This errs toward caution. It was documented,
  not "fixed", because no measured failure justified a change.

### 3.4 Expected cost and the argmin rule
- **Expected cost** = average cost you'd pay if you took that action many times with risk `p`.
- **argmin** = "pick the option with the smallest value".
- **Our policy:** compute the three expected costs, pick the smallest. *That is the entire policy.*
  It is intentionally simple; the classic cost-sensitive learning result (Elkan, 2001).

```text
E[cost(approve)] = p × fraud_loss(amount)
E[cost(review)]  = review_cost + p × residual_fraud_loss
E[cost(block)]   = (1 − p) × false_positive_cost
action = argmin of the three
```

### 3.5 The cost matrix (frozen before modelling) [MEMORIZE]

| Setting | Value | Plain meaning |
|---|---:|---|
| `fraud_loss` | 1.0 | Loss from a fraud of *average* size (the unit) |
| `false_positive_cost` | 0.1 | Cost of wrongly blocking a genuine customer |
| `review_cost` | 0.02 | Cost of one manual check |
| `residual_fraud_loss` | 0.3 | Loss still suffered on a fraud even after a check |
| `amount_scaled` | true | Fraud loss grows with the amount |

- **Cost unit:** 1 unit = the loss from one fraudulent application of average size.
- **Where the values came from:** the documents describe them as **frozen assumptions**, chosen
  before any modelling and never tuned. They do **not** record an industry source. **Don't claim
  one.** The honest defence is the sensitivity sweep (§3.10).

### 3.6 Amount scaling (the mechanism behind the result) ★
- **What:** `fraud_loss(amount) = amount × 0.0019187869`, where `0.0019187869 = 1 / 521.1626`,
  the average credit limit in the **training** months only. So an average-size fraud costs 1.0.
- **Why:** a 2,000 fraud should hurt more than a 200 fraud.
- **Effect:** same risk, bigger amount → approving gets more expensive → the desk switches to
  **review**. Under a constant loss, those same applications would have been approved.
- **No leakage:** the rate uses training-month amounts only, so no test information leaks in.
- **Amount used:** `proposed_credit_limit` (renamed `amount_proxy`). BAF has no true
  transaction-amount column, which is a stated limitation.

### 3.7 Delayed and censored labels
- **Delayed:** the label arrives after the decision. We **simulate a 1-month delay**: a row in
  month `t` gets its label at month `t+1`. (BAF only has month-level time, so 1 month is the
  finest delay we can simulate.)
- **Censored:** month 7's labels would arrive in month 8, after the data ends, so they are
  **unknown**, not "legit". We **exclude and report** those 96,843 rows (9.68%).
- **Why not call them legit?** That would teach the model that some frauds are safe and make
  precision look better than it is.

### 3.8 Temporal (chronological) split
- **What:** learn on the past, test on the future, never shuffle.

```text
 Month:   0    1    2  │  3    4  │  5    6  │   7
         ───LEARN──────│──TUNE────│──TEST────│ UNKNOWN
         397,039 rows  │ 278,627  │ 227,491  │ 96,843 (censored)
         fraud 0.98%   │  1.02%   │  1.26%   │ excluded
```

- **Why:** in real life you always predict the future from the past. A random split would let
  the model "see the future" and look better than it really is.
- **Test used exactly once**, after everything was frozen.

### 3.9 Cross-validation (expanding window)
- **What:** to choose hyperparameters, train on months 0..k and validate on month k+1, inside
  the training window only. With months 0–2 this gives **2 folds**.
- **Why expanding-window, not k-fold:** normal k-fold mixes time and leaks the future.

### 3.10 Bootstrap confidence interval and sensitivity sweep
- **Bootstrap:** resample the 227,491 test rows **with replacement** 1,000 times (seed 42),
  recompute the advantage each time, and take the middle 95% → **[53.95%, 62.13%]**. Because
  it excludes zero, the result isn't luck.
- **Sensitivity:** halve and double each of the 3 cost settings, one at a time, **without
  retraining**. Worst case: **47.76%** (when manual checks cost twice as much).

### 3.11 Baselines
Six "simple strategies" to beat:

| Baseline | What it does | Cost/application |
|---|---|---:|
| Random decision | Picks approve/review/block at random (seed 42) | 0.047484 |
| Approve-all | Approves everything | 0.018928 |
| Block-all | Blocks everything | 0.098742 |
| LR + static 0.5 | Blocks if p ≥ 0.5, else approves | 0.018737 |
| RF + static 0.5 | Same, with Random Forest | 0.018928 |
| **LightGBM + static 0.5** (strongest) | Same, with LightGBM | **0.017798** |
| **Our policy** | argmin of expected cost | **0.007491** |

Note: the static-0.5 baselines **never use review**. Rule of the project: always compare
against the **strongest** baseline, not the weakest.

### 3.12 The metrics (and why accuracy is forbidden)

| Metric | Meaning | Our use |
|---|---|---|
| **Realized cost per application** | Average actual cost of the decisions, using true labels | **Primary metric** |
| Accuracy | % correct | **Forbidden as a claim**: misleading at 1.1% fraud |
| Precision | Of flagged apps, % really fraud | Supporting (0.0654 for the policy) |
| Recall | Of all fraud, % flagged | Supporting (0.5051 for the policy) |
| ROC-AUC | How well the model *ranks* fraud above legit | Supporting (0.8753) |
| Brier score | Average squared error of probabilities | Supporting (0.011506 on test) |
| Precision@k / Recall@k | Quality of the top k% riskiest apps | Supporting (e.g. Recall@5% = 0.4729) |

### 3.13 The three classifiers

| Model | Plain explanation | Config used | Preprocessing |
|---|---|---|---|
| **Logistic Regression** (selected) | Weighted sum of features → S-curve → probability. Simple, readable weights | C = 10.0, max_iter = 1000 | Standard scaling + one-hot encoding |
| Random Forest | Many decision trees vote | 400 trees, random_state 42 | Ordinal encoding, no scaling |
| LightGBM | Trees built one after another, each fixing the last one's mistakes | 300 trees, learning rate 0.05 | Native categorical handling |

Grids searched: LR `C ∈ {0.01, 0.1, 1, 10}`; RF trees `{100, 200, 400}`; LightGBM
`(trees, lr) ∈ {(100, .10), (300, .10), (300, .05), (500, .05)}`.
**No neural networks / deep learning / AutoML**: out of scope by the project's own rules
(traditional ML only).

### 3.14 Noise-band guard and "non-finding"
- **Rule set before modelling:** a classifier only "wins" if it wins **every** fold **and** beats
  the runner-up by **more than 5%**. Otherwise it's a tie, reported as a **non-finding**, and the
  simplest model is chosen (LR > RF > LightGBM).
- **What happened:** LightGBM 0.005852 vs LR 0.005915, a **1.07%** gap. Tie, so LR was chosen.
- **Why that's good science:** a 1.07% gap from two folds could easily be noise. Calling it a
  win would be overclaiming.

### 3.15 Data leakage (what we prevented)
Leakage = the model sees information it wouldn't have at decision time.

| Leak | How we blocked it |
|---|---|
| Future data | Chronological split; test used once |
| `device_fraud_count` | Excluded: may include fraud events **after** the decision |
| `month`, `label_month`, `observed` | Excluded: time/simulation columns |
| `transaction_id` | Excluded: an ID, no real signal |
| Scaling/encoding stats | Fit on training folds only |
| Cost rate | From training months only |
| Calibration | Never fit on test |

---

## §4. Methodology, step by step (with the "why") [UNDERSTAND]

### 4.1 The pipeline (one command: `python -m src.pipeline`)

```text
 Base.csv (1,000,000 × 32)
   │
 [1] load ............ read data, give each row a transaction_id
 [2] simulate_delay .. label_month = month + 1; observed = label_month ≤ 7
 [3] split ........... train 0–2 / val 3–4 / test 5–6; month 7 censored
 [4] train_compare ... 3 classifiers × small grids, expanding-window CV,
                       pick by realized cost AFTER the policy
 [5] evaluate_compare  noise-band guard → non-finding → Logistic Regression
 [6] score ........... p_fraud for every test row
 [7] decide .......... argmin of expected cost → approve / review / block
 [8] backtest ........ realized cost vs 6 baselines → report
   │
 Analyses: calibration (ECE), sensitivity sweep, bootstrap CI
```

Reproducible: fixed seed 42; re-running gives identical output. **68 automated tests**
(`pytest`) check the policy maths, edge cases, data schema, and pipeline.

### 4.2 Every major decision and why ★ [REASON]

| Decision | Why |
|---|---|
| Treat it as a **decision** problem | The bank needs an action, not a score; both mistakes cost money |
| **Three actions** (not two) | Real fraud teams use manual review; review is the middle ground |
| **Expected-cost argmin** | Makes the trade-off explicit and auditable; standard theory (Elkan 2001) |
| **Freeze costs before modelling** | Prevents tuning costs to make results look good |
| **Amount scaling** | Bigger amounts = bigger possible loss; the main source of the gain |
| Rate from **training** months | No test information leaks into the cost |
| **Chronological split** | Mimics real use; random splits leak the future |
| **1-month delay** | BAF only has month-level time |
| **Exclude censored month 7** | Unknown ≠ legit; treating them as legit biases results |
| **Calibration gate** | The policy multiplies `p` by costs, so `p` must be a real probability |
| **No class weights / resampling** | They distort probabilities |
| **Select by realized cost, not F1/AUC** | The goal is cost, so choose by cost |
| **Noise-band guard (5%)** | Avoid calling noise a winner |
| **Strongest baseline** | Comparing to a weak baseline would inflate the result |
| **Bootstrap CI + 2× sensitivity** | Show the result isn't luck and survives wrong cost guesses |
| Credit limit used as a **cost input**, not a feature | It's reserved to price the loss (data card); the paper also notes it's heavily skewed (median 200, mean 515.85) |

### 4.3 Worked example (the demo's "Unusual" application) ★ [REASON]

Risk `p = 12.53%`. Costs: `fpc = 0.1`, `rc = 0.02`, `rfl = 0.3`, rate `= 0.0019187869`.

**At credit limit 200:** `fraud_loss = 200 × 0.0019188 = 0.3838`

| Option | Calculation | Expected loss |
|---|---|---:|
| Approve | 0.1253 × 0.3838 | **0.0481** ← cheapest |
| Review | 0.02 + 0.1253 × 0.3 | 0.0576 |
| Block | 0.8747 × 0.1 | 0.0875 |

**At credit limit 1,000:** `fraud_loss = 1.9188`

| Option | Calculation | Expected loss |
|---|---|---:|
| Approve | 0.1253 × 1.9188 | 0.2404 |
| Review | 0.02 + 0.1253 × 0.3 | **0.0576** ← cheapest |
| Block | 0.8747 × 0.1 | 0.0875 |

Same risk, 5× the amount → approve becomes 5× more expensive → **FOR REVIEW**.
The switch happens at about **240** for this application.

### 4.4 The thresholds (diagnostic view) [UNDERSTAND]

From the formulas you can derive *when* each action wins:

```text
review beats approve when  p > review_cost / (fraud_loss(amount) − residual_fraud_loss)
block  beats review  when  p > (fpc − rc) / (fpc + rfl) = 0.08 / 0.40 = 0.20
```

| Credit limit | Approve if risk below | Review if risk between | Block if risk above |
|---:|---:|---:|---:|
| 200 | 20.7% | (no review zone) | 20.7% |
| 500 | 3.0% | 3.0% – 20.0% | 20.0% |
| 1,000 | 1.2% | 1.2% – 20.0% | 20.0% |
| 2,000 | 0.6% | 0.6% – 20.0% | 20.0% |
| ≈521 (average) | 2.86% | 2.86% – 20.0% | 20.0% |

- At an average amount, review starts at **2.86%** risk (= 0.02 / 0.7), the "constant-loss" threshold.
- **Important:** the thresholds are only a *view*. The **argmin is the source of truth**. Thresholds
  can break (e.g. the review zone disappears at 200); the argmin never does. Three such edge cases
  are covered by unit tests.

---

## §5. Dataset [MEMORIZE + UNDERSTAND]

| Fact | Value |
|---|---|
| Name | Bank Account Fraud (BAF) Suite v1, `Base.csv` (Jesus et al., NeurIPS 2022) |
| What a row is | One **bank-account opening application** (the paper calls each a "transaction") |
| Size | 1,000,000 rows, 32 raw columns, months 0–7 |
| Fraud rate | 1.1029% overall |
| Synthetic? | **Yes.** Generated from a real, anonymized bank dataset |
| License | CC BY-NC-SA 4.0 (non-commercial research use) |
| Features used | 28 (23 numeric, 5 categorical: `payment_type`, `employment_status`, `housing_status`, `source`, `device_os`) |
| Excluded columns (8) | `transaction_id`, `fraud_bool`, `month`, `label_month`, `observed`, `amount_proxy`, `proposed_credit_limit`, `device_fraud_count` |

**EDA findings** (paper §VI-A; notebook `notebooks/01_eda.ipynb`):
1. **Fraud drifts over time:** 1.13% (month 0) → 0.87% (month 2) → 1.47% (month 7). That's why we test on later months.
2. **Credit limit is very skewed:** median 200, mean 515.85, skew 1.30, 24.17% above the outlier fence. Most ask for 200; a few up to 2,100.
3. **Every single feature is a weak signal:** strongest correlations with fraud are `credit_risk_score` (r = 0.0706) and `proposed_credit_limit` (r = 0.0689). Fraud detection is a "many weak signals" problem.
4. **Some groups are much riskier:** e.g. housing status BA has 3.75% fraud vs 0.34% for the lowest group.

---

## §6. Results and how to read them [MEMORIZE + UNDERSTAND]

### 6.1 Classifier comparison (cross-validated; a non-finding)

| Classifier | Mean realized cost ± SD |
|---|---|
| LightGBM | 0.005852 ± 0.000300 |
| Logistic Regression | 0.005915 ± 0.000338 |
| Random Forest | 0.006515 ± 0.000579 |

LightGBM vs LR: **0.000063 absolute, 1.07% relative** < 5% → tie → **LR chosen for simplicity**.
Random Forest was clearly worse.

### 6.2 The selected model at a 0.5 cut (supporting evidence only)

| Metric | Value |
|---|---|
| Accuracy | 0.9875 (misleading!) |
| Precision (fraud) | 0.7826 |
| Recall (fraud) | **0.0063** |
| Macro F1 | 0.5031 |
| ROC-AUC | 0.8753 |
| Confusion (TN, FP, FN, TP) | (224,625, 5, 2,843, 18) |

How to read it: at 0.5, the model almost never says "fraud". It misses 2,843 frauds and catches
18. **This is not how we use it**; it shows why a fixed cut-off fails.

### 6.3 The main result (test window, used once)
- Policy **0.007491** vs strongest baseline **0.017798** → **57.91%** lower cost.
- Bootstrap (1,000 resamples, seed 42): difference **0.010307** per app, CI [0.009602, 0.011058];
  advantage CI **[53.95%, 62.13%]**. Excludes zero → pre-registered success criterion met.

### 6.4 Sensitivity (each cost halved / doubled, no retraining)

| Scenario | Policy cost | Advantage |
|---|---:|---:|
| As planned | 0.007491 | 57.91% |
| `false_positive_cost` = 0.05 | 0.007037 | 60.36% |
| `false_positive_cost` = 0.20 | 0.007625 | 57.38% |
| `review_cost` = 0.01 | 0.006253 | 64.87% |
| `review_cost` = 0.04 | 0.009298 | **47.76%** (worst) |
| `residual_fraud_loss` = 0.15 | 0.006588 | 62.99% |
| `residual_fraud_loss` = 0.60 | 0.008700 | 51.12% |

Read it as: **the result depends on the cost guesses, but not fragilely.** Even the worst case keeps
a 47.76% advantage. Note: bootstrap CIs were computed only for the main comparison, not for each
sensitivity row.

### 6.5 What the policy actually did on the test months

| | Count | Of which fraud |
|---|---:|---:|
| Approve | 205,395 | 1,416 (missed) |
| Review | 21,371 | 1,208 |
| Block | 725 | 237 |
| **Total** | **227,491** | **2,861** |

- Recall 0.5051: it flagged 1,445 of 2,861 frauds (about half).
- Precision 0.0654: about **1 in 15** flagged apps is fraud. **That's intended**: a check (0.02)
  is cheap compared with a missed fraud (≈ the amount × rate), so the policy accepts many false alarms.
- Brier score 0.011506 (test). Precision@1/5/10% = 0.2431 / 0.1189 / 0.0775;
  Recall@1/5/10% = 0.1933 / 0.4729 / 0.6162.

---

## §7. The system (app) [UNDERSTAND]: John Kelly's section

**Live app:** delayed-label-fraud-decisioning-gefp9s9mbkfdyzhhvescdm.streamlit.app
(Streamlit; loads the **same** saved model + preprocessing as the paper.)

| In | Through | Out |
|---|---|---|
| Application details (28) | Risk model (Logistic Regression) | Fraud risk % |
| Requested credit limit | Price the 3 options | Stamp: APPROVED / FOR REVIEW / BLOCKED |
| Fixed cost settings | Pick the cheapest | Reason, risk scale, cost slip; batch worklist + CSV |

**Four tabs:**
1. **Check one application**: three real examples (Everyday 1.3% → approved; Unusual 12.5% → approved at 200, review at 1,000; Suspicious 29.8% → blocked, labelled fraud in the data), a credit-limit slider, a risk-zone scale, and the 3-row cost slip.
2. **Check a batch**: upload a CSV or use the 500-application sample → 450 approved, 46 review, 4 blocked; worklist sorted by expected saving; CSV download.
3. **How it decides**: the steps, formulas, the amount-threshold table, model card.
4. **Study results**: the 57.91% chart, sensitivity table, limitations.

Advanced (sidebar): cost what-if sliders. These are **what-ifs only**; the study's costs were frozen.

---

## §8. Limitations and future work [UNDERSTAND + REASON]

### 8.1 Limitations (say them confidently; naming them builds credibility)

| Group | Limitation |
|---|---|
| Data | **Synthetic** dataset, not production estimates |
| Data | **One delay regime** (1 month), forced by month-level granularity |
| Data | **Amount is a proxy** (`proposed_credit_limit`) |
| Assumptions | **Cost matrix is assumed**, not measured (bounded by the sensitivity sweep) |
| Assumptions | Classifier choice was a tie; a different seed/fold could pick another |
| Framing | **No review-capacity limit** in the paper's policy |
| Framing | **No feedback loop**: in reality, our decisions change which labels we see later |
| Framing | **No drift adaptation**: fraud rate rose train → test (0.98% → 1.26%) and wasn't corrected |
| Other | `false_positive_cost` not scaled by amount (named scope boundary) |

### 8.2 Future work (from the paper)
More delay regimes (needs finer timestamps) · capacity-aware decisions · cost-sensitive
training · rolling-window evaluation for drift · fairness constraints · amount-scaled
false-positive cost.

### 8.3 About "V2" (the follow-up work): only if asked
After V1, the team ran a follow-up ("V2", `docs/v2/`) that tested six "what if" questions
(review capacity, 2-month delay, rolling retraining, feature drift, fairness, bias in the
cost estimate). **These are NOT in the submitted paper**, and the paper's limitations say those
things were not evaluated. **Do not volunteer V2.** If directly asked "did you try X?", the safe
answer is: *"Not in this paper; it's listed as future work. We did an exploratory follow-up
outside the paper, and the advantage held up there, but those results aren't part of
what we submitted."*

---

## §9. Presentation script [MEMORIZE YOUR PART]

**Length:** just under 10 minutes. **Speakers:** Ken 1–3 · Lawrence 4–6 · John Kelly 7–8 ·
Smith 9–11 · All 12. **Handoffs** are the last line of each part.
Full script with speaker notes: `docs/presentation_notes.md` (also embedded in `docs/presentation.pptx`).

### Ken: Problem and objectives (≈ 1:50)

**Slide 1, Title (0:20).** "Good morning. We are Ken, Lawrence, John Kelly, and Smith. Our project
is the Fraud Decision Desk: a system that decides what a bank should do with an application
**right now**, before anyone knows if it is fraud."

**Slide 2, The problem (0:50).** "When someone applies for a bank account, the bank has to decide
immediately: approve or refuse. But it only finds out if it was fraud weeks or months later,
usually 30 to 120 days. And some fraud is never reported at all. So the real question is not
'is this fraud?'. We can't know that yet. It's: **what should we do right now?**"

**Slide 3, Objectives (0:40).** "Four goals. One: treat fraud as a decision, not just a prediction.
Two: choose between approve, review, or block by comparing costs. Three: test it fairly, on months
the system never saw, and only once. Four: be honest about the limits. *Lawrence will explain how it works.*"

### Lawrence: Methodology and data (≈ 2:30)

**Slide 4, Our idea (1:00).** "Three steps. First, a model estimates a fraud risk, say 12.5%.
Second, it prices each option: letting it through risks the money; a manual check costs something
but stops most of the loss; blocking might turn away a genuine customer. Third, it **picks the
cheapest** and stamps it. A bigger credit limit means a bigger possible loss, so the same risk can
be approved for a small amount but checked for a large one."

**Slide 5, Fair test (0:50).** "One million applications from the Bank Account Fraud dataset, a
synthetic dataset built to look like real bank data. We kept time in order: learn on months 0–2,
tune on 3–4, test **once** on 5–6, 227,491 applications it never saw. Fraud answers arrive one
month late, so month 7, 96,843 applications or 9.68%, had no answer yet. We set those aside
instead of pretending they were safe."

**Slide 6, The data (0:40).** "Two things stood out. Fraud is rare, about 1 in 90, and it changes
over time, from 0.87% to 1.47%, which is why we test on later months. And most people ask for a
small limit, typically 200, but some ask for up to 2,100, about ten times more at risk. That's why
the desk looks at the amount. *John Kelly will now show you the system.*"

### John Kelly: System and live demo (≈ 3:15)

**Slide 7, The system (0:45).** "In: application details, the credit limit, fixed costs. Through: a
risk model, then the desk prices three options and picks the cheapest. Out: the risk, a stamp, the
reason, and for a batch, a ranked worklist. Let me show you."

**Slide 8, Live demo (2:30).** Steps:
1. *Everyday* → "1.3% risk, **APPROVED**; letting it through is the cheapest."
2. *Unusual* → "12.5% risk; at a 200 limit, still approved."
3. **Drag the limit to about 1,000** → "The risk stays 12.5%, but now it's **FOR REVIEW**. Bigger amount, bigger possible loss."
4. *Suspicious* → "Labelled fraud in the dataset. Almost 30% risk: **BLOCKED**."
5. *Check a batch → Use the sample* → "500 applications: 450 approved, 46 review, 4 blocked; the worklist puts the important ones first."
6. *Study results tab* → "And this is what we found. *Smith will explain.*"

**If the internet fails:** go to backup slides **13–14** and say the same lines.

### Smith: Results and conclusion (≈ 2:20)

**Slide 9, Result (1:00).** "The best simple rule cost 0.017798 per application; our desk cost
0.007491, **57.91% lower**. With 95% confidence the true reduction is between 53.95% and 62.13%,
so it isn't luck. The 50% cut-off fails because fraud is only about 1 in 100: the model almost
never says 'above 50%', so it approves nearly everything."

**Slide 10, It holds up (0:40).** "We halved and doubled each cost guess: still **at least 47.76%**
cheaper. The three models were within 1.07% of each other, under the 5% bar we set in advance, so
we chose the simplest. The decision rule does the work, not a fancier model."

**Slide 11, Conclusion (0:40).** "Weighing costs beats a fixed cut-off by 57.91%. Bigger amounts
get more caution automatically. We reported what we couldn't judge instead of hiding it. Limits:
synthetic data, one one-month delay, and credit limit as the amount. Thank you; we're happy to take
questions."

**Slide 12, Q&A (all).** Use §10. Supporting figures for answers are on slides **15–20**
(model comparison, calibration, test decisions, model weights, EDA figures).

---

## §10. Professor's Q&A bank ★

Owner = who answers first (others can add). ★ = most likely.

### 10.1 Problem and theory

**★ Q: In one sentence, what is your project?** *(Ken)*
A cost-sensitive policy that decides approve/review/block before fraud labels arrive, evaluated by
realized cost on a time-ordered test; it cut cost 57.91% vs the strongest baseline.

**★ Q: Why is this a decision problem and not a classification problem?** *(Ken)*
Because the bank must *act* before the label exists, and the two mistakes cost different amounts.
A score doesn't tell you what to do; you need to weigh the costs. Classification accuracy is just
a proxy, and a poor one under imbalance.

**Q: What is a delayed label? A censored label?** *(Ken)*
Delayed: the truth arrives after the decision (we simulate one month). Censored: it never arrives
within the data window (month 7). Censored ≠ legitimate, so we exclude and report those rows.

**★ Q: Why not just use accuracy?** *(Smith)*
98.9% of applications are legit, so "approve everyone" scores about 99% accuracy and catches zero
fraud. Our model hits 98.75% accuracy at 0.5 while catching only 18 of 2,861 frauds. Cost is what
the bank cares about.

**Q: What does "argmin of expected cost" mean?** *(Lawrence)*
For each application we compute the average cost of approving, reviewing and blocking given the
risk, and pick the smallest. It's the standard Bayes-optimal rule from cost-sensitive learning (Elkan 2001).

**Q: Why three actions instead of approve/block?** *(Lawrence)*
Real fraud teams use manual review; it's the right action when risk is uncertain. With only two
actions you'd be forced to either block good customers or approve risky ones.

### 10.2 Dataset

**★ Q: What dataset, and is it real?** *(Lawrence)*
BAF Suite v1 (Jesus et al., NeurIPS 2022): 1,000,000 bank-account applications, 1.1029% fraud. It's
**synthetic**, generated from a real anonymized dataset, so results are not production estimates.

**Q: Why this dataset?** *(Lawrence)*
It has a month index, which lets us simulate label delay and split by time; its ~1.1% fraud rate makes
the cost asymmetry matter; it has a public license and a citable source, so it's reproducible.

**Q: Why only a one-month delay?** *(Lawrence)*
BAF only records the month, so one month is the finest delay we can simulate honestly. More regimes are future work.

**Q: Why exclude month 7 instead of treating it as legit?** *(Ken)*
Its labels would only arrive after the data ends, so we don't know them. Calling them legit would
teach the model that unknown frauds are safe and inflate precision.

**Q: The paper says "transaction" but the app says "application". Which is it?** *(John Kelly)*
Each BAF row is a bank-account opening application; the paper uses "transaction" as the general term
for a decision event. Same rows.

**★ Q: Why isn't the credit limit a model feature, but it's used in the cost? Isn't that leakage?** *(Lawrence)*
It's known at decision time, so using it is not leakage. We **reserve** it to price the possible
loss (the amount at risk) rather than as a fraud signal, and it's very skewed (median 200, mean
515.85). The model estimates *how likely* fraud is; the amount says *how much is at stake*.

**Q: Why exclude `device_fraud_count`?** *(Lawrence)*
It may include fraud events recorded **after** the decision: that's future information (leakage).

**Q: What did your EDA show?** *(Lawrence)*
Fraud is rare and drifts (0.87% → 1.47%); credit limit is skewed; each feature is only a weak
signal (top correlations about 0.07); some categories are much riskier (housing BA 3.75%).
See slides 6, 19, 20 and the notebook.

### 10.3 Methodology and models

**★ Q: Why Logistic Regression if LightGBM had the lowest cost?** *(Lawrence)*
LightGBM was only 1.07% cheaper, under the 5% bar we set before modelling, and it didn't satisfy
the noise-band rule. That's a tie. With a tie we chose the simplest, most interpretable model.
Reporting 1.07% as a win would be overclaiming.

**Q: Explain how each of the three models works.** *(Lawrence)*
LR: weighted sum of features through an S-curve → probability. RF: many decision trees, each on a
random sample, vote. LightGBM: trees built in sequence, each correcting the previous ones' errors. (See §3.13.)

**Q: How did you choose hyperparameters?** *(Lawrence)*
Small documented grids (§3.13), expanding-window cross-validation on months 0–2 (2 folds), choosing
the setting with the lowest mean **realized cost after the policy**, not F1 or AUC.

**Q: Why only two folds? Isn't that weak?** *(Lawrence)*
With training months 0–2 and expanding windows, two folds is what the data allows without touching
validation/test months. It's also why we treat small gaps as noise and required a 5% margin.

**★ Q: What is calibration and why does it matter so much here?** *(Lawrence)*
A model is calibrated if its "10%" means about 10% really are fraud. Our policy multiplies the
risk by costs, so if the risk is off, every decision is off. We required ECE < 0.05; ours is
0.0033, so no calibration fix was needed.

**Q: How is ECE computed?** *(Lawrence)*
Split validation apps into 10 equal groups by predicted risk, compare average predicted vs actual
fraud rate in each, take the size-weighted average gap.

**Q: Your model over-estimates risk in every group. Is that a problem?** *(Lawrence)*
The gaps are small (ECE 0.0033, top group ≈ 8.3% predicted vs 6.8% actual). Over-estimating errs
toward caution, sending a few more to review. We documented it rather than "fixing" it, because
no measured failure justified a change.

**Q: Why no class weights or oversampling (e.g. SMOTE)?** *(Lawrence)*
They change the probabilities, and the policy needs honest probabilities. We handle the imbalance
in the **decision rule** (through costs), not in training.

**Q: Why no deep learning?** *(Lawrence)*
The project is scoped to traditional ML by design (neural nets, AutoML etc. are explicitly out of
scope). And our finding is that the **decision rule** matters more than the model; a fancier model
wasn't the bottleneck, as the tie between three different families shows.

**Q: How did you prevent data leakage?** *(Ken)*
Time-ordered split, test used once, preprocessing fit on training folds only, cost rate from training
months, calibration never on test, and post-decision/ID/time columns excluded. (§3.15.)

### 10.4 Costs and the policy

**★ Q: Where did the cost values come from? Aren't they made up?** *(Smith)*
They're **assumptions**, frozen before modelling and never tuned. We don't claim they're measured
bank costs, and we say so as a limitation. Our defence is the sensitivity test: halving or doubling
each one still leaves at least a 47.76% advantage. So the conclusion doesn't hinge on the exact values.

**Q: What does `residual_fraud_loss = 0.3` mean?** *(Lawrence)*
A manual check isn't perfect: when a fraud is reviewed, we assume 0.3 cost units of loss still get through.

**Q: How did you get `fraud_loss_rate`?** *(Lawrence)*
1 / 521.1626, the average credit limit in the **training** months. It scales fraud loss so an
average-size fraud costs 1.0, without using any test data.

**★ Q: Where exactly does the 57.91% come from? The model or the rule?** *(Smith)*
The rule. The same kinds of probabilities with a 50% cut-off were barely better than approving
everyone (≤ 5.97%). The argmin rule with amount scaling routes large, moderately risky applications
to review, which the 50% cut-off never does.

**Q: What's the review threshold?** *(Lawrence)*
It depends on the amount. At an average amount, review starts at 2.86% risk; at 1,000, 1.2%; at 200
there's no review zone. Block starts at 20% when a review zone exists. But the argmin is the real
rule; thresholds are just a view.

**Q: Why is the policy's precision only 6.5%? Isn't that bad?** *(Smith)*
It's intended. A check costs 0.02 while a missed fraud costs about the amount × rate (1.0 on
average), so it's worth checking many applications to catch a fraud. A rule chasing precision
would check fewer and miss more, raising total cost.

**Q: What happens when the thresholds "break"?** *(Lawrence)*
E.g. when review is never cheapest (small amounts). The threshold view fails, but the argmin still
picks the cheapest action. Three such edge cases are covered by unit tests.

### 10.5 Results and statistics

**★ Q: How do you know 57.91% isn't luck?** *(Smith)*
Bootstrap: we resampled the test set 1,000 times; 95% of the advantages fell between 53.95% and
62.13%. That excludes zero, and it's far above our 5% minimum effect.

**Q: Why compare to LightGBM + 0.5 and not approve-all?** *(Smith)*
Our rule is to compare against the **strongest** baseline. Beating a weak one would overstate the result.

**Q: Did you tune anything on the test set?** *(Ken)*
No. Costs, split, baselines and metric were fixed beforehand; the test window was used exactly once,
after everything was frozen.

**Q: Is the sensitivity result statistically significant too?** *(Smith)*
We computed bootstrap CIs only for the main comparison, not for each sensitivity row; we report the
sensitivity minimum (47.76%) as a robustness bound, not a significance claim.

**Q: What's the difference between ROC-AUC 0.8753 and your result?** *(Smith)*
AUC measures how well the model *ranks* fraud above legit, across all thresholds. It says nothing
about costs or which action to take. Our result is about the **decisions**.

### 10.6 System and implementation

**★ Q: Walk us through inputs, processes and outputs.** *(John Kelly)*
In: 28 application details, the credit limit, frozen costs. Process: preprocessing → Logistic
Regression risk → three expected costs → cheapest. Out: risk %, action stamp, reason, cost
breakdown; for batches a worklist and CSV.

**Q: Does the app use the same model as the paper?** *(John Kelly)*
Yes: it loads the same saved classifier and preprocessing pipeline from the `models/` folder.

**Q: How do you reproduce the results?** *(John Kelly)*
One command, `python -m src.pipeline`, runs all 8 steps with fixed seed 42 and gives identical
output; 68 automated tests check the logic.

**Q: Is it real-time? How fast is it?** *(John Kelly)*
We didn't measure latency, so we don't claim real-time performance. (A logistic regression is cheap
to run, but that's not a measured result.)

### 10.7 Limitations, challenges, improvements

**★ Q: What are the main limitations?** *(Smith)*
Synthetic data; one 1-month delay; credit limit as an amount proxy; assumed costs; no review-capacity
limit; no feedback loop; no drift correction.

**★ Q: Is this ready for a real bank?** *(Ken)*
No. It's a controlled backtest. It shows the approach works on a benchmark; a bank would need its own
data, measured costs, real amounts, and capacity limits.

**Q: What if the review team can only check a fixed number per day?** *(Smith)*
Not modelled in the paper; it's named future work. The natural fix: rank the review band by expected
saving and review the top K. (The app's "analyst tools" show this ranking view.)

**Q: What if fraudsters adapt / the data drifts?** *(Ken)*
We saw drift (0.98% → 1.26% from train to test) and documented it rather than correcting it.
Rolling retraining and drift monitoring are future work.

**Q: What about feedback loops?** *(Ken)*
In real use, what we approve/block changes which labels we ever see (blocked frauds may never be
confirmed). We assumed a fixed label set; that's a stated limitation.

**Q: What would you improve first?** *(Smith)*
Real amounts and measured costs; capacity-aware review; more delay regimes (needs finer timestamps);
cost-sensitive training compared against our decoupled design.

**Q: What was the hardest part?** *(any)*
The documents don't record this, so answer from your own experience. Two candidates the docs show
took deliberate effort: keeping time strictly ordered everywhere (CV, preprocessing, the cost rate)
so nothing leaked, and accepting a **non-finding** for the model comparison instead of declaring a
winner. Only say these if they're true for you.

### 10.8 Curveball questions ★ [REASON]

**Q: If a static 0.5 is so bad, why not just lower the threshold, say to 5%?** *(Smith)*
A single fixed threshold ignores the amount and the three-way choice. Our rule effectively uses a
different threshold for every amount, plus a separate block threshold. And choosing a threshold by
looking at results would be tuning; ours fall out of frozen costs.

**Q: Isn't your policy just a threshold rule in disguise?** *(Lawrence)*
Partly yes: for a fixed amount it's equivalent to two thresholds. But the thresholds move with the
amount and come from the costs rather than tuning, and the argmin still works where thresholds break.

**Q: Your recall is only 50%. Half of all fraud gets through!** *(Smith)*
Yes, and on purpose. By construction, the policy only approves when the expected loss of approving is
*lower* than the cost of checking: low risk, a small amount, or both. The objective is minimum
total cost, not maximum recall. It's still far better than the static baselines (LR at 0.5 caught
18 of 2,861).

**Q: If the costs were different, would your conclusion change?** *(Smith)*
The size changes (47.76% to 64.87% across our sweep), but the conclusion held in every scenario we
tested. Outside a 2× range we haven't tested, so we don't claim it.

**Q: Couldn't LightGBM be better with more tuning?** *(Lawrence)*
Possibly; we used small documented grids. But even a better ranker would be fed into the same
rule, and our evidence says the rule, not the ranker, drives the gain.

**Q: Why should we trust conclusions from synthetic data?** *(Ken)*
We don't claim production numbers. The claim is methodological: under realistic structure (imbalance,
drift, delay), the decision rule beats static thresholds by a wide, stable margin. That kind of
claim is exactly what a benchmark is for.

**Q: What's the single most important thing you learned?** *(any)*
"The decision rule, not the model, does the work": how you *use* a model's probabilities can matter
more than which model produced them.

---

## §11. Self-test (cover the answers, say them out loud)

1. What are the four must-know numbers and what does each mean?
2. Write the three expected-cost formulas from memory.
3. Why is accuracy misleading here? Give our 98.75% / 18-of-2,861 example.
4. Draw the month timeline (learn / tune / test / unknown) with row counts.
5. Why is month 7 excluded, and how many rows?
6. Why was Logistic Regression chosen? Say the 1.07% vs 5% rule.
7. What is calibration, what's our ECE, and why is it a gate?
8. Compute the Unusual example at 200 and 1,000 (§4.3).
9. Where do the cost values come from? (Answer honestly.)
10. Name five limitations.
11. Why is 6.5% precision acceptable?
12. What does the bootstrap CI tell us?

---

## §12. Where to find things

| Need | File |
|---|---|
| The submitted paper | `docs/main.tex` (PDF: `GroupNo.1_COM243ML.pdf`) |
| Every number with its source | `docs/paper/reference_sheet.md` |
| Policy details and edge cases | `docs/decision_policy.md` |
| Evaluation rules | `docs/evaluation_protocol.md` |
| Dataset, leakage, biases | `docs/data_card.md` |
| The "why" of the whole project | `docs/problem_framing.md` |
| Slides + speaker notes | `docs/presentation.pptx`, `docs/presentation_notes.md` |
| EDA | `notebooks/01_eda.ipynb`, `reports/figures/` |
| Results reports | `reports/decision_backtest.md`, `bootstrap.md`, `sensitivity.md`, `model_comparison.md` |
| App guide | `documentation/app_guide.md` |
