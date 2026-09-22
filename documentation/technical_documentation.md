# Technical Documentation

> **Repository:** `delayed-label-fraud-decisioning`  
> **Course:** Introduction to Machine Learning - Final Group Project  
> **Institution:** National University Philippines  
> **Instructor:** Ken Oliver Caparros  
> **Document:** Technical Documentation  
> **Status:** v1.0  
> **Last updated:** 2026-09-23

---

## 1. Purpose

This document explains how to install, run, and reproduce the project. It
covers:

- System requirements
- Installation steps
- Repository structure
- How to run each pipeline
- How to run the tests
- How to run the app
- Where artifacts land
- Exact reproduction recipe
- Environment notes
- Troubleshooting

It complements:

- [`documentation/app_guide.md`](app_guide.md) - how to use the app
- [`documentation/data_dictionary.md`](data_dictionary.md) - feature reference
- [`docs/mvp_architecture.md`](../docs/mvp_architecture.md) - system design

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
├── requirements.txt
├── conftest.py                     # pytest path bootstrap
├── app/
│   └── streamlit_app.py            # deployed application
├── configs/
│   └── costs.yaml                  # cost matrix
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
│   ├── data_card.md
│   ├── decision_policy.md
│   ├── evaluation_protocol.md
│   ├── architecture.md
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
│   ├── model_comparison.md         # primary course deliverable
│   ├── mvp_backtest.md             # supplementary deliverable
│   ├── cv_results.json
│   ├── sensitivity.md
│   └── bootstrap.md
├── src/
│   ├── common.py
│   ├── pipeline.py
│   ├── data/
│   │   ├── load.py
│   │   ├── primary_split.py
│   │   ├── simulate_delay.py
│   │   └── split.py
│   ├── models/
│   │   ├── preprocess.py
│   │   ├── train_baseline.py
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

## 5. Running the Pipelines

The repository has two pipelines that share the same raw dataset.

| Pipeline | Purpose | Course role |
|---|---|---|
| Primary | Three-algorithm classification comparison | Required deliverable |
| Supplementary | Cost-sensitive decision policy under delayed labels | Project depth |

### 5.1 Primary Pipeline

Builds the 3-algorithm comparison and the deployed model.

```bash
python -m src.pipeline --primary
```

Runs four steps in order:

1. `load` - read `data/original/Base.csv`, add `transaction_id` and
   `amount_proxy`, write `data/interim/transactions.parquet`
2. `primary_split` - chronological split (train months 0-5, test months 6-7)
3. `train_compare` - 5-fold expanding-window CV for Logistic Regression,
   Random Forest, and LightGBM; writes `reports/model_comparison.md` and
   `reports/cv_results.json`
4. `evaluate_compare` - select best model by mean CV Macro F1; retrain on
   full training split; evaluate once on test set; save `models/best_model.pkl`,
   `models/preprocessing.pkl`, and feature metadata

**Expected runtime:** 10-15 minutes on a modern laptop. Most of it is the
3-algorithm CV.

### 5.2 Supplementary Pipeline

Builds the cost-sensitive decision analysis under delayed labels.

```bash
python -m src.pipeline
```

Runs seven steps:

1. `load`
2. `simulate_delay` - assign `label_month = month + 1`; mark `observed`
3. `split` - train months 0-2, val 3-4, test 5-6; censor month 7
4. `train_baseline` - LightGBM with defaults and early stopping; save
   `artifacts/model.txt` and `artifacts/categories.json`
5. `score` - score test set; write `data/processed/scored_test.parquet`
6. `decide` - apply argmin expected-cost policy; write `action_log.parquet`
7. `backtest` - realized cost vs baselines; write `reports/mvp_backtest.md`

### 5.3 Both Pipelines

```bash
python -m src.pipeline --all
```

Runs primary first, then supplementary. Use this to reproduce everything
from a clean checkout in one command.

### 5.4 Supplementary Analyses

Two standalone analyses extend the supplementary report. They are not part
of the pipeline because they are diagnostic, not part of the delivered
system.

```bash
python -m src.evaluation.sensitivity    # writes reports/sensitivity.md
python -m src.evaluation.bootstrap      # writes reports/bootstrap.md
```

Or run both after the supplementary pipeline:

```bash
python -m src.pipeline --analyses
```

### 5.5 Calibration Diagnostic

Not part of any pipeline. Run manually after retraining:

```bash
python -m src.evaluation.calibration
```

Prints ECE and a reliability table to stdout. Expected: `ECE = 0.0040`,
which is below the 0.05 threshold from `docs/architecture.md` section 9.2,
so no calibration step is applied.

### 5.6 List the Steps Without Running

```bash
python -m src.pipeline --list
```

---

## 6. Running the Tests

```bash
pytest
```

Expected: **60 passed**.

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
checkout, run at least one pipeline:

```bash
python -m src.pipeline --primary
```

Tests that check primary artifacts require `--primary`. Tests that check
supplementary artifacts require the default run. To satisfy both:

```bash
python -m src.pipeline --all
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
https://delayed-label-fraud-decisioning-gefp9s9mbkfdyzhvsecdm.streamlit.app
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

### 8.1 Primary Pipeline Outputs

| Path | Description |
|---|---|
| `data/interim/transactions.parquet` | 1,000,000 rows, 34 columns |
| `data/processed/primary_train.parquet` | 794,989 rows (months 0-5) |
| `data/processed/primary_test.parquet` | 205,011 rows (months 6-7) |
| `models/best_model.pkl` | Selected LightGBM classifier |
| `models/preprocessing.pkl` | Fitted LGBMPreprocessor |
| `models/feature_columns.json` | Training-time feature order |
| `models/feature_defaults.json` | Median/mode per feature |
| `models/feature_importances.json` | Feature importances |
| `reports/model_comparison.md` | Primary course deliverable |
| `reports/cv_results.json` | Per-fold CV metrics |

### 8.2 Supplementary Pipeline Outputs

| Path | Description |
|---|---|
| `data/interim/labeled.parquet` | Adds `label_month`, `observed` |
| `data/processed/train.parquet` | 397,039 rows (months 0-2) |
| `data/processed/val.parquet` | 278,627 rows (months 3-4) |
| `data/processed/test.parquet` | 227,491 rows (months 5-6) |
| `data/processed/scored_test.parquet` | Adds `p_fraud` |
| `data/processed/action_log.parquet` | Decision log |
| `artifacts/model.txt` | Supplementary LightGBM booster |
| `artifacts/categories.json` | Training-time category mapping |
| `reports/mvp_backtest.md` | Supplementary deliverable |
| `reports/sensitivity.md` | Cost parameter sensitivity |
| `reports/bootstrap.md` | Bootstrap CIs on policy advantage |

---

## 9. Reproduction Recipe

From a clean checkout, with `data/original/Base.csv` in place:

```bash
# 1. Install
python -m venv .venv
.\.venv\Scripts\Activate.ps1          # Windows
pip install -r requirements.txt

# 2. Run both pipelines
python -m src.pipeline --all

# 3. Optional supplementary analyses
python -m src.pipeline --analyses

# 4. Verify
pytest -q

# 5. Launch the app
streamlit run app/streamlit_app.py
```

**Expected results after step 2:**

- `reports/model_comparison.md` shows LightGBM selected with CV Macro F1
  0.5337
- Test Macro F1 = 0.5336
- Test ROC-AUC = 0.8766
- Test confusion matrix `[[201861, 272], [2756, 122]]`
- `reports/mvp_backtest.md` shows policy advantage over the strongest
  baseline

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
| App shows `Missing artifact: models/best_model.pkl` | Primary pipeline not run | Run `python -m src.pipeline --primary` |
| Streamlit Cloud build fails on `pyarrow` | Python 3.14 has no wheel; source build needs CMake | Set Python version to 3.11 in Streamlit Cloud Advanced settings |
| Streamlit Cloud build fails on missing package | Package absent from `requirements.txt` | Add the package, commit, push |
| Batch upload crashes on large CSV | Memory limit | Split into chunks |
| `pytest` fails on missing primary artifacts | Supplementary pipeline run only | Run `python -m src.pipeline --primary` |
| App is slow on first load | Streamlit caches model loading on first request | Subsequent loads are faster |

---

## 12. One-Command Reference

| Task | Command |
|---|---|
| Primary pipeline | `python -m src.pipeline --primary` |
| Supplementary pipeline | `python -m src.pipeline` |
| Both pipelines | `python -m src.pipeline --all` |
| Both pipelines plus analyses | `python -m src.pipeline --analyses` |
| List steps | `python -m src.pipeline --list` |
| Sensitivity analysis | `python -m src.evaluation.sensitivity` |
| Bootstrap analysis | `python -m src.evaluation.bootstrap` |
| Calibration diagnostic | `python -m src.evaluation.calibration` |
| Run tests | `pytest -q` |
| Launch app | `streamlit run app/streamlit_app.py` |

---

## 13. Related Documents

| Document | Purpose |
|---|---|
| [`documentation/data_dictionary.md`](data_dictionary.md) | Feature reference |
| [`documentation/app_guide.md`](app_guide.md) | How to use the app |
| [`docs/mvp_architecture.md`](../docs/mvp_architecture.md) | As-built system design |
| [`docs/evaluation_protocol.md`](../docs/evaluation_protocol.md) | Metric definitions |
| [`docs/data_card.md`](../docs/data_card.md) | Dataset and splits |
| [`README.md`](../README.md) | Project overview |

---

## 14. Guiding Rule

> If a fresh clone cannot reproduce the published numbers with the commands
> in Section 9, the environment or the committed artifacts are wrong. Fix
> the environment or the artifacts, not the numbers.
