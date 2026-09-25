# Delayed-Label Fraud Decisioning

A cost-sensitive fraud decision pipeline on the Bank Account Fraud (BAF)
dataset, evaluated under a delayed, censored, and biased label regime.

> **Course:** Introduction to Machine Learning - Final Group Project  
> **Institution:** National University Philippines  
> **Instructor:** Ken Oliver Caparros  
> **Lead Author:** Ken Ira Lacson Talingting  
> **Co-Authors:** [Group member names]

---

## Course Context

This project is submitted as the final group project for *Introduction to
Machine Learning*. It satisfies the course requirement to design, train,
evaluate, and deploy an end-to-end traditional machine learning solution
with exploratory data analysis, a fair comparison of exactly three
traditional algorithms, and a deployable Streamlit application.

The project is a **single decision pipeline**. The classifier is an input
to the policy. The policy is the product. The backtest is the evidence.
Course deliverables — three-algorithm comparison, EDA, Streamlit app,
IMRaD paper — are instruments for that pipeline, not separate layers.

---

## Problem

A transaction must be approved, reviewed, or blocked in **milliseconds**,
but the fraud label (chargeback, dispute, investigation outcome) may not
arrive for **weeks or months**. This creates a structural mismatch:

- The model must act **before** it can know whether it was correct.
- Observed labels are **delayed, censored, and biased** by prior decisions.
- Errors are **asymmetric**: a missed fraud and a false positive do not cost
  the same.
- Fraudsters **adapt**, so the data distribution drifts.

**Decision framing:** at decision time, choose the action that minimizes
expected operational cost, given a calibrated `P(fraud)` estimate and a
frozen cost matrix. Classification accuracy is a proxy; realized cost is
the objective.

---

## Headline Result

### Cost-Sensitive Policy (Primary)

Under a 1-month delayed-label regime with a chronological train /
validation / test split, the cost-sensitive policy reduces realized cost
per transaction by **60.02%** relative to the strongest baseline
(selected classifier + static 0.5), with a 95% bootstrap confidence
interval of **[56.00%, 64.16%]**.

| Baseline | Cost per transaction |
|---|---:|
| Random | 0.047484 |
| Approve-all | 0.018928 |
| Block-all | 0.098742 |
| Selected classifier + static 0.5 (strongest baseline) | 0.018737 |
| **Cost-sensitive policy (ours)** | **0.007491** |

Action distribution on the test window:

| Action | Count |
|---|---:|
| approve | 205,395 |
| review | 21,371 |
| block | 725 |

The result is robust to a 2× variation in each cost parameter
(`false_positive_cost`, `review_cost`, `residual_fraud_loss`); the minimum
advantage across all variations is **50.38%** (at `review_cost=0.04`).

Primary report: [`reports/decision_backtest.md`](reports/decision_backtest.md).
Supporting sensitivity and bootstrap:
[`reports/sensitivity.md`](reports/sensitivity.md),
[`reports/bootstrap.md`](reports/bootstrap.md).

### Classifier Comparison (Supporting)

Three traditional classifiers are compared as **policy inputs** under
identical folds, preprocessing, and cost criterion. Selection is by mean
realized cost after the policy, with a pre-registered noise-band guard
(top classifier must win every fold and the gap must exceed 5% relative).

| Classifier | CV realized cost (mean ± SD) |
|---|---:|
| LightGBM | 0.005852 ± 0.000300 |
| Logistic Regression | 0.005915 ± 0.000338 |
| Random Forest | 0.006515 ± 0.000579 |

Top gap: 0.000063 → **1.07% relative** (below the 5% threshold). Reported
as a **non-finding**; tie broken by simplicity. **Selected classifier:
LogisticRegression** (`C=10.0`, `max_iter=1000`).

Full CV and test results:
[`reports/model_comparison.md`](reports/model_comparison.md).

### Calibration Gate

Expected Calibration Error on the validation window: **ECE = 0.0033**
(gate: ECE < 0.05). Gate passed; no calibration step applied. The policy
uses raw classifier output directly.

---

## Approach

### Data and Split

- **Dataset:** Bank Account Fraud (BAF) `Base.csv` — 1,000,000 rows,
  32 raw features, ~1.1% fraud rate.
- **Delay regime:** `label_month = month + 1`; `observed = label_month <= 7`.
- **Single chronological split:**
  - Train: months 0–2 (397,039 rows)
  - Validation: months 3–4 (278,627 rows)
  - Test: months 5–6 (227,491 rows)
  - Censored: month 7 (96,843 rows, 9.68%, excluded and counted)
- **No shuffling. No random splits.** Preprocessing is fit on the training
  window only.

### Preprocessing

Algorithm-specific, fit within each training fold:

- Logistic Regression: one-hot + StandardScaler
- Random Forest: ordinal encoding, no scaling
- LightGBM: native categorical, no scaling

No class weighting is applied to any classifier: the decision policy
depends on `p` being a calibrated probability, and reweighting would
distort it. Cost asymmetry is handled by the policy, not the training
objective. See [`docs/data_card.md`](docs/data_card.md) §9.2.

### Decision Policy

The classifier output feeds an operational policy that minimizes expected
cost:

```text
E[cost(approve)] = p * fraud_loss(amount)
E[cost(review)]  = review_cost + p * residual_fraud_loss
E[cost(block)]   = (1 - p) * false_positive_cost

action = argmin over {approve, review, block}
```

The argmin rule is the source of truth. Derived thresholds are a
diagnostic view only. `fraud_loss` scales with transaction amount:

```text
fraud_loss(amount) = amount * fraud_loss_rate
fraud_loss_rate    = 1 / mean(amount_proxy on train)
                   = 0.0019187869
```

Calibration is required before the classifier is admissible: ECE < 0.05 on
the validation window. See [`docs/decision_policy.md`](docs/decision_policy.md).

### Evaluation Discipline

This project pre-registers its evaluation and forbids practices that
inflate results.

- **Temporal splits only.** No random splits, no shuffling.
- **Delay-aware.** A label may only be used after `label_time`.
- **Cost-based.** Every decision is scored by realized cost.
- **Baseline-anchored.** The policy is compared against the **strongest**
  baseline, not the weakest.
- **Pre-registered.** Metrics, thresholds, and the cost matrix are fixed
  before modeling.
- **Noise-aware.** A finding requires the 95% bootstrap CI on the
  advantage to exclude zero and the relative reduction to exceed 5%.
- **Honest.** Failures and non-findings are reported.

Forbidden: random splits on temporal data, test-window tuning of any kind,
treating censored labels as negatives, reporting macro F1 or ROC-AUC as
the primary success criterion, counting hyperparameter variants as
distinct algorithms.

See [`docs/evaluation_protocol.md`](docs/evaluation_protocol.md) for the
full protocol.

---

## Deployable Application

A Streamlit application loads the saved classifier and the same
preprocessing pipeline used during training. It is a **decision system**,
not a classifier demo.

**Input:** validated form fields (or CSV upload) for transaction features.  
**Output:** `p_fraud` and the routed action (`approve` / `review` /
`block`), with the expected-cost reasoning visible.  
**Error handling:** missing, invalid, and out-of-range inputs are rejected
with clear error messages; the app does not crash.

- **Deployed URL:** https://delayed-label-fraud-decisioning-gefp9s9mbkfdyzhhvescdm.streamlit.app
- **Local setup:** see [`documentation/technical_documentation.md`](documentation/technical_documentation.md)
- **App guide:** see [`documentation/app_guide.md`](documentation/app_guide.md)

---

## Reproduce

### Full pipeline

```bash
python -m src.pipeline
```

Runs eight steps: `load → simulate_delay → split → train_compare →
evaluate_compare → score → decide → backtest`.

### Pipeline plus standalone analyses

```bash
python -m src.pipeline --analyses
```

Runs the pipeline, then `calibration`, `sensitivity`, and `bootstrap`.

### List the steps without running

```bash
python -m src.pipeline --list
```

### Standalone analyses

```bash
python -m src.evaluation.calibration    # prints ECE and reliability table
python -m src.evaluation.sensitivity    # writes reports/sensitivity.md
python -m src.evaluation.bootstrap      # writes reports/bootstrap.md
```

### Tests

```bash
pytest -q
# 58 passed
```

### Environment

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1      # Windows
# source .venv/bin/activate       # macOS / Linux

python -m pip install --upgrade pip
pip install -r requirements.txt
```

**Python 3.11 is required.** Do not use 3.14; several pinned dependencies
lack prebuilt wheels for it.

Verified library versions: Python 3.11, numpy 2.2.6, pandas 2.3.3,
pyarrow 19.0.1, scikit-learn 1.7.2, LightGBM 4.7.0, Streamlit 1.64.0,
joblib 1.6.0, PyYAML 6.0.3, matplotlib 3.8+, pytest 8.1+.

The pipeline reproduces byte-for-byte. Given `data/original/Base.csv`
plus `configs/costs.yaml` and the fixed seed (`42`), every number in the
reports regenerates.

---

## Documentation

### Course deliverables

| Document | Purpose |
|---|---|
| [`documentation/data_dictionary.md`](documentation/data_dictionary.md) | Every feature: name, type, unit, description, allowed values |
| [`documentation/technical_documentation.md`](documentation/technical_documentation.md) | Install, run, input format, limitations, troubleshooting |
| [`documentation/app_guide.md`](documentation/app_guide.md) | Streamlit usage, examples, expected outputs |
| [`documentation/contribution_record.md`](documentation/contribution_record.md) | Member names, tasks, actual contributions |
| [`documentation/ownership_declaration.md`](documentation/ownership_declaration.md) | Signed ownership and authorship declaration |
| [`paper/paper_imrad.md`](paper/paper_imrad.md) | IMRaD draft (DOCX + PDF versions in `paper/`) |

### Foundation (source of truth)

| Document | Purpose |
|---|---|
| [`docs/problem_framing.md`](docs/problem_framing.md) | First-principles problem decomposition, scope, success criteria |
| [`docs/first_principles_decomposition.md`](docs/first_principles_decomposition.md) | Derivation behind the framing; assumptions audit; traceability |
| [`docs/data_card.md`](docs/data_card.md) | Dataset, schema, delay simulation, splits, leakage and bias registers |
| [`docs/decision_policy.md`](docs/decision_policy.md) | Actions, expected cost, threshold derivation, action log schema |
| [`docs/evaluation_protocol.md`](docs/evaluation_protocol.md) | Cost matrix, temporal backtest, baselines, forbidden metrics, stop criteria |

### Build, plan, and history

| Document | Purpose |
|---|---|
| [`docs/mvp_architecture.md`](docs/mvp_architecture.md) | The as-built single decision pipeline |
| [`docs/roadmap.md`](docs/roadmap.md) | Gated execution plan |
| [`docs/README.md`](docs/README.md) | Documentation index with reading orders |
| [`docs/daily_log/`](docs/daily_log/) | Session-by-session build record |
| [`TODO.md`](TODO.md) | Open work items for the current phase |

### Superseded (kept for context)

| Document | Reason |
|---|---|
| [`docs/architecture.md`](docs/architecture.md) | Week 1 MVP specification; superseded by `mvp_architecture.md` and the v1.0 foundation documents |
| [`docs/mvp_2_weeks.md`](docs/mvp_2_weeks.md) | Original 2-week plan; superseded by `mvp_architecture.md` |

### Reports

| Report | Contents |
|---|---|
| [`reports/decision_backtest.md`](reports/decision_backtest.md) | Primary: policy vs. baseline comparison, data integrity, failure analysis, stop verdict |
| [`reports/model_comparison.md`](reports/model_comparison.md) | Supporting: classifier comparison as policy inputs, selection justification |
| [`reports/sensitivity.md`](reports/sensitivity.md) | Full cost sensitivity table across the 2× sweep |
| [`reports/bootstrap.md`](reports/bootstrap.md) | 95% confidence intervals on cost per transaction |

### Paper materials

| Document | Purpose |
|---|---|
| [`docs/paper/paper_blueprint.md`](docs/paper/paper_blueprint.md) | IEEE section map |
| [`docs/paper/abstract_and_index_terms.md`](docs/paper/abstract_and_index_terms.md) | Abstract and index terms |
| [`docs/paper/introduction_draft.md`](docs/paper/introduction_draft.md) | Section 1 skeleton |
| [`docs/paper/reference_sheet.md`](docs/paper/reference_sheet.md) | Every number and claim, one page |

---

## Repository Layout

```text
delayed-label-fraud-decisioning/
├── README.md
├── TODO.md
├── requirements.txt
├── conftest.py
├── app/
│   └── streamlit_app.py
├── configs/
│   └── costs.yaml
├── data/
│   ├── original/Base.csv
│   ├── interim/
│   └── processed/
├── notebooks/
│   ├── 01_eda.ipynb
│   ├── 02_preprocessing.ipynb
│   ├── 03_model_training.ipynb
│   └── 04_evaluation.ipynb
├── models/
│   ├── best_model.pkl
│   ├── preprocessing.pkl
│   ├── feature_columns.json
│   ├── feature_defaults.json
│   └── feature_importances.json
├── docs/
│   ├── problem_framing.md
│   ├── first_principles_decomposition.md
│   ├── data_card.md
│   ├── decision_policy.md
│   ├── evaluation_protocol.md
│   ├── mvp_architecture.md
│   ├── roadmap.md
│   ├── README.md
│   ├── daily_log/
│   └── paper/
├── documentation/
│   ├── data_dictionary.md
│   ├── technical_documentation.md
│   ├── app_guide.md
│   ├── contribution_record.md
│   └── ownership_declaration.md
├── paper/
│   ├── paper_imrad.md
│   ├── paper.docx
│   └── paper.pdf
├── reports/
│   ├── decision_backtest.md
│   ├── model_comparison.md
│   ├── sensitivity.md
│   ├── bootstrap.md
│   └── cv_results.json
├── src/
│   ├── common.py
│   ├── pipeline.py
│   ├── data/
│   │   ├── load.py
│   │   ├── simulate_delay.py
│   │   └── split.py
│   ├── models/
│   │   ├── preprocess.py
│   │   ├── train_compare.py
│   │   ├── evaluate_compare.py
│   │   └── score.py
│   ├── policy/
│   │   └── decide.py
│   └── evaluation/
│       ├── backtest.py
│       ├── calibration.py
│       ├── sensitivity.py
│       └── bootstrap.py
└── tests/
    ├── test_app_validation.py
    ├── test_backtest.py
    ├── test_data_schema.py
    ├── test_model.py
    ├── test_pipeline_integration.py
    ├── test_policy.py
    ├── test_preprocessing.py
    └── test_reproducibility.py
```

---

## Required Deliverables (Course)

| # | Deliverable | Status |
|---|---|---|
| 1 | Deployable application (Streamlit URL + local) | Done |
| 2 | Source code (repo link + ZIP) | Done |
| 3 | Technical documentation | Done |
| 4 | Dataset package (original, processed, data dictionary, source, license) | In progress |
| 5 | IMRaD style paper (DOCX + PDF) | Paper team |
| 6 | Contribution record | Missing |
| 7 | Ownership and authorship declaration (signed PDF) | Missing |

---

## Non-Goals

Deliberately excluded. Each is only added if a measured failure justifies
it and the addition has its own stop criterion.

- Neural networks, deep learning, CNNs, RNNs, transformers, LLMs
- Pretrained foundation models
- AutoML-generated solutions
- Streaming infrastructure (Kafka, RabbitMQ, Faust)
- Service layer (FastAPI, Uvicorn)
- Online learning (SGD, Passive-Aggressive)
- PU learning
- Delayed-label correction models
- Drift detectors
- Graph neural networks
- Federated learning
- Docker / Kubernetes
- MLflow / W&B / DVC
- Model registry, feature store, hyperparameter search frameworks

---

## Citation

```bibtex
@misc{delayed_label_fraud_2026,
  title  = {Delayed-Label Fraud Decisioning: A Cost-Sensitive Policy on
            the Bank Account Fraud Dataset under Delayed and Censored
            Labels},
  author = {Talingting, Ken Ira Lacson and [Co-author names]},
  year   = {2026},
  note   = {Introduction to Machine Learning final project,
            National University Philippines}
}
```

---

## Authors

**Lead Author:** Ken Ira Lacson Talingting  
**Co-Authors:** [Group member names]

Introduction to Machine Learning final project,
National University Philippines.

**Instructor:** Ken Oliver Caparros

## License

TBD — will be added before public release.
