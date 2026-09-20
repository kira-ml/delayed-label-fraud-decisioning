# Delayed-Label Fraud Decisioning

A first-principles machine learning system for **cost-sensitive fraud decisioning under delayed, censored, and biased labels**.

> Most fraud detection projects optimize offline classification metrics on data where the label is already known.  
> This project addresses the operational problem: **decide now, when the truth may not arrive for weeks or months.**

---

## Problem

In modern payment systems, a transaction must be approved, reviewed, or blocked in **milliseconds to seconds**, but the fraud label (chargeback, dispute, investigation outcome) may not arrive for **weeks or months**.

This creates a structural mismatch:

- The model must act **before** it can know whether it was correct.
- Observed labels are **delayed, censored, and biased** by prior decisions.
- Errors are **asymmetric**: a missed fraud and a false positive do not cost the same.
- Fraudsters **adapt**, so the data distribution drifts.

Standard tutorials frame this as binary classification:  
`dataset → model → AUC`.

This project frames it as a **one-step decision problem under delayed feedback**:

```text
observe → decide → act → observe delayed/partial outcome → evaluate
```

Full online adaptation and delayed-label correction are future work, not Week 1 requirements.

---

## Core Question

> How can a fraud decision policy be trained and evaluated when fraud labels arrive late, are censored at evaluation time, and have asymmetric operational costs?

---

## Approach

The system optimizes **operational utility**, not classification accuracy:

```text
utility = fraud loss avoided
        − false-positive cost
        − review cost
```

### Decision Policy

For each transaction, given predicted fraud probability `p`:

```text
E[cost(approve)] = p * fraud_loss
E[cost(review)]  = review_cost + p * residual_fraud_loss
E[cost(block)]   = (1 - p) * false_positive_cost

action = argmin over {approve, review, block}
```

The policy is evaluated by **realized cost under a chronological backtest**, not by AUC.

The argmin rule is the source of truth. Derived thresholds are a diagnostic view only.

---

## Week 1 System Architecture

Week 1 is a batch pipeline, not a production system.

```mermaid
flowchart LR
    A[Raw Dataset] --> B[Load and Normalize]
    B --> C[Delay Simulator]
    C --> D[Temporal Splitter]
    D --> E[Baseline Trainer]
    E --> F[Scorer]
    F --> G[Decision Policy]
    G --> H[Action Log]
    H --> I[Cost-Based Backtest]
    I --> J[Week 1 Report]
```

See [docs/architecture.md](docs/architecture.md) for the full Week 1 MVP architecture.

---

## Status

**Week 1 — baseline end-to-end pipeline in progress.**

Documentation:

- [x] Problem framing
- [x] Architecture
- [x] Evaluation protocol
- [x] Data card
- [x] Decision policy

Implementation:

- [ ] BAF timestamp granularity verified
- [ ] Data loader
- [ ] Delay simulator (fixed 7 / 30 / 90 day regimes)
- [ ] Temporal splitter (chronological, label-matured)
- [ ] Baseline LightGBM trained
- [ ] Scorer
- [ ] Decision policy with fixed cost matrix
- [ ] Action log with all three expected costs and `cost_config_hash`
- [ ] Cost-based backtest with canonical baselines
- [ ] Calibration report: Brier and ECE
- [ ] Amount-scaled fraud loss sensitivity analysis
- [ ] `reports/week1_backtest.md`

---

## Documentation

| Document | Purpose |
|---|---|
| [Problem Framing](docs/problem_framing.md) | First-principles problem decomposition, scope, success criteria |
| [Architecture](docs/architecture.md) | Week 1 MVP pipeline, component contracts, and **data-driven stop criteria** (Section 9) |
| [Evaluation Protocol](docs/evaluation_protocol.md) | Cost matrix, temporal backtest, canonical baselines, metrics |
| [Data Card](docs/data_card.md) | Dataset, schema, label-delay simulation, leakage and bias registers |
| [Decision Policy](docs/decision_policy.md) | Actions, expected cost, threshold derivation, action log schema |
| [Roadmap](docs/roadmap.md) | Weekly milestones and non-goals |

---

## Setup

### Requirements

- Python 3.11 (3.10 also supported)
- PowerShell, Bash, or any shell

### Install

```bash
python -m venv .venv
# Windows
.\.venv\Scripts\Activate.ps1
# macOS / Linux
source .venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements.txt
```

Locked versions are in `requirements.lock.txt` for reproducibility.

---

## Run (Week 1)

```bash
python -m src.pipeline --config configs/week1.yaml
```

Or, if using `make`:

```bash
make week1
```

Outputs:

- `data/processed/decisions.parquet`
- `data/processed/action_log.parquet`
- `reports/week1_backtest.md`

---

## Data

Primary dataset: **Bank Account Fraud (BAF) Suite**  
Secondary: **IEEE-CIS Fraud Detection** — optional, out of Week 1 unless BAF proves insufficient.

Raw and processed data are **not committed** to this repository.  
See [docs/data_card.md](docs/data_card.md) for schema, splits, delay simulation, and known biases.

Label delay is **simulated**, using a fixed Δ per regime:

| Regime | Δ |
|---|---|
| Short | 7 days |
| Medium | 30 days |
| Long | 90 days |

If BAF does not support day-level timestamps, regimes fall back to 1 / 2 / 3 months and the data card is updated.

Censored labels are excluded from training and evaluation, and **counted** per split and per regime.

---

## Evaluation

All results are reported under:

- **Chronological splits only** — no random splits, ever
- **Fixed delay regimes** — 7 / 30 / 90 days, reported separately
- **Fixed cost matrix** — documented in `configs/costs.yaml`
- **Fixed review budget** — top 1% / 5% / 10%

Canonical Week 1 baselines:

1. Random decision
2. Approve-all
3. Block-all
4. Rule-based threshold
5. LightGBM + static threshold
6. Cost-sensitive policy using the same LightGBM probabilities

Primary metrics:

- Cost per transaction
- Total cost
- Fraud dollars saved at fixed FPR
- Fraud dollars saved at fixed review budget
- Precision@N, Recall@N
- Calibration: Brier score and ECE
- Censored-label counts per split and per regime

Required sensitivity analysis:

- Constant `fraud_loss` vs amount-scaled `fraud_loss(amount) = amount * fraud_loss_rate`
- `false_positive_cost`, `review_cost`, `residual_fraud_loss`

AUC is reported but never used as the sole success criterion.

**Primary success criterion:** realized cost per transaction under the cost-sensitive policy is lower than every canonical baseline, under the same split, delay regime, cost matrix, and budget.

See [docs/evaluation_protocol.md](docs/evaluation_protocol.md) for the full protocol.

---

## When to Stop

Iteration is not open-ended. The project has **data-driven stop criteria** for each phase of the Week 1 loop.

See [docs/architecture.md](docs/architecture.md) **Section 9** for:

- Global rules: noise band, minimum effect size, no test-set tuning, report non-findings
- Phase-specific stop criteria: baseline model, calibration, amount-scaled sensitivity, feature engineering, policy tuning, capacity simulation
- Overall project stop condition
- Don't-stop conditions that block premature declarations of "done"

Every stopping decision is reported in `reports/week1_backtest.md`.

---

## Repository Layout

```text
delayed-label-fraud-decisioning/
├── README.md
├── requirements.txt
├── requirements.lock.txt
├── .gitignore
├── configs/
│   ├── costs.yaml
│   ├── delay.yaml
│   ├── policy.yaml
│   └── splits.yaml
├── data/
│   ├── raw/                 # gitignored
│   ├── interim/             # gitignored
│   └── processed/           # gitignored
├── docs/
│   ├── problem_framing.md
│   ├── architecture.md
│   ├── evaluation_protocol.md
│   ├── data_card.md
│   ├── decision_policy.md
│   └── roadmap.md
├── notebooks/
│   └── week1_exploration.ipynb
├── reports/
│   └── week1_backtest.md
├── src/
│   ├── data/
│   ├── models/
│   ├── policy/
│   └── evaluation/
└── tests/
```

---

## Non-Goals (Week 1)

Explicitly out of scope to prevent over-engineering:

- Streaming infrastructure (Kafka, RabbitMQ, Faust)
- Service layer (FastAPI, Uvicorn)
- Dashboards (Streamlit, Dash, Grafana)
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

These are only added after the Week 1 baseline is measured, and only if a specific measured failure justifies them and the addition has its own stop criterion.

---

## Roadmap

- **Week 1:** baseline end-to-end pipeline + cost-based backtest
- **Week 2:** calibration + cost-sensitive LightGBM (only if Week 1 stop criteria justify)
- **Week 3:** amount-scaled cost sensitivity + optional capacity simulation as a separate experiment
- **Week 4:** one improvement (online learning / PU learning / delayed-label correction), final report, demo

Each Week 2+ addition is gated by:

1. A measured failure of the Week 1 baseline, and
2. Its own stop criterion defined before work starts.

See [docs/roadmap.md](docs/roadmap.md) for details, and [docs/architecture.md](docs/architecture.md) Section 9 for stopping rules.

---

## Why This Project

Most fraud detection projects stop at “train XGBoost, report AUC.”  
This project treats fraud detection as what it actually is: a **decision system under delayed, censored, and biased feedback**.

The goal is not a novel algorithm.  
The goal is a **correct, honest, reproducible loop** with **explicit stopping rules**, so later improvements rest on measured results rather than ambition.

---

## License

TBD — will be added before public release.

## Author

Kira — Introduction to Machine Learning final project
