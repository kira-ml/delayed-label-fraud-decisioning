# Roadmap

> **Repository:** `delayed-label-fraud-decisioning`  
> **Document:** Roadmap  
> **Status:** v0.2 — aligned with Week 1 MVP and stop criteria  
> **Last updated:** YYYY-MM-DD

---

## 1. Purpose

This document defines the weekly plan for the project.

It exists to:

- Keep Week 1 focused on the minimum end-to-end loop
- Prevent scope creep into later weeks before Week 1 is measured
- Make every Week 2+ addition conditional on a measured Week 1 result
- Give each week a clear Definition of Done and a clear stop criterion

**Rule:** No week starts before the previous week's stop criteria are evaluated and reported.

---

## 2. Governing Principles

1. **Pain-point-driven.** Every addition must trace back to the fraud decision problem: decide now, when labels arrive later.
2. **Scope discipline.** Anything not required to reduce realized cost per transaction under the same split, delay regime, cost matrix, and budget is out of scope.
3. **Stop-criteria gated.** Every phase has a stop criterion in `architecture.md` Section 9. Weeks do not continue past a stop condition.
4. **Measured failure required.** A Week N+1 addition is only allowed if a specific Week N result is measurably insufficient.
5. **One change at a time.** Weeks 2–4 add one improvement each, not a bundle.

If any of these is violated, the roadmap is not being followed.

---

## 3. Scope Summary

### In scope for the project

- Chronological transaction replay from a static dataset
- Simulated delayed and censored labels under fixed regimes
- Chronological train / validation / test splits
- A calibrated fraud probability model
- A cost-sensitive decision policy with three actions: `approve`, `review`, `block`
- A cost-based temporal backtest
- Reproducible evaluation

### Out of scope for all weeks unless a measured failure justifies otherwise

- Streaming infrastructure (Kafka, RabbitMQ, Faust)
- Service layer (FastAPI, Uvicorn)
- Dashboards (Streamlit, Grafana, Dash)
- Online learning (SGD, Passive-Aggressive)
- PU learning
- Delayed-label correction models
- Drift detectors
- Graph neural networks or graph features
- Federated learning
- Deep learning
- Docker / Kubernetes
- MLflow / W&B / DVC
- Model registry, feature store, hyperparameter search frameworks

Each item on this list is allowed only if:

1. A specific Week 1 result is measurably insufficient, and
2. The addition has its own stop criterion in the same format as `architecture.md` Section 9.2, written before work starts.

---

## 4. Week 1 — Baseline End-to-End Loop

**Goal:** Prove the full loop works end-to-end with the simplest possible components.

**Primary deliverable:** `reports/week1_backtest.md`, produced by a single reproducible command.

### Tasks

1. **Verify BAF timestamp granularity** (blocking, per `data_card.md` Section 4.6)
   - Confirm day-level, month-level, or synthesized
   - Finalize day-based or month-based delay regimes
   - Record the result in `data_card.md`

2. **Load and normalize BAF**
   - `src/data/load.py` produces `data/interim/transactions.parquet`
   - Schema matches `data_card.md` Section 3

3. **Simulate delayed labels**
   - `src/data/simulate_delay.py`
   - Fixed Δ per regime: 7 / 30 / 90 days (or month-level fallback)
   - Censored labels marked, not treated as negative
   - `configs/delay.yaml` written

4. **Chronological splits**
   - `src/data/split.py`
   - Train / validation / test split by `decision_time`, with `label_time` maturation constraint
   - `configs/splits.yaml` written
   - Censored counts reported per split and per regime

5. **Train baseline model**
   - `src/models/train_baseline.py`
   - LightGBM binary classifier
   - Early stopping on validation
   - Model, feature list, training config saved to `artifacts/`

6. **Score test set**
   - `src/models/score.py`
   - Attaches `p_fraud` to each test transaction

7. **Apply decision policy**
   - `src/policy/decide.py`
   - Argmin of expected cost, three actions
   - Cost matrix fixed in `configs/costs.yaml` with canonical key `residual_fraud_loss`
   - Policy config in `configs/policy.yaml`

8. **Write action log**
   - `src/policy/log_actions.py`
   - Schema from `decision_policy.md` Section 10, including all three expected costs and `cost_config_hash`

9. **Run cost-based backtest**
   - `src/evaluation/backtest.py`
   - Join labels only when `label_time <= test_end`
   - Report censored counts per split and per regime
   - Compute realized cost, fraud dollars saved, precision@N, recall@N
   - Compute calibration: Brier and ECE
   - Compare against the canonical baselines
   - Run amount-scaled fraud loss sensitivity analysis

10. **Write Week 1 report**
    - `reports/week1_backtest.md` using the format in `evaluation_protocol.md` Section 13
    - Include all stopping decisions from `architecture.md` Section 9.5

### Canonical baselines compared

1. Random decision
2. Approve-all
3. Block-all
4. Rule-based threshold
5. LightGBM + static threshold
6. Cost-sensitive policy using the same LightGBM probabilities

### Week 1 Definition of Done

Task checklist in `architecture.md` Section 8, plus:

- Every stop criterion in `architecture.md` Section 9.2 evaluated and reported
- Every don't-stop condition in `architecture.md` Section 9.4 satisfied
- `reports/week1_backtest.md` written
- One command reproduces the entire pipeline

### Week 1 stop criterion

Apply `architecture.md` Section 9.3. The project stops here if:

- All Week 1 tasks are done
- Every phase has hit a Success / Null / Scope stop
- No measured failure remains that is not explicitly listed as future work
- Any further change would fall inside the noise band or below the effect size

If the stop condition is met, do not start Week 2. Report and stop.

---

## 5. Week 2 — Calibration and Cost-Sensitive Model

**Gate:** Only starts if Week 1 produced a measured failure that Week 2 can address.

Possible measured failures that justify Week 2:

- ECE >= 0.05 after one calibration attempt in Week 1
- Cost-sensitive training outperforms the plain LightGBM baseline in a pilot
- Calibration improves realized cost by >= 5% relative

If none of these hold, skip Week 2 and go to the final report.

### Candidate work

- Measure calibration more carefully: reliability diagram, per-regime ECE
- Compare Platt scaling against isotonic regression as a sensitivity analysis
- Train a cost-sensitive LightGBM variant using sample weights derived from the cost matrix
- Re-evaluate under the same split, delay regime, cost matrix, and budget

### Week 2 stop criterion

Define before work starts, in the same format as `architecture.md` Section 9.2. Report it in `reports/week2_calibration.md`.

If neither calibration nor cost-sensitive training improves realized cost per transaction beyond the noise band and effect size, stop and go to the final report.

### Out of scope for Week 2

- Online learning
- PU learning
- Delayed-label correction
- Drift detection
- Feature engineering beyond what is needed to fix a measured failure

---

## 6. Week 3 — Policy and Sensitivity

**Gate:** Only starts if Week 2 produced a measured change in policy behavior, or if Week 1 flagged amount-scaled cost as a material sensitivity.

### Candidate work

- Report the amount-scaled cost sensitivity results in more depth
- Vary `false_positive_cost`, `review_cost`, and `residual_fraud_loss` across a range
- Report whether the ranking of baselines changes under different cost matrices
- Optionally, run a capacity simulation as a **separate** experiment

### Week 3 stop criterion

Define before work starts. Report it in `reports/week3_policy.md`.

If the policy ranking of baselines does not change under any reasonable cost range, the Week 1 conclusion is robust. Stop and go to the final report.

### Out of scope for Week 3

- Learned policies (bandits, RL)
- Capacity-aware scheduling as the default policy
- Fairness-aware policy constraints

---

## 7. Week 4 — One Optional Improvement and Final Report

**Gate:** Only starts if Week 1–3 produced a measured failure that Week 4 can address.

### Candidate improvements (pick exactly one)

- Online learning (SGD, Passive-Aggressive) as an update mechanism
- PU learning with censored negatives
- Delayed-label correction model

### Rules for choosing one

- The chosen improvement must address a specific measured failure from Weeks 1–3
- It must come with its own stop criterion, defined before work starts
- It must be evaluated against the Week 1 baseline under the same split, delay regime, cost matrix, and budget
- If the improvement does not exceed the noise band and effect size, it is reported as a non-finding

### Final report contents

- Problem, pain point, and root cause
- ML formulation and decision policy
- Data, delay simulation, and splits
- Canonical baselines
- Primary metrics and sensitivity analyses
- Every stopping decision from Weeks 1–4
- Failure cases and limitations
- Reproduction instructions

### Demo

- Notebook or Markdown report
- No dashboards, no service layer

---

## 8. What Is Not on This Roadmap

Explicitly deferred and not scheduled:

- Dashboards (Streamlit, Grafana, Dash)
- Service layer (FastAPI, Uvicorn)
- Streaming infrastructure (Kafka, RabbitMQ, Faust)
- Docker / Kubernetes / CI/CD
- Model registry, feature store, hyperparameter search frameworks
- Deployment of any kind

These are not "future work" in this project. They are excluded unless a measured result makes them necessary and a stop criterion justifies the addition.

---

## 9. Gating Rule

For any addition not already in Week 1:

1. Name the measured failure it addresses.
2. Write its stop criterion before starting work.
3. Run it under the same split, delay regime, cost matrix, and budget as the Week 1 baseline.
4. Report the result, including non-findings.
5. If it does not exceed the noise band and effect size, do not adopt it.

If any of these steps is skipped, the addition is not part of the project.

---

## 10. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| BAF timestamp granularity blocks delay simulation | Verify first; fall back to month-based regimes |
| Censored labels bias the test set | Report censored counts; never treat as negative |
| Cost matrix is unrealistic | Run sensitivity analysis; report which conclusions depend on it |
| Scope creep into Week 2+ features | Gate each week on a measured Week 1–3 failure |
| Overfitting to one delay regime | Report per regime; never average across regimes |
| Stop criteria ignored | Report every stopping decision in `week1_backtest.md` |

---

## 11. Definition of Done for the Roadmap

- [ ] Week 1 tasks completed and reported
- [ ] Every stop criterion from `architecture.md` Section 9 evaluated
- [ ] Each Week 2+ addition gated by a measured failure
- [ ] Each Week 2+ addition has a written stop criterion
- [ ] Non-findings reported, not hidden
- [ ] Final report written
- [ ] Reproduction instructions verified

---

## 12. Guiding Rule

> Each week is justified by a measured result, not by the desire to build more.

> If a week cannot point to a number that made it necessary, it does not happen.
