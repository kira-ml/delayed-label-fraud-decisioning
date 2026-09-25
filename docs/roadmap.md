# Roadmap

> **Repository:** `delayed-label-fraud-decisioning`  
> **Course:** Introduction to Machine Learning — Final Group Project  
> **Institution:** National University Philippines  
> **Instructor:** Ken Oliver Caparros  
> **Document:** Roadmap  
> **Status:** v1.0 — unified decision pipeline  
> **Last updated:** 2026-09-25

---

## 1. Purpose

This document defines the execution plan for the project. There is **one**
pipeline: a cost-sensitive fraud decision pipeline. The classifier is an
input to the policy. The policy is the product. The backtest is the
evidence.

It exists to:

- Track the actual execution of the pipeline
- Define each phase's Definition of Done and stop criterion
- Make every addition conditional on a measured failure
- Keep the course deliverables (EDA, three-algorithm comparison, Streamlit
  app, IMRaD paper) aligned with the decision pipeline

**Rule:** No phase starts before the previous phase's Definition of Done is
satisfied.

**Rule:** A component is only added if a measured failure justifies it, and
its stop criterion is written before work starts.

---

## 2. Governing Principles

1. **Decision-first.** The object of study is the decision policy. The
   classifier is an input. The backtest is the evidence.
2. **Pain-point-driven.** Every addition must trace back to the fraud
   decision problem: decide now, when labels arrive later.
3. **Cost-based evaluation.** Realized cost per transaction is the primary
   metric. Classification metrics are supporting evidence.
4. **Temporal discipline.** No random splits. No test-window tuning. The
   test window is used exactly once.
5. **Reproducibility.** Fixed seeds, documented versions, one-command
   reproduction.
6. **Honest reporting.** Failures and non-findings are reported, not
   hidden.

If any of these is violated, the roadmap is not being followed.

---

## 3. Scope Summary

### In scope

**Framing and evaluation**

- Decision-centric problem framing
- Frozen cost matrix in `configs/costs.yaml`
- Chronological delay-aware split (train 0-2, val 3-4, test 5-6,
  censored 7)
- Calibration gate (ECE < 0.05)
- Cost-based backtest vs. canonical baselines
- Bootstrap CIs and 2× sensitivity sweep

**Classification methodology**

- Three traditional classifiers: Logistic Regression, Random Forest,
  LightGBM
- Identical folds, preprocessing, and cost criterion
- Noise-band guard on selection

**Data understanding**

- EDA with ≥5 meaningful visualizations
- Data dictionary with source-time availability
- Leakage register

**Deployment and reporting**

- Streamlit app showing `p_fraud` and routed action
- IMRaD paper in IEEE format
- Technical documentation, data dictionary, contribution record,
  ownership declaration
- Reproducibility from raw data, configs, seeds

### Out of scope

- Neural networks, deep learning, transformers, LLMs, AutoML
- Streaming infrastructure
- Service layer
- Online learning
- PU learning
- Delayed-label correction models
- Drift detectors
- Graph neural networks
- Federated learning
- Docker / Kubernetes / CI-CD
- MLflow / W&B / DVC
- Model registry, feature store, hyperparameter search frameworks
- Capacity-aware decisioning
- Multiple delay regimes
- Rule-based threshold baseline
- Fairness-aware policy constraints
- Bandit or RL policies

---

## 4. Pipeline Phases

The pipeline runs in eight steps:
`load → simulate_delay → split → train_compare → evaluate_compare →
score → decide → backtest`

The phases below group those steps into execution units.

### Phase P1 — Exploratory Data Analysis

**Goal:** Understand the dataset and produce findings that drive
preprocessing, feature selection, classifier choice, and evaluation
strategy.

**Deliverable:** `notebooks/01_eda.ipynb` and an EDA summary in the paper.

**Definition of Done:**

- [x] EDA notebook runs end-to-end
- [x] ≥5 visualizations, each with a written finding
- [x] Every finding maps to a decision
- [x] Summary ready for the IMRaD paper

**Stop criterion:** complete when every required audit has a written
finding and every finding has a decision.

---

### Phase P2 — Data Preparation

**Goal:** Build a preprocessing pipeline fit on training data only and
applied unchanged to validation and test.

**Deliverable:** `notebooks/02_preprocessing.ipynb` and
`models/preprocessing.pkl`.

**Definition of Done:**

- [x] Preprocessing notebook runs end-to-end
- [x] Every decision traced to an EDA finding or the framing
- [x] Pipeline saved and loadable
- [x] Leakage audit completed
- [x] No class weighting applied (calibration must be preserved)

**Stop criterion:** complete when the same fitted pipeline can be applied
to any test row without recomputation.

---

### Phase P3 — Classifier Comparison

**Goal:** Train Logistic Regression, Random Forest, and LightGBM under
identical folds, preprocessing, and cost criterion.

**Deliverable:** `src/models/train_compare.py`,
`reports/model_comparison.md`, `reports/cv_results.json`.

**Definition of Done:**

- [x] Three classifiers trained under identical folds
- [x] Hyperparameter grids documented
- [x] CV results table complete with mean ± SD realized cost
- [x] Supporting classification metrics reported

**Stop criterion:** complete when all three classifiers have CV results
reported on the same metric and folds.

---

### Phase P4 — Calibration and Selection

**Goal:** Enforce the calibration gate and select the classifier as a
policy input.

**Deliverable:** `src/models/evaluate_compare.py`,
`models/best_model.pkl`, `models/preprocessing.pkl`.

**Definition of Done:**

- [x] Calibration gate run: ECE = 0.0033 < 0.05
- [x] Selection by validation realized cost with the noise-band guard
- [x] Non-finding reported when the top gap is < 5%
- [x] Tie broken by simplicity (LR > RF > LGBM)
- [x] Selected classifier: LogisticRegression
- [x] Test window evaluated once, after selection

**Stop criterion:** complete when the test window has been evaluated once
and no further tuning is permitted.

---

### Phase P5 — Policy Evaluation

**Goal:** Apply the argmin expected-cost policy, evaluate on the test
window, and validate the result with bootstrap CIs and cost sensitivity.

**Deliverable:** `src/policy/decide.py`, `src/evaluation/backtest.py`,
`src/evaluation/bootstrap.py`, `src/evaluation/sensitivity.py`,
`reports/decision_backtest.md`, `reports/bootstrap.md`,
`reports/sensitivity.md`.

**Definition of Done:**

- [x] Policy cost/txn = 0.007491 vs strongest baseline 0.018737
- [x] Policy advantage = 60.02%
- [x] Bootstrap 95% CI on advantage = [56.00%, 64.16%] (excludes zero)
- [x] Sensitivity minimum advantage = 50.38% across 2× sweep
- [x] Amount-scaled `fraud_loss` adopted
- [x] Censored count reported: 96,843 (9.68%)
- [x] Failure analysis written
- [x] Stop verdict recorded

**Stop criterion:** complete when the primary metric, its CI, and the
sensitivity minimum are reported in `reports/decision_backtest.md`.

---

### Phase P6 — Deployable Application

**Goal:** Build a Streamlit app that loads the saved classifier and
preprocessing pipeline and shows both `p_fraud` and the routed action.

**Deliverable:** `app/streamlit_app.py`, deployed URL,
`documentation/app_guide.md`.

**Definition of Done:**

- [x] App runs locally with `streamlit run app/streamlit_app.py`
- [x] App loads the same classifier and preprocessing reported in the
      paper
- [x] Valid, invalid, and boundary inputs tested
- [x] Deployed URL works
- [x] `documentation/app_guide.md` and
      `documentation/technical_documentation.md` written

**Stop criterion:** complete when the deployed URL works and the local
version reproduces the same predictions.

---

### Phase P7 — IMRaD Paper and Submission

**Goal:** Write the IMRaD paper in IEEE format and finish all submission
artifacts.

**Deliverable:** `paper/paper.docx`, `paper/paper.pdf`,
`documentation/contribution_record.md`,
`documentation/ownership_declaration.md`, ZIP archive.

**Definition of Done:**

- [ ] `paper/paper.docx` and `paper/paper.pdf` complete
- [ ] IEEE numbered citations match the reference list
- [ ] Contribution record signed
- [ ] Ownership declaration signed
- [ ] Dataset package assembled
- [ ] ZIP archive in the required layout
- [ ] Final checklist against the course PDF

**Stop criterion:** complete when all required deliverables are submitted
and every declared URL and file opens successfully.

---

## 5. Current Status

| Phase | Status |
|---|---|
| P1 EDA | Complete |
| P2 Data preparation | Complete |
| P3 Classifier comparison | Complete |
| P4 Calibration and selection | Complete |
| P5 Policy evaluation | Complete |
| P6 Deployable application | Complete |
| P7 Paper and submission | In progress |

**Verified numbers (from the latest pipeline run):**

| Fact | Value |
|---|---|
| Selected classifier | LogisticRegression (`C=10.0`, `max_iter=1000`) |
| Selection rule | Noise-band guard: LGBM vs LR gap 1.07% < 5% |
| Policy cost/txn | 0.007491 |
| Strongest baseline | 0.018737 |
| Policy advantage | 60.02% |
| Bootstrap CI | [56.00%, 64.16%] |
| Sensitivity minimum | 50.38% at `review_cost=0.04` |
| Calibration ECE | 0.0033 |
| Test rows | 227,491 |
| Censored rows | 96,843 (9.68%) |
| Tests | 58 / 58 passing |

---

## 6. What Remains

### Required for submission

- [ ] Generate `paper/paper.docx` from `paper/paper_imrad.md`
- [ ] Generate `paper/paper.pdf`
- [ ] Sign `documentation/contribution_record.md`
- [ ] Sign `documentation/ownership_declaration.md`
- [ ] Assemble ZIP in `GROUPNAME_PROJECTTITLE/` layout
- [ ] Final checklist against the course PDF

### Documentation follow-ups (non-blocking)

- [ ] Add M4 entry to `TODO.md` if `technical_documentation.md` still
      describes retired architecture in any section
- [ ] Mark `docs/architecture.md` and `docs/mvp_2_weeks.md` as superseded
      at the top of each file
- [ ] Update `docs/mvp_architecture.md` §13 to remove deviations that no
      longer exist

### Deferred (candidate future work)

Each deferred item requires a specific measured failure and its own stop
criterion before work begins.

- Additional delay regimes (2-month, 3-month)
- Rule-based threshold baseline
- Capacity-aware decisioning
- Rolling-window evaluation
- Cost-sensitive training
- Calibration application (only if ECE drifts beyond 0.05)
- Fairness-aware policy constraints
- Drift detection

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
- Docker / Kubernetes / CI-CD
- Model registry, feature store, hyperparameter search frameworks
- Capacity-aware scheduling as the default policy
- Fairness-aware policy constraints
- Bandit or RL policies

These are excluded from the submission. Each may be revisited after
submission if a measured failure justifies it and a stop criterion is
defined before work begins.

---

## 8. Gating Rules

- P2 does not start until P1 is complete.
- P3 does not start until P2 is complete.
- P4 does not start until P3 is complete.
- P5 does not start until P4 is complete.
- P6 does not start until P5 is complete.
- P7 does not start until P3 is complete (paper methods section needs CV
  results) and P5 is complete (paper results section needs the backtest).
- The test window is used **once**, in P4. No exceptions.
- Any new addition requires its own stop criterion written before work
  starts.
- If an addition does not exceed the noise band and the effect size, it is
  reported as a non-finding and not adopted.

---

## 9. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Class imbalance biases classifier selection | Selection by realized cost, not macro F1 |
| Data leakage through preprocessing | Preprocessing fit on training folds only |
| Test-window contamination | Test used once, after selection |
| Classifier comparison unfair | Same split, preprocessing, folds, cost criterion |
| EDA produces decorative charts | Every figure must lead to a finding or decision |
| Streamlit app crashes on invalid input | Validate inputs; test boundary cases |
| Calibration drifts after retraining | Re-run `calibration.py` after each retrain |
| Cost matrix unrealistic | 2× sensitivity sweep over all four parameters |
| Paper exceeds or falls short of length | IEEE format, 6-10 pages excluding appendices |
| Missing deliverable at submission | Checklist tracks all 7 required deliverables |
| Documentation drift | If docs disagree with code, code wins and docs are updated |

---

## 10. Definition of Done for the Roadmap

### 10.1 Pipeline

- [x] EDA notebook complete
- [x] Preprocessing pipeline saved and documented
- [x] Three classifiers compared under identical conditions
- [x] Calibration gate passed (ECE = 0.0033)
- [x] Classifier selected by noise-band guard (LR)
- [x] Policy evaluated once on the test window
- [x] Bootstrap CIs computed
- [x] 2× sensitivity sweep completed
- [x] Streamlit app deployed and verified
- [x] Reports regenerated with current numbers

### 10.2 Submission

- [ ] IMRaD paper complete (DOCX + PDF)
- [ ] Technical documentation final
- [ ] Data dictionary final
- [ ] Contribution record signed
- [ ] Ownership declaration signed
- [ ] Dataset package assembled
- [ ] ZIP archive in required layout
- [ ] Final checklist against the course PDF

---

## 11. Guiding Rules

> The decision is the object of study. The classifier is an input. The
> backtest is the evidence. The cost matrix is the assumption. The paper
> is the argument.

> The test window is used **once**. Any result that touches it before the
> model and policy are frozen is invalid.

> A claim is only a finding if the 95% bootstrap CI on the cost advantage
> excludes zero and the relative reduction exceeds 5%. Everything else is
> a non-finding, reported as such.

> Each addition is justified by a measured result, not by the desire to
> build more. If an addition cannot point to a number that made it
> necessary, it does not happen.

---

## 12. Changelog

| Date | Change | Reason |
|---|---|---|
| 2026-09-22 | Initial roadmap | Project start |
| 2026-09-22 | Aligned with Week 1 MVP and stop criteria | Project planning |
| 2026-09-22 | Restructured into primary (course deliverables) and supplementary (project depth) | Align with course requirements |
| 2026-09-25 | v1.0 — first-principles revision; two-layer architecture removed; single decision pipeline adopted; phases restructured around the pipeline steps; primary metric changed to realized cost; noise-band guard added; current status section added; what-remains section added | Derive from `problem_framing.md` v1.0, `evaluation_protocol.md` v1.0, and the verified pipeline run |
