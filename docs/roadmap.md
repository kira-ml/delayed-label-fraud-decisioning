# Roadmap

> **Repository:** `delayed-label-fraud-decisioning`  
> **Course:** Introduction to Machine Learning — Final Group Project  
> **Institution:** National University Philippines  
> **Instructor:** Ken Oliver Caparros  
> **Document:** Roadmap  
> **Status:** v0.3 — restructured around course deliverables with supplementary depth  
> **Last updated:** YYYY-MM-DD

---

## 1. Purpose

This document defines the execution plan for the project across two layers:

1. **Primary (course requirement)** — Three-algorithm classification study,
   EDA, Streamlit application, and IMRaD paper.
2. **Supplementary (project depth)** — Cost-sensitive decision policy under
   delayed labels, already built and documented.

It exists to:

- Keep the course-required deliverables on schedule
- Prevent scope creep beyond what the course requires
- Make every additional task conditional on a measured result or a course
  requirement
- Give each phase a clear Definition of Done and, where appropriate, a stop
  criterion

**Rule:** No phase starts before the previous phase's Definition of Done is
satisfied.

---

## 2. Governing Principles

1. **Course-first.** The three-algorithm comparison, EDA, Streamlit app, and
   IMRaD paper are the priority. The supplementary cost-sensitive analysis
   is already done and documented.
2. **Pain-point-driven.** Every addition must trace back to the fraud
   decision problem: decide now, when labels arrive later.
3. **Scope discipline.** Anything not required by the course or by a
   measured failure is out of scope.
4. **Reproducibility.** Fixed seeds, documented versions, one-command
   reproduction.
5. **Honest reporting.** Failures and non-findings are reported, not hidden.

If any of these is violated, the roadmap is not being followed.

---

## 3. Scope Summary

### In scope — Primary (Course Requirement)

- Exploratory data analysis with ≥5 meaningful visualizations
- Data preparation: missing values, duplicates, outliers, encoding, scaling,
  feature selection, class imbalance handling
- **Exactly three traditional algorithms:** Logistic Regression, Random
  Forest, LightGBM
- Fair experimental design: same split, same preprocessing, same 5-fold
  time-series CV, same primary metric (Macro F1)
- Documented hyperparameter tuning
- Model selection based on validation results
- Final evaluation once on the untouched test set
- Deployable Streamlit application
- IMRaD paper in IEEE format
- Technical documentation, data dictionary, contribution record, ownership
  declaration

### In scope — Supplementary (Project Depth, Complete)

- Chronological transaction replay from BAF
- Simulated delayed and censored labels (1-month regime)
- Chronological train / validation / test splits
- Cost-sensitive decision policy over `approve` / `review` / `block`
- Cost-based temporal backtest
- Calibration measurement (Brier, ECE)
- Sensitivity analysis on all four cost parameters
- Bootstrap confidence intervals
- Reproducible evaluation

### Out of scope

- Streaming infrastructure (Kafka, RabbitMQ, Faust)
- Service layer (FastAPI, Uvicorn)
- Online learning (SGD, Passive-Aggressive)
- PU learning
- Delayed-label correction models
- Drift detectors
- Graph neural networks or graph features
- Federated learning
- **Neural networks, deep learning, transformers, LLMs, AutoML**
- Docker / Kubernetes / CI/CD
- MLflow / W&B / DVC
- Model registry, feature store, hyperparameter search frameworks
- Multiple delay regimes (only 1-month regime in current build)
- Capacity-aware decisioning
- Rule-based threshold baseline

---

## 4. Primary Roadmap — Course Deliverables

This is the primary schedule. All course requirements must be satisfied
before the submission deadline.

### Phase P1 — Exploratory Data Analysis

**Goal:** Understand the dataset and produce findings that drive
preprocessing, feature selection, algorithm choice, and evaluation strategy.

**Deliverable:** `notebooks/01_eda.ipynb` and an EDA summary section in the
IMRaD paper.

**Tasks:**

1. Load `data/original/Base.csv`
2. Report dimensions, dtypes, feature definitions, summary statistics
3. Audit missing values, duplicates, inconsistent entries, impossible values
4. Plot univariate distributions of important variables
5. Analyze feature–target relationships (correlation, association)
6. Report class distribution and imbalance concerns
7. Investigate outliers (distinguish errors from legitimate extremes)
8. Produce **≥5 meaningful visualizations**, each with a written finding
9. Write an EDA findings summary that informs preprocessing, feature
   selection, algorithm choice, or evaluation strategy

**Definition of Done:**

- [ ] EDA notebook runs end-to-end
- [ ] ≥5 visualizations, each with a written finding
- [ ] Every finding maps to a decision (preprocessing, feature, algorithm,
      or evaluation)
- [ ] Summary section ready to paste into the IMRaD paper

**Stop criterion:** EDA is complete when every required audit (missing,
duplicates, distributions, relationships, imbalance, outliers) has a written
finding and every finding has a decision.

---

### Phase P2 — Data Preparation

**Goal:** Build a preprocessing pipeline that is fit on training data only
and applied unchanged to test data.

**Deliverable:** `notebooks/02_preprocessing.ipynb` and
`models/preprocessing.pkl`.

**Tasks:**

1. Handle missing values (documented per column)
2. Handle duplicates (documented)
3. Handle outliers (documented as errors vs. legitimate extremes)
4. Encode categoricals per algorithm:
   - Logistic Regression: one-hot
   - Random Forest: ordinal
   - LightGBM: native categorical
5. Scale numerics per algorithm:
   - Logistic Regression: StandardScaler
   - Random Forest, LightGBM: none
6. Select features (driven by EDA findings)
7. Handle class imbalance:
   - Logistic Regression: `class_weight='balanced'`
   - Random Forest: `class_weight='balanced_subsample'`
   - LightGBM: `is_unbalance=True`
8. Save the pipeline to `models/preprocessing.pkl`
9. Document leakage prevention: preprocessing fit only on training folds

**Definition of Done:**

- [ ] Preprocessing notebook runs end-to-end
- [ ] Every preprocessing decision traced to an EDA finding or course
      requirement
- [ ] Pipeline saved and loadable
- [ ] Leakage audit completed

**Stop criterion:** preprocessing is complete when the same fitted pipeline
can be applied to any test row without recomputation.

---

### Phase P3 — Three-Algorithm Training

**Goal:** Train Logistic Regression, Random Forest, and LightGBM under
identical conditions.

**Deliverable:** `notebooks/03_model_training.ipynb` and
`src/models/train_compare.py`.

**Tasks:**

1. Define the chronological 80/20 split:
   - Train: months 0–5
   - Test: months 6–7
2. Define 5-fold time-series CV on the training split
3. For each algorithm:
   - Define a small hyperparameter grid
   - Run grid search within the CV folds
   - Record mean ± SD of Macro F1 across folds
   - Record supporting metrics: accuracy, per-class precision/recall/F1,
     ROC-AUC
4. Report results for all three algorithms in a single comparison table

**Definition of Done:**

- [ ] Three algorithms trained under identical folds and preprocessing
- [ ] Hyperparameter grids documented
- [ ] Cross-validation results table complete with mean ± SD
- [ ] Comparison documented in `reports/model_comparison.md`

**Stop criterion:** the phase is complete when all three algorithms have CV
results reported on the same metric and folds. No further tuning after the
test set is touched.

---

### Phase P4 — Final Evaluation and Model Selection

**Goal:** Select the best model and evaluate it once on the untouched test
set.

**Deliverable:** `notebooks/04_evaluation.ipynb`,
`src/models/evaluate_compare.py`, `models/best_model.pkl`, and the results
section of the IMRaD paper.

**Tasks:**

1. Select the best model based on validation Macro F1, with interpretability,
   speed, and practical suitability as tiebreakers
2. Justify the selection in writing
3. Retrain the selected model on the full training split
4. Evaluate **once** on the untouched test set
5. Report:
   - Macro F1 (primary)
   - Accuracy
   - Per-class precision, recall, F1
   - Confusion matrix
   - ROC-AUC (informational)
6. Write failure analysis (which errors dominate, what they mean)
7. Save the final model to `models/best_model.pkl`

**Definition of Done:**

- [ ] Selected model justified in writing
- [ ] Final model trained on full training split
- [ ] Test evaluated exactly once
- [ ] All required metrics reported
- [ ] Confusion matrix included
- [ ] Failure analysis written

**Stop criterion:** the phase is complete when the test set has been
evaluated once and no further tuning is permitted.

---

### Phase P5 — Deployable Application

**Goal:** Build a working Streamlit application that loads the saved best
model and preprocessing pipeline.

**Deliverable:** `app/streamlit_app.py`, deployed URL, and setup
instructions.

**Tasks:**

1. Build a Streamlit form for transaction feature input
2. Load `models/best_model.pkl` and `models/preprocessing.pkl`
3. Apply the same preprocessing used at training time
4. Display predicted class and predicted probability
5. Show the model name and short feature explanations
6. Handle missing, invalid, and out-of-range inputs gracefully
7. Display understandable error messages
8. Test with valid, invalid, and boundary inputs
9. Deploy to Streamlit Cloud
10. Write setup instructions and app guide

**Definition of Done:**

- [ ] App runs locally with `streamlit run app/streamlit_app.py`
- [ ] App loads the same model and preprocessing reported in the paper
- [ ] All three input categories tested: valid, invalid, boundary
- [ ] Deployed URL works
- [ ] `documentation/app_guide.md` and
      `documentation/technical_documentation.md` written

**Stop criterion:** the phase is complete when the deployed URL works and
the local version reproduces the same predictions.

---

### Phase P6 — IMRaD Paper and Documentation

**Goal:** Write the complete IMRaD paper in IEEE format and finish all
documentation.

**Deliverable:** `paper/paper.docx`, `paper/paper.pdf`,
`documentation/data_dictionary.md`,
`documentation/technical_documentation.md`,
`documentation/contribution_record.md`,
`documentation/ownership_declaration.md`.

**Tasks:**

1. Write the paper in IMRaD sections:
   - Title, abstract, keywords
   - Introduction (problem, objective, significance, related work)
   - Methods (dataset, EDA procedure, preprocessing, three algorithms,
     tuning, metrics)
   - Results (EDA findings, comparison table, validation, final test,
     confusion matrix, app evidence)
   - Discussion (why selected model performed best, errors, tradeoffs)
   - Conclusion and recommendations
   - References (IEEE numbered, in order of appearance)
   - Appendices (data dictionary, contribution record, signed declaration)
2. Use IEEE conference paper format
3. Cite sources in the order they first appear with bracketed numbers
4. Create the data dictionary
5. Create the technical documentation
6. Create the contribution record
7. Create the ownership and authorship declaration
8. Sign the declaration (instructor + all group members)

**Definition of Done:**

- [ ] `paper/paper.docx` and `paper/paper.pdf` complete
- [ ] IEEE numbered citations match the reference list
- [ ] All required deliverables present
- [ ] Declaration signed by instructor and all members

**Stop criterion:** the project is complete when all seven required
deliverables are submitted and the declared URLs and files open successfully.

---

## 5. Supplementary Roadmap — Project Depth

This layer is already built and documented. It is preserved here for
reference and for future work.

### Status Summary

| Component | Status |
|---|---|
| `src/data/load.py` | ✅ Complete |
| `src/data/simulate_delay.py` | ✅ Complete |
| `src/data/split.py` | ✅ Complete |
| `src/models/train_baseline.py` | ✅ Complete |
| `src/models/score.py` | ✅ Complete |
| `src/policy/decide.py` | ✅ Complete |
| `src/evaluation/backtest.py` | ✅ Complete |
| `src/evaluation/calibration.py` | ✅ Complete |
| `src/evaluation/sensitivity.py` | ✅ Complete |
| `src/evaluation/bootstrap.py` | ✅ Complete |
| `src/pipeline.py` | ✅ Complete |
| `tests/test_policy.py`, `tests/test_backtest.py` | ✅ 13 tests passing |
| `reports/mvp_backtest.md` | ✅ Complete |
| `reports/sensitivity.md` | ✅ Complete |
| `reports/bootstrap.md` | ✅ Complete |

### Key Result

Under a 1-month delayed-label regime, the cost-sensitive policy reduces
realized cost per transaction by **56.87%** relative to the strongest
baseline, with a 95% bootstrap confidence interval of **[52.77%, 60.91%]**.

### Deferred Supplementary Work

These are not part of the course submission. Each is a candidate for future
work and each would require its own stop criterion, in the same format as
`docs/architecture.md` §9.2.

- Additional delay regimes (2-month, 3-month)
- Rule-based threshold baseline
- Capacity-aware decisioning
- Rolling-window evaluation
- Cost-sensitive training
- Calibration application (only if ECE drifts beyond 0.05)
- Fairness-aware policy constraints
- Drift detection

**Rule for adding deferred work:** the addition must address a specific
measured failure, and its stop criterion must be written before work starts.

---

## 6. Timeline

The primary roadmap is scheduled across four working phases. The timeline is
flexible and gated by Definition of Done, not by calendar dates.

| Phase | Focus | Primary deliverable |
|---|---|---|
| P1 | Exploratory data analysis | `notebooks/01_eda.ipynb` |
| P2 | Data preparation | `notebooks/02_preprocessing.ipynb`, `models/preprocessing.pkl` |
| P3 | Three-algorithm training | `notebooks/03_model_training.ipynb`, `reports/model_comparison.md` |
| P4 | Final evaluation and selection | `notebooks/04_evaluation.ipynb`, `models/best_model.pkl` |
| P5 | Deployable application | `app/streamlit_app.py`, deployed URL |
| P6 | IMRaD paper and documentation | `paper/paper.docx`, `paper/paper.pdf` |

Phases P1–P4 run in sequence. Phase P5 can start as soon as P4 produces a
saved model. Phase P6 can start in parallel once P3 produces validation
results.

---

## 7. What Is Not on This Roadmap

Explicitly deferred and not scheduled:

- Neural networks, deep learning, transformers, LLMs, AutoML
- Streaming infrastructure
- Service layer
- Online learning
- PU learning
- Delayed-label correction
- Drift detectors
- Graph neural networks
- Federated learning
- Docker / Kubernetes / CI/CD
- Model registry, feature store, hyperparameter search frameworks
- Capacity-aware scheduling as the default policy
- Fairness-aware policy constraints
- Bandit or RL policies

These are excluded from the course submission. Each may be revisited after
submission if a measured failure justifies it and a stop criterion is
defined before work begins.

---

## 8. Gating Rules

### 8.1 Primary Gates

- Phase P2 does not start until P1 is done.
- Phase P3 does not start until P2 is done (preprocessing pipeline saved).
- Phase P4 does not start until P3 is done (all three algorithms compared).
- Phase P5 does not start until P4 is done (best model saved).
- Phase P6 does not start until P3 is done (validation results available).
- The test set is used **once**, in P4. No exceptions.

### 8.2 Supplementary Gates

- No supplementary work starts until primary phases P1–P4 are complete.
- Any new supplementary addition must have its own stop criterion written
  before work starts.
- If a supplementary addition does not exceed the noise band and effect
  size, it is reported as a non-finding and not adopted.

---

## 9. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Class imbalance biases model selection | Macro F1 as primary; per-class metrics reported |
| Data leakage through preprocessing | Preprocessing fit on training folds only |
| Test set contamination | Test used once, after model selection |
| Algorithm comparison unfair | Same split, preprocessing, folds, metric |
| EDA produces decorative charts | Every figure must lead to a finding or decision |
| Streamlit app crashes on invalid input | Validate inputs; test boundary cases |
| Paper exceeds or falls short of length | IEEE format, 6–10 pages excluding appendices |
| Missing deliverable at submission | Checklist tracks all 7 required deliverables |
| Documentation drift | If docs disagree with code, code wins and docs are updated |

---

## 10. Definition of Done for the Roadmap

### 10.1 Primary

- [ ] Phase P1 complete: EDA notebook with ≥5 meaningful visualizations
- [ ] Phase P2 complete: preprocessing pipeline saved and documented
- [ ] Phase P3 complete: three-algorithm comparison with CV results
- [ ] Phase P4 complete: final test evaluation once
- [ ] Phase P5 complete: Streamlit app deployed and tested
- [ ] Phase P6 complete: IMRaD paper and all documentation submitted
- [ ] All 7 required deliverables present and openable
- [ ] Ownership declaration signed by instructor and all members
- [ ] Repository and ZIP archive accessible

### 10.2 Supplementary

- [x] All supplementary pipeline scripts implemented
- [x] Supplementary reports written
- [x] Tests passing (13 tests)
- [x] Reproducibility verified byte-for-byte

---

## 11. Guiding Rules

### 11.1 Primary

> The course deliverables come first. Anything that does not contribute to
> the three-algorithm comparison, the Streamlit app, the EDA, or the IMRaD
> paper is deferred.

> The test set is used **once**. Any result that touches it before model
> selection is invalid.

### 11.2 Supplementary

> Each supplementary addition is justified by a measured result, not by the
> desire to build more.

> If a supplementary addition cannot point to a number that made it
> necessary, it does not happen.

---

## 12. Changelog

| Date | Change | Reason |
|---|---|---|
| YYYY-MM-DD | Initial roadmap | Project start |
| YYYY-MM-DD | Aligned with Week 1 MVP and stop criteria | Project planning |
| YYYY-MM-DD | Restructured into primary (course deliverables) and supplementary (project depth); added phases P1–P6 with Definition of Done; moved supplementary work to a status summary; added gating rules; updated risks and DoD | Align with course requirements |
