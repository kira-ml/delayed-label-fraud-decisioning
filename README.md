# Delayed-Label Fraud Decisioning

A three-algorithm classification study on fraud detection with a supplementary
cost-sensitive decision policy evaluated under delayed, censored, and biased
labels.

> **Course:** Introduction to Machine Learning — Final Group Project
> **Institution:** National University Philippines
> **Instructor:** Ken Oliver Caparros
> **Authors:** [Group member names]

---

## Course Context

This project is submitted as the final group project for *Introduction to
Machine Learning*. It satisfies the course requirement to design, train,
evaluate, and deploy an end-to-end traditional machine learning solution
based on a clear classification problem, with exploratory data analysis,
a fair comparison of exactly three traditional algorithms, and a deployable
Streamlit application.

The project has two layers:

1. **Primary (course requirement):** A binary classification study that
   compares three traditional algorithms on the Bank Account Fraud (BAF)
   dataset, supported by exploratory data analysis and a Streamlit
   application.
2. **Supplementary (project depth):** A cost-sensitive decision policy
   evaluated under a delayed-label regime, which reframes the classification
   output as an operational `approve` / `review` / `block` decision.

Both layers share the same dataset, the same chronological split, and the
same evaluation discipline.

---

## Problem

A transaction must be approved, reviewed, or blocked in **milliseconds**, but
the fraud label (chargeback, dispute, investigation outcome) may not arrive
for **weeks or months**. This creates a structural mismatch:

- The model must act **before** it can know whether it was correct.
- Observed labels are **delayed, censored, and biased** by prior decisions.
- Errors are **asymmetric**: a missed fraud and a false positive do not cost
  the same.
- Fraudsters **adapt**, so the data distribution drifts.

**Classification framing (primary):** Predict `fraud_bool` from
transaction-time features. The intended user is a fraud operations team that
needs a ranked list of high-risk transactions.

**Decision framing (supplementary):** Map the predicted probability to an
operational action under an explicit cost structure.

---

## Headline Result

### Primary — Three-Algorithm Comparison

Three traditional algorithms are compared under identical data, preprocessing,
and cross-validation conditions on the training split.

| Algorithm | Primary Metric (Macro F1) | Precision (Fraud) | Recall (Fraud) | ROC-AUC |
|---|---:|---:|---:|---:|
| Logistic Regression | TBD | TBD | TBD | TBD |
| Random Forest | TBD | TBD | TBD | TBD |
| LightGBM | TBD | TBD | TBD | TBD |

*Numbers pending final model training. The selected model is justified in the
IMRaD paper using validation performance, interpretability, speed, and
practical suitability.*

### Supplementary — Cost-Sensitive Policy

Under a 1-month delayed-label regime with a chronological train / validation
/ test split, the cost-sensitive policy reduces realized cost per transaction
by **56.87%** relative to the strongest baseline, with a 95% bootstrap
confidence interval of **[52.77%, 60.91%]**.

| Baseline | Cost per transaction |
|---|---:|
| Random | 0.046931 |
| Approve-all | 0.018928 |
| Block-all | 0.098742 |
| LightGBM + static 0.5 | 0.017543 |
| **Cost-sensitive policy (ours)** | **0.007566** |

The result is robust to a 2× variation in each cost parameter
(`false_positive_cost`, `review_cost`, `residual_fraud_loss`); the minimum
advantage across all variations is **46.46%**.

This supplementary analysis is documented in
[`reports/mvp_backtest.md`](reports/mvp_backtest.md),
[`reports/sensitivity.md`](reports/sensitivity.md), and
[`reports/bootstrap.md`](reports/bootstrap.md).

---

## Approach

### Primary — Three-Algorithm Classification

- **Dataset:** Bank Account Fraud (BAF) `Base.csv` — 1,000,000 rows, 32 raw
  features, ~1.1% fraud rate.
- **Target:** `fraud_bool` (binary).
- **Split:** chronological 80/20 train/test, with 5-fold time-series
  cross-validation on the training data for model selection and tuning.
- **Preprocessing:** fit on training data only; applied unchanged to test.
  Missing-value handling, categorical encoding, and scaling are documented
  in [`docs/data_card.md`](docs/data_card.md) §9.
- **Primary metric:** Macro F1, chosen because the class distribution is
  heavily imbalanced and both false positives and false negatives carry
  operational cost. Supporting metrics: per-class precision, recall, F1,
  confusion matrix, and ROC-AUC.
- **Algorithms compared:** Logistic Regression, Random Forest, LightGBM.
  Each is a permitted traditional algorithm; each is tuned with a small
  documented grid; each uses identical folds and preprocessing.
- **Selected model:** justified in the IMRaD paper on performance,
  interpretability, speed, and practical suitability.

### Supplementary — Decision Policy

The classification output feeds an operational policy that minimizes
expected cost:

```text
E[cost(approve)] = p * fraud_loss(amount)
E[cost(review)]  = review_cost + p * residual_fraud_loss
E[cost(block)]   = (1 - p) * false_positive_cost

action = argmin over {approve, review, block}
```

The argmin rule is the source of truth. Derived thresholds are a diagnostic
view only. `fraud_loss` scales with transaction amount under the adopted
amount-scaled cost model.

---

## Deployable Application

A Streamlit application loads the saved best model and the same preprocessing
pipeline used during training.

**Input:** validated form fields (or CSV upload) for transaction features.
**Output:** predicted class, predicted probability, and — where the selected
algorithm supports it — a confidence indicator.
**Error handling:** missing, invalid, and out-of-range inputs are rejected
with clear error messages; the app does not crash.

- **Deployed URL:** [TBD — to be added after deployment]
- **Local setup:** see [`documentation/technical_documentation.md`](documentation/technical_documentation.md)
- **App guide:** see [`documentation/app_guide.md`](documentation/app_guide.md)

---

## Reproduce

### Full pipeline

```bash
python -m src.pipeline
```

Runs, in order: load → simulate delay → split → train → score → decide →
backtest.

### Supplementary analyses

```bash
python -m src.evaluation.sensitivity   # writes reports/sensitivity.md
python -m src.evaluation.bootstrap     # writes reports/bootstrap.md
```

### Tests

```bash
pytest
# 13 passed in ~1.4s
```

The pipeline reproduces byte-for-byte. Given `data/raw/baf/Base.csv` plus
`configs/costs.yaml` and the fixed seeds, every number in the report
regenerates.

### Environment

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1      # Windows
# source .venv/bin/activate       # macOS / Linux

python -m pip install --upgrade pip
pip install -r requirements.txt
```

Pinned library versions: Python 3.10, LightGBM 4.7.0, pandas 2.3.3,
numpy 2.2.6, pyarrow 19.0.1, scikit-learn 1.7.2, PyYAML 6.0.3, Streamlit
[TBD], matplotlib, seaborn, pytest.

---

## Documentation

### Primary documents (course submission)

| Document | Purpose |
|---|---|
| [`documentation/data_dictionary.md`](documentation/data_dictionary.md) | Every feature: name, type, unit, description, allowed values |
| [`documentation/technical_documentation.md`](documentation/technical_documentation.md) | Install, run, input format, app guide, limitations, troubleshooting |
| [`documentation/app_guide.md`](documentation/app_guide.md) | Streamlit usage and expected units |
| [`documentation/contribution_record.md`](documentation/contribution_record.md) | Member names, tasks, actual contributions |
| [`documentation/ownership_declaration.md`](documentation/ownership_declaration.md) | Signed ownership and authorship declaration |
| [`paper/paper_imrad.md`](paper/paper_imrad.md) | IMRaD draft (DOCX + PDF versions in `paper/`) |

### Supplementary documents (project depth)

| Document | Purpose |
|---|---|
| [`docs/problem_framing.md`](docs/problem_framing.md) | First-principles problem decomposition, scope, success criteria |
| [`docs/data_card.md`](docs/data_card.md) | Dataset, schema, label-delay simulation, leakage and bias registers |
| [`docs/evaluation_protocol.md`](docs/evaluation_protocol.md) | Cost matrix, temporal backtest, canonical baselines, forbidden metrics |
| [`docs/decision_policy.md`](docs/decision_policy.md) | Actions, expected cost, threshold derivation, action log schema |
| [`docs/mvp_architecture.md`](docs/mvp_architecture.md) | The as-built pipeline |
| [`docs/architecture.md`](docs/architecture.md) | Full architecture spec with data-driven stop criteria |
| [`docs/roadmap.md`](docs/roadmap.md) | Weekly plan, gated on measured failure |

### Reports

| Report | Contents |
|---|---|
| [`reports/model_comparison.md`](reports/model_comparison.md) | Primary: 3-algorithm comparison, CV results, final test results |
| [`reports/mvp_backtest.md`](reports/mvp_backtest.md) | Supplementary: cost-sensitive policy backtest |
| [`reports/sensitivity.md`](reports/sensitivity.md) | Supplementary: full cost sensitivity table |
| [`reports/bootstrap.md`](reports/bootstrap.md) | Supplementary: 95% confidence intervals on cost per transaction |

### Paper materials

| Document | Purpose |
|---|---|
| [`docs/paper/paper_blueprint.md`](docs/paper/paper_blueprint.md) | IEEE section map |
| [`docs/paper/abstract_and_index_terms.md`](docs/paper/abstract_and_index_terms.md) | Abstract and index terms |
| [`docs/paper/introduction_draft.md`](docs/paper/introduction_draft.md) | Section 1 skeleton |
| [`docs/paper/reference_sheet.md`](docs/paper/reference_sheet.md) | Every number and claim, one page |

Session-by-session build record: [`docs/daily_log/`](docs/daily_log/).

---

## Evaluation Discipline

This project pre-registers its evaluation and forbids practices that inflate
results.

- **Temporal splits only.** No random splits, no shuffling.
- **Delay-aware.** A label may only be used after `label_time`.
- **Cost-based (supplementary).** Every decision is scored by realized cost.
- **Baseline-anchored.** Every improvement must beat a named baseline.
- **Pre-registered.** Metrics and thresholds fixed before modeling.
- **Honest.** Failures and non-findings are reported, not hidden.
- **Stopping rules.** Each phase has a data-driven stop criterion.

Forbidden metrics: raw accuracy, AUC-only claims, F1 without context.
AUC is reported informationally but never used as the sole success criterion.

See [`docs/evaluation_protocol.md`](docs/evaluation_protocol.md) for the full
protocol.

---

## Repository Layout

```text
delayed-label-fraud-decisioning/
├── README.md
├── requirements.txt
├── conftest.py
├── app/
│   └── streamlit_app.py
├── configs/
│   └── costs.yaml
├── data/
│   ├── original/Base.csv
│   └── processed/
├── notebooks/
│   ├── 01_eda.ipynb
│   ├── 02_preprocessing.ipynb
│   ├── 03_model_training.ipynb
│   └── 04_evaluation.ipynb
├── models/
│   └── best_model.pkl
├── docs/
│   ├── problem_framing.md
│   ├── data_card.md
│   ├── decision_policy.md
│   ├── evaluation_protocol.md
│   ├── architecture.md
│   ├── mvp_architecture.md
│   ├── roadmap.md
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
│   ├── model_comparison.md
│   ├── mvp_backtest.md
│   ├── sensitivity.md
│   └── bootstrap.md
├── src/
│   ├── common.py
│   ├── pipeline.py
│   ├── data/{load, simulate_delay, split}.py
│   ├── models/{train_baseline, score, train_compare}.py
│   ├── policy/decide.py
│   └── evaluation/{backtest, calibration, sensitivity, bootstrap}.py
└── tests/
    ├── test_policy.py
    └── test_backtest.py
```

---

## Required Deliverables (Course)

| # | Deliverable | Status |
|---|---|---|
| 1 | Deployable application (Streamlit URL + local) | In progress |
| 2 | Source code (repo link + ZIP) | Available |
| 3 | Technical documentation (README + PDF/DOCX) | In progress |
| 4 | Dataset package (original, processed, data dictionary, source, license) | In progress |
| 5 | IMRaD style paper (DOCX + PDF) | In progress |
| 6 | Contribution record | In progress |
| 7 | Ownership and authorship declaration (signed PDF) | In progress |

---

## Non-Goals

Deliberately excluded. Each is only added if a measured failure justifies it
and the addition has its own stop criterion.

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
  title  = {Delayed-Label Fraud Decisioning: A Three-Algorithm Classification
            Study with a Cost-Sensitive Policy under Delayed and Censored
            Labels},
  author = {[Author names]},
  year   = {2026},
  note   = {Introduction to Machine Learning final project,
            National University Philippines}
}
```

---

## Authors

[Group member names] — Introduction to Machine Learning final project,
National University Philippines.

**Instructor:** Ken Oliver Caparros

## License

TBD — will be added before public release.
