# Technical Documentation

> **Repository:** `delayed-label-fraud-decisioning`  
> **Course:** Introduction to Machine Learning - Final Group Project  
> **Institution:** National University Philippines  
> **Instructor:** Ken Oliver Caparros  
> **Document:** Technical Documentation  
> **Status:** v1.1 — unified decision pipeline  
> **Last updated:** 2026-09-25

---

## 1. Purpose

This document explains how to install, run, and reproduce the project. It
covers:

- System requirements
- Installation steps
- Repository structure
- How to run the pipeline
- How to run the tests
- How to run the app
- Where artifacts land
- Exact reproduction recipe
- Environment notes
- Troubleshooting

It complements:

- [`documentation/app_guide.md`](app_guide.md) — how to use the app
- [`documentation/data_dictionary.md`](data_dictionary.md) — feature reference
- [`docs/mvp_architecture.md`](../docs/mvp_architecture.md) — as-built system design

---

## 2. System Requirements

| Component | Requirement |
|---|---|
| Operating system | Windows 10/11, macOS 12+, or Ubuntu 20.04+ |
| Python | 3.11 (required by Streamlit Cloud; also works locally) |
| Disk space | ~2 GB (raw dataset is ~130 MB, models and artifacts are < 5 MB) |
| RAM | 4 GB minimum, 8 GB recommended for the full pipeline |
| GPU | Not required |

**Do not use Python 3.14.** Several pinned dependencies (`pyarrow`,
`scikit-learn`, `lightgbm`) lack prebuilt wheels for 3.14 and would attempt
to build from source. That fails on machines without CMake and on the
Streamlit Cloud build container.

---

## 3. Installation

### 3.1 Clone the Repository

```bash
git clone https://github.com/kira-ml/delayed-label-fraud-decisioning.git
cd delayed-label-fraud-decisioning
```

### 3.2 Create a Virtual Environment

Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3.3 Install Dependencies

```bash
pip install -r requirements.txt
```

### 3.4 Download the Dataset

The raw BAF dataset is not committed to the repository. Download it from
Kaggle:

```
https://www.kaggle.com/datasets/sgpjesus/bank-account-fraud-dataset-neurips-2022
```

Place `Base.csv` at:

```
data/original/Base.csv
```

The `load.py` script also searches the legacy path
`data/raw/baf/Base.csv` if the primary path is missing.

**License:** CC BY 4.0. Academic and non-commercial use permitted with
attribution. See [`docs/data_card.md`](../docs/data_card.md) section 2.

---

## 4. Repository Structure

```
delayed-label-fraud-decisioning/
├── README.md
├── TODO.md                         # open work items
├── requirements.txt
├── conftest.py                     # pytest path bootstrap
├── app/
│   └── streamlit_app.py            # deployed decision system
├── configs/
│   └── costs.yaml                  # frozen cost matrix
├── data/                           # gitignored
│   ├── original/
│   │   └── Base.csv
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
├── docs/                           # design and methodology
│   ├── problem_framing.md
│   ├── first_principles_decomposition.md
│   ├── data_card.md
│   ├── decision_policy.md
│   ├── evaluation_protocol.md
│   ├── mvp_architecture.md
│   ├── roadmap.md
│   └── daily_log/
├── documentation/                  # course-required deliverables
│   ├── data_dictionary.md
│   ├── app_guide.md
│   ├── technical_documentation.md
│   ├── contribution_record.md
│   └── ownership_declaration.md
├── paper/
│   ├── paper_imrad.md
│   ├── paper.docx
│   └── paper.pdf
├── reports/
│   ├── decision_backtest.md        # primary deliverable
│   ├── model_comparison.md         # supporting classifier comparison
│   ├── cv_results.json
│   ├── sensitivity.md
│   └── bootstrap.md
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

## 5. Running the Pipeline

There is **one** pipeline. It is a decision pipeline: the classifier is an
input to the policy, and the policy is the product.

```bash
python -m src.pipeline
```

Runs eight steps in order:

1. `load` — read `data/original/Base.csv`, add `transaction_id` and
   `amount_proxy`, write `data/interim/transactions.parquet`
2. `simulate_delay` — assign `label_month = month + 1`; mark `observed`;
   write `data/interim/labeled.parquet`
3. `split` — chronological split: train months 0-2, val 3-4, test 5-6;
   censor month 7
4. `train_compare` — expanding-window CV by month for Logistic
   Regression, Random Forest, and LightGBM; write
   `reports/model_comparison.md` and `reports/cv_results.json`
5. `evaluate_compare` — select the classifier by validation realized cost
   with the noise-band guard; retrain on the full training window;
   evaluate **once** on the test window; save `models/best_model.pkl`,
   `models/preprocessing.pkl`, and feature metadata
6. `score` — score the test window; write
   `data/processed/scored_test.parquet`
7. `decide` — apply the argmin expected-cost policy; write
   `data/processed/action_log.parquet`
8. `backtest` — realized cost vs. canonical baselines; write
   `reports/decision_backtest.md`

**Expected runtime:** 3-5 minutes on a modern laptop. Most of it is the
3-algorithm CV.

### 5.1 Standalone Analyses

Three standalone analyses extend the backtest report. They are not part of
the pipeline because they are diagnostic and do not modify the delivered
system.

```bash
python -m src.evaluation.calibration    # prints ECE and reliability table
python -m src.evaluation.sensitivity    # writes reports/sensitivity.md
python -m src.evaluation.bootstrap      # writes reports/bootstrap.md
```

Or run all three after the pipeline:

```bash
python -m src.pipeline --analyses
```

### 5.2 Calibration Diagnostic

Run manually after each retrain:

```bash
python -m src.evaluation.calibration
```

Prints ECE and a reliability table to stdout. Expected: `ECE = 0.0033`,
which is below the 0.05 threshold from `docs/evaluation_protocol.md` §17.1,
so no calibration step is applied.

### 5.3 List the Steps Without Running

```bash
python -m src.pipeline --list
```

---

## 6. Running the Tests

```bash
pytest
```

Expected: **58 passed**.

```bash
pytest -q
```

Quiet mode, one line per test.

```bash
pytest tests/test_policy.py -v
```

Verbose mode for a specific test file.

### 6.1 What the Tests Cover

| Test file | Coverage |
|---|---|
| `test_policy.py` | Argmin rule, threshold edge cases, amount scaling |
| `test_backtest.py` | Realized cost matrix, per-row cost with amount scaling |
| `test_preprocessing.py` | Fit/transform determinism, unseen categories |
| `test_data_schema.py` | Row counts, dtypes, feature exclusion |
| `test_model.py` | Saved model behavior, calibration |
| `test_pipeline_integration.py` | Required artifacts exist |
| `test_reproducibility.py` | Same seed produces identical predictions |
| `test_app_validation.py` | Input validation, boundary cases |

### 6.2 Test Prerequisites

The tests read from `data/processed/`. Before running `pytest` on a clean
checkout, run the pipeline once:

```bash
python -m src.pipeline
```

---

## 7. Running the Application

### 7.1 Local

```bash
streamlit run app/streamlit_app.py
```

Opens at `http://localhost:8501`.

### 7.2 Deployed

```
https://delayed-label-fraud-decisioning-gefp9s9mbkfdyzhhvescdm.streamlit.app
```

Deployed via Streamlit Community Cloud. The build uses Python 3.11.

### 7.3 Requirements for the App

The app loads these files at startup:

| File | Produced by |
|---|---|
| `models/best_model.pkl` | `evaluate_compare.py` |
| `models/preprocessing.pkl` | `evaluate_compare.py` |
| `models/feature_columns.json` | `evaluate_compare.py` |
| `models/feature_defaults.json` | `evaluate_compare.py` |
| `models/feature_importances.json` | `evaluate_compare.py` |
| `configs/costs.yaml` | committed to repo |
| `reports/cv_results.json` | `train_compare.py` |

If any is missing, the app shows a red error.

See [`documentation/app_guide.md`](app_guide.md) for usage.

---

## 8. Artifacts

### 8.1 Data Layer Outputs

| Path | Description |
|---|---|
| `data/interim/transactions.parquet` | 1,000,000 rows, 34 columns |
| `data/interim/labeled.parquet` | Adds `label_month`, `observed` |
| `data/processed/train.parquet` | 397,039 rows (months 0-2) |
| `data/processed/val.parquet` | 278,627 rows (months 3-4) |
| `data/processed/test.parquet` | 227,491 rows (months 5-6) |
| `data/processed/scored_test.parquet` | Adds `p_fraud` |
| `data/processed/action_log.parquet` | Decision log |

### 8.2 Model Outputs

| Path | Description |
|---|---|
| `models/best_model.pkl` | Selected classifier (LogisticRegression) |
| `models/preprocessing.pkl` | Fitted preprocessing pipeline |
| `models/feature_columns.json` | Training-time feature order |
| `models/feature_defaults.json` | Median/mode per feature |
| `models/feature_importances.json` | Feature importances |

### 8.3 Report Outputs

| Path | Description |
|---|---|
| `reports/decision_backtest.md` | Primary deliverable: policy vs. baseline comparison |
| `reports/model_comparison.md` | Supporting: classifier comparison as policy inputs |
| `reports/cv_results.json` | Per-fold CV metrics |
| `reports/sensitivity.md` | Cost parameter sensitivity (2× sweep) |
| `reports/bootstrap.md` | Bootstrap CIs on policy advantage |

---

## 9. Reproduction Recipe

From a clean checkout, with `data/original/Base.csv` in place:

```bash
# 1. Install
python -m venv .venv
.\.venv\Scripts\Activate.ps1          # Windows
pip install -r requirements.txt

# 2. Run the pipeline and analyses
python -m src.pipeline --analyses

# 3. Verify
pytest -q

# 4. Launch the app
streamlit run app/streamlit_app.py
```

**Expected results after step 2:**

- `reports/model_comparison.md` shows LogisticRegression selected by the
  noise-band guard (LGBM vs. LR CV gap 1.07% < 5% → non-finding →
  simplicity tiebreak)
- `reports/decision_backtest.md` shows:
  - Policy cost/txn = **0.007491**
  - Strongest baseline cost/txn = **0.018737**
  - Policy advantage = **60.02%**
  - Approve / review / block = 205,395 / 21,371 / 725
- `reports/bootstrap.md` shows 95% CI on advantage = **[56.00%, 64.16%]**
- `reports/sensitivity.md` shows minimum advantage = **50.38%** at
  `review_cost=0.04`
- `src.evaluation.calibration` prints **ECE = 0.0033** (gate passed)
- Test rows = 227,491
- Censored rows = 96,843 (9.68%)

**Reproducibility:** all random operations use seed `42`. Library versions
are pinned in `requirements.txt`. LightGBM training is deterministic on
single-threaded execution; the test suite verifies this for both Random
Forest and LightGBM.

---

## 10. Environment Notes

### 10.1 Python Version

**Required: 3.11**

Do not use 3.14. `pyarrow` and possibly other dependencies lack prebuilt
wheels for 3.14.

### 10.2 Package Versions

Documented versions from the most recent verified run:

| Package | Version |
|---|---|
| Python | 3.11 |
| numpy | 2.2.6 |
| pandas | 2.3.3 |
| pyarrow | 19.0.1 |
| scikit-learn | 1.7.2 |
| lightgbm | 4.7.0 |
| streamlit | 1.64.0 |
| joblib | 1.6.0 |
| matplotlib | 3.8+ |
| PyYAML | 6.0.3 |
| pytest | 8.1+ |

Exact pins are enforced in `requirements.txt` at the ranges declared there.

### 10.3 Seeds

| Seed | Used by |
|---|---|
| `SEED = 42` | All stochastic operations in `src/common.py` |
| `seed=42` | LightGBM training |
| `random_state=42` | scikit-learn models |
| `SEED=42` in `bootstrap.py` | Bootstrap resampling |

### 10.4 Determinism

- Random Forest and LightGBM are verified deterministic by
  `tests/test_reproducibility.py` (LightGBM is pinned to `num_threads=1` in
  that test to avoid OpenMP reduction-order variance).
- The pipeline reproduces byte-for-byte from the same raw data, configs, and
  seed.

---

## 11. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'src'` | Running from the wrong directory or missing `conftest.py` | Run from repo root. Ensure `conftest.py` exists at the root. |
| `FileNotFoundError: data/original/Base.csv` | Raw dataset missing | Download from Kaggle and place at `data/original/Base.csv` |
| `ImportError: cannot import name 'DATA_PROCESSED'` | Stale `src/common.py` | Pull latest `main`; verify `src/common.py` defines path constants |
| `TypeError: Object of type float64 is not JSON serializable` | `cv_results.json` serialization | Add `default=float` to `json.dumps` in `train_compare.py` |
| App shows `Missing artifact: models/best_model.pkl` | Pipeline not run | Run `python -m src.pipeline` |
| Streamlit Cloud build fails on `pyarrow` | Python 3.14 has no wheel; source build needs CMake | Set Python version to 3.11 in Streamlit Cloud Advanced settings |
| Streamlit Cloud build fails on missing package | Package absent from `requirements.txt` | Add the package, commit, push |
| Batch upload crashes on large CSV | Memory limit | Split into chunks |
| `pytest` fails on missing artifacts | Pipeline not run | Run `python -m src.pipeline` |
| App is slow on first load | Streamlit caches model loading on first request | Subsequent loads are faster |

---

## 12. One-Command Reference

| Task | Command |
|---|---|
| Full pipeline | `python -m src.pipeline` |
| Full pipeline plus analyses | `python -m src.pipeline --analyses` |
| List steps | `python -m src.pipeline --list` |
| Calibration diagnostic | `python -m src.evaluation.calibration` |
| Sensitivity analysis | `python -m src.evaluation.sensitivity` |
| Bootstrap analysis | `python -m src.evaluation.bootstrap` |
| Run tests | `pytest -q` |
| Launch app | `streamlit run app/streamlit_app.py` |

---

## 13. Related Documents

| Document | Purpose |
|---|---|
| [`documentation/data_dictionary.md`](data_dictionary.md) | Feature reference |
| [`documentation/app_guide.md`](app_guide.md) | How to use the app |
| [`docs/mvp_architecture.md`](../docs/mvp_architecture.md) | As-built system design |
| [`docs/evaluation_protocol.md`](../docs/evaluation_protocol.md) | Metric definitions and stop criteria |
| [`docs/decision_policy.md`](../docs/decision_policy.md) | Policy specification |
| [`docs/data_card.md`](../docs/data_card.md) | Dataset and splits |
| [`README.md`](../README.md) | Project overview |

---

## 14. Guiding Rule

> If a fresh clone cannot reproduce the published numbers with the commands
> in Section 9, the environment or the committed artifacts are wrong. Fix
> the environment or the artifacts, not the numbers.
