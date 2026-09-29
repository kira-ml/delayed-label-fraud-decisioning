# TODO — 2026-09-29

> **Repository:** `delayed-label-fraud-decisioning`
> **Scope:** Finalize Markdown documentation before paper team GO SIGNAL
> **Status:** Open
> **Priority order:** Source fixes → Paper-layer corrections → Missing paper files → Verification → Submission packaging

The framework is frozen at v1.0. The pipeline is correct and internally
consistent with the frozen foundation documents. All remaining work is
**documentation correction, file creation, and packaging** — no model
change, no policy change, no cost matrix change, no split change.

The original S1–S6 submission items from the earlier TODO remain valid but
are now **downstream** of the documentation work below. They cannot start
until the paper-layer files are accurate.

---

## Why This TODO Exists

The as-built code (`src/**`), the regenerated reports (`reports/**`), and
the v1.0 foundation documents (`docs/problem_framing.md`,
`docs/evaluation_protocol.md`, `docs/decision_policy.md`, `docs/data_card.md`,
`docs/first_principles_decomposition.md`) are mutually consistent and
trustworthy.

The **paper-writing layer** is not. Four files in `docs/paper/` and
`documentation/app_guide.md` still carry facts from the pre-v1.0
architecture (2026-09-23, one day before the revision). Six
paper-support files referenced by `docs/paper/paper_blueprint.md` do not
exist at all.

If the paper team starts writing from the current paper layer, they will
inherit a wrong classifier, a false tuning claim, a wrong baseline count,
and an unsourced percentage. This TODO fixes that.

---

## Verified Numbers (post-correction — anchor for all edits)

| Fact | Value | Source of truth |
|---|---|---|
| Selected classifier | **LogisticRegression** (`C=10.0`, `max_iter=1000`) | `reports/model_comparison.md`, `src/models/evaluate_compare.py` |
| Selection rule | Noise-band guard: LGBM vs LR gap 1.07% < 5% → non-finding → simplicity | `src/models/evaluate_compare.py` |
| Policy cost/txn | 0.007491 | `reports/decision_backtest.md` |
| Strongest baseline | LGBM + static 0.5 = 0.017798 | `reports/decision_backtest.md` |
| Policy advantage | 57.91% | `reports/decision_backtest.md`, `reports/bootstrap.md` |
| Bootstrap CI | [53.95%, 62.13%] | `reports/bootstrap.md` |
| Sensitivity minimum | 47.76% at `review_cost=0.04` | `reports/sensitivity.md` |
| Calibration ECE | 0.0033 | `src/evaluation/calibration.py` |
| Brier (test) | 0.011506 | `reports/decision_backtest.md` |
| Test rows | 227,491 | `reports/decision_backtest.md` |
| Censored rows | 96,843 (9.68%) | `reports/decision_backtest.md` |
| Action distribution | 205,395 / 21,371 / 725 | `reports/decision_backtest.md` |
| Baselines reported | 6 baselines + policy = 7 rows | `reports/decision_backtest.md` |
| Features | 28 | `src/common.py` `FEATURE_EXCLUDE` |
| Tests | 58 / 58 passing | `pytest -q` |

**The four numbers the paper team must preserve exactly: 57.91%, [53.95%, 62.13%], 96,843, 9.68%.**

---

## Phase 0 — Source-Truth Fixes (Blocking)

These are the root causes. Until they land and the pipeline is re-run,
downstream corrections will not hold.

### 0.1 Fix the hardcoded limitation string in `backtest.py`

**File:** `src/evaluation/backtest.py`
**Location:** near the end of `main()`, where report lines are appended.

Current literal:

```python
L.append("- No hyperparameter tuning, no calibration step, no capacity constraint.")
```

This string is written into `reports/decision_backtest.md` on every run.
It is false: `train_compare.py` runs a documented grid per algorithm and
selects by mean realized cost.

**Fix:**

```python
L.append("- Hyperparameter grid per algorithm was evaluated on the same folds; selection by realized cost.")
L.append("- No calibration step applied (ECE = 0.0033, below the 0.05 gate).")
L.append("- No capacity constraint on the review queue.")
```

This is a string-only change. No model, no policy, no cost matrix, no split.

- [ ] Edit the literal
- [ ] Confirm no other hardcoded claim strings exist in `backtest.py`

### 0.2 Fix the docstring in `sensitivity.py`

**File:** `src/evaluation/sensitivity.py`
**Location:** module docstring.

Current: "For each variation, recomputes decisions via argmin and realized
cost for the policy and all 5 baselines."

Actual: 6 baselines (Random, Approve-all, Block-all, LR+0.5, RF+0.5,
LGBM+0.5) + policy.

**Fix:** change "all 5 baselines" → "all 6 baselines".

- [ ] Edit the docstring

### 0.3 Re-run the pipeline

```bash
python -m src.pipeline --analyses
```

Confirm regenerated reports match the verified numbers table above.

- [ ] `reports/decision_backtest.md` regenerated, limitation text corrected
- [ ] `reports/sensitivity.md` regenerated
- [ ] `reports/bootstrap.md` regenerated
- [ ] `reports/model_comparison.md` unchanged (no model edits)
- [ ] Calibration prints ECE = 0.0033

---

## Phase 1 — Correct Existing Paper-Layer Files

### 1.1 `docs/paper/reference_sheet.md`

This is the linchpin. Every number the paper team uses passes through it.

**Errors to fix:**

| # | Location | Current | Correct |
|---|---|---|---|
| 1 | §4 Methodology Summary | Names **LightGBM** as the classifier | **LogisticRegression** (`C=10.0`, `max_iter=1000`) |
| 2 | §5 Limitations | "No hyperparameter tuning; LightGBM defaults" | Documented LR grid, selection by validation realized cost |
| 3 | §5 Limitations | "5 baselines implemented, not 6" | 6 baselines + policy = 7 rows |
| 4 | §2 Claims | "Static-0.5 reduces cost 7.3% vs approve-all" | Unsourced. Actual LGBM+0.5 vs approve-all is 5.97%. Replace or cite. |
| 5 | §1 Train/Val/Test rows source | `evaluation_protocol.md §7.1` | `evaluation_protocol.md §4` |
| 6 | §1 Fraud rate (overall) source | `data_card.md §4.1` | `data_card.md §4.5` |
| 7 | §1 "Static-0.5 cost/txn" label | Ambiguous; three static-0.5 rows exist | Label as "Strongest static-0.5 (LGBM+0.5)" |
| 8 | §6 Related Work | "cite Elkan 2001, Chapelle 2014, Jesus 2022" | Add Dal Pozzolo 2015 (referenced in `introduction_draft.md`) |

- [ ] Apply all 8 corrections
- [ ] Verify every value against the regenerated reports
- [ ] Confirm every section pointer resolves to the correct section

### 1.2 `docs/paper/abstract_and_index_terms.md`

**Error:** Abstract names LightGBM as the classifier.

**Fix:** replace with "A Logistic Regression classifier feeding an
argmin-of-expected-cost policy..." Keep all four preserved numbers
unchanged.

- [ ] Correct classifier name
- [ ] Confirm the four preserved numbers still read 57.91%, [53.95%, 62.13%], 96,843, 9.68%
- [ ] Confirm no accuracy claim was introduced

### 1.3 `docs/paper/introduction_draft.md`

**Errors:**

| # | Location | Current | Correct |
|---|---|---|---|
| 1 | Paragraph 5 | "compare a cost-sensitive policy against five baselines" | six baselines |
| 2 | Paragraph 6 | "static threshold performs near-identically to approve-all (7.3% reduction)" | 5.97% (LGBM+0.5 vs approve-all) |

**Note:** the bracketed `[STATISTIC NEEDED]` placeholders are expected
handoff content for the paper team. Do not fill them.

- [ ] Correct baseline count
- [ ] Correct the 7.3% figure
- [ ] Leave BSP placeholders untouched

### 1.4 `docs/paper/paper_blueprint.md`

**Errors:**

| # | Location | Current | Correct |
|---|---|---|---|
| 1 | §8 Limitations source | `reports/mvp_backtest.md` | `reports/decision_backtest.md` |
| 2 | Length target | 8–10 pages | 6–10 pages (align with `TODO.md` S1 and course PDF) |

**Also:** the section map lists `paper/related_work.md`,
`methodology.md`, `results_narrative.md`, `discussion_notes.md`,
`references.md` as "to write". These are created in Phase 3. Update the
map's "to write" column to reflect that they now exist.

- [ ] Fix report path
- [ ] Align length target
- [ ] Update section map after Phase 3 completes

---

## Phase 2 — Correct Existing Delivery Documentation

### 2.1 `documentation/app_guide.md` — full rewrite of model sections

This file is dated **2026-09-23**, one day before the v1.0 revision. Every
number in its model card comes from the retired two-layer architecture.

**Errors:**

| # | Location | Current | Correct |
|---|---|---|---|
| 1 | §2.3 table | `models/best_model.pkl` = "Selected LightGBM classifier" | Selected LogisticRegression classifier |
| 2 | §3 Model Card | Algorithm: LightGBM | LogisticRegression |
| 3 | §3 Model Card | Training window: Months 0–5 | Months 0–2 |
| 4 | §3 Model Card | Test window: Months 6–7 | Months 5–6 |
| 5 | §3 Model Card | Macro F1: 0.5336 | 0.5031 |
| 6 | §3 Model Card | ROC-AUC: 0.8766 | 0.8753 |
| 7 | §3 Model Card | Precision (fraud): 0.3096 | 0.7826 (at 0.5 cut on test) |
| 8 | §3 Model Card | Recall (fraud): 0.0424 | 0.0063 (at 0.5 cut on test) |
| 9 | §3 Model Card | ECE: 0.0040 | 0.0033 |
| 10 | §9 Limitations | Test fraud rate ~1.40% | 1.2576% |
| 11 | §9 Limitations | ECE 0.0040 | 0.0033 |
| 12 | §10 Troubleshooting | `python -m src.pipeline --primary` | `python -m src.pipeline` |
| 13 | §6.2 Derived thresholds | Presented as the decision rule | Present as diagnostic view; argmin is source of truth |

**Note on #7/#8:** the app guide's old precision/recall came from the
retired months 0–5 classifier. The current model's test-window classification
behavior at the 0.5 cut is: precision_fraud 0.7826, recall_fraud 0.0063.
State these as "at the 0.5 cut, which is not the deployed operating point."

- [ ] Rewrite §2.3 table
- [ ] Rewrite §3 Model Card
- [ ] Correct §6.2 framing
- [ ] Correct §9 limitations
- [ ] Correct §10 command
- [ ] Verify §8 worked examples still hold under the current model (spot-check at least §8.1 and §8.2)

### 2.2 `docs/data_card.md` — apply the counts already flagged

`documentation/data_dictionary.md §9` already documents these two errors
and instructs that `src/common.py` is the source of truth. The corrections
were never applied.

| # | Location | Current | Correct |
|---|---|---|---|
| 1 | §4.3 Feature Types table | Numeric = 26 | Numeric = 23 |
| 2 | §11.4 | "29 features" | 28 features |

- [ ] Correct §4.3
- [ ] Correct §11.4
- [ ] Remove §9 of `data_dictionary.md` (the discrepancy note is no longer needed once resolved), or update it to record that the correction was applied

### 2.3 `documentation/data_dictionary.md` — post-fix cleanup

- [ ] After §2.2 is done, update or remove §9 "Consistency Notes"

---

## Phase 3 — Create the Six Missing Paper-Support Files

These are the files `paper_blueprint.md` anticipated but that were never
written. The paper team cannot write efficiently without them.

### 3.1 `paper/paper_imrad.md` — master draft

**Purpose:** The single assembled IMRaD draft in IEEE section order. The
DOCX and PDF (S1, S2 in the original TODO) are generated from this file.

**Structure:** Follow `paper_blueprint.md` section map exactly:

```
Title
Authors
Abstract (from abstract_and_index_terms.md)
Index Terms
1. INTRODUCTION (from introduction_draft.md)
2. RELATED WORK (from related_work.md)
3. METHODOLOGY (from methodology.md)
4. DATASET & PREPROCESSING (from data_card.md §2–5)
5. EXPERIMENTAL SETUP (from evaluation_protocol.md §7–9)
6. RESULTS (from results_narrative.md)
7. DISCUSSION (from discussion_notes.md)
8. LIMITATIONS
9. CONCLUSION & FUTURE WORK
References (from references.md)
Appendices (data dictionary, contribution record, ownership declaration)
```

**Rule:** if a sentence states a number, it must appear in
`reference_sheet.md §1`. If it states a claim, it must appear in §2 or §3.
No bullet lists in the body. Prose only.

- [ ] Create skeleton with section headers
- [ ] Populate Introduction from the corrected `introduction_draft.md`
- [ ] Populate all other sections from their support files (Phase 3.2–3.6)
- [ ] Confirm every number traces to `reference_sheet.md`

### 3.2 `paper/related_work.md` — Section 2

**Purpose:** Related-work prose, IEEE numbered citations in order of first
appearance.

**Sources to draw from:** `reference_sheet.md §6` (paper team writes),
`introduction_draft.md` (which lists the four core citations).

**Citations to anchor:**

- Elkan, "The Foundations of Cost-Sensitive Learning," IJCAI 2001
- Chapelle, "Modeling delayed feedback in display advertising," KDD 2014
- Jesus et al., "Turning the Tables," NeurIPS 2022 (BAF dataset)
- Dal Pozzolo et al., "Calibrating probability with an unbalanced class," IEEE CIDM 2015

**Positioning to make explicit:**

- BAF as the dataset (Jesus 2022)
- Cost-sensitive learning as the decision framework (Elkan 2001)
- Delayed feedback as the operational constraint (Chapelle 2014)
- Calibration under imbalance (Dal Pozzolo 2015)
- Why our work differs: end-to-end evaluation of a decision policy on
  fraud data with simulated label delay, censored labels reported,
  pre-registered stop criteria

- [ ] Draft 1–1.5 pages
- [ ] Every citation numbered in order of first appearance
- [ ] No claims beyond what the cited works support

### 3.3 `paper/methodology.md` — Section 3

**Purpose:** Prose version of the decision policy, cost formulation, and
training methodology.

**Sources to draw from:**

- `docs/decision_policy.md §3–6` — actions, expected cost, argmin rule
- `docs/evaluation_protocol.md §5, §8, §9` — algorithms, tuning, policy
- `src/models/train_compare.py` `PARAM_GRIDS` — the actual grids
- `src/models/preprocess.py` — per-algorithm preprocessing rules
- `configs/costs.yaml` — the frozen cost matrix

**Must include:**

- Three actions (approve / review / block)
- Expected-cost formulas
- Argmin rule as source of truth (thresholds as diagnostic)
- Amount-scaled fraud loss with train-calibrated rate
- Three classifiers compared: LR, RF, LGBM
- Hyperparameter grids (per algorithm)
- Preprocessing per algorithm
- Selection criterion: validation realized cost with noise-band guard
- Calibration gate: ECE < 0.05

**Must not:** state "no hyperparameter tuning"; call thresholds the
decision rule; count hyperparameter variants as distinct algorithms.

- [ ] Draft 1.5–2 pages
- [ ] Every formula matches `decision_policy.md §5`
- [ ] Grid contents match `train_compare.py` exactly
- [ ] Preprocessing rules match `preprocess.py` exactly

### 3.4 `paper/results_narrative.md` — Section 6

**Purpose:** Prose narrative of the results, anchored to the reports.

**Sources to draw from:**

- `reports/decision_backtest.md` — policy vs baseline table, action distribution
- `reports/bootstrap.md` — point estimates and CIs
- `reports/sensitivity.md` — full sweep table
- `reports/model_comparison.md` — CV table, selection justification, confusion matrix
- `reports/cv_results.json` — per-fold numbers if needed

**Must include, in order:**

- EDA findings (draw from `eda_summary.json` and `notebooks/01_eda.ipynb`)
- CV comparison table (all three algorithms, mean ± SD realized cost)
- Selection: LR by noise-band guard
- Final test-window policy result: 0.007491
- Baseline comparison table (7 rows)
- Bootstrap CI on the advantage
- Sensitivity sweep minimum
- Calibration result (ECE = 0.0033, Brier = 0.011506)
- Action distribution (205,395 / 21,371 / 725)
- Confusion matrix at the 0.5 cut (not the deployed operating point)

**Rule:** every number must trace to `reference_sheet.md §1`.

- [ ] Draft 2–2.5 pages
- [ ] Include the policy-vs-baseline table
- [ ] Include the CV table
- [ ] State the four preserved numbers exactly

### 3.5 `paper/discussion_notes.md` — Section 7

**Purpose:** Interpretation, error analysis, tradeoffs, connection back
to the problem.

**Sources to draw from:**

- `reports/decision_backtest.md §Interpretation`
- `reports/model_comparison.md §Selection Justification` and `§Failure Analysis`
- `docs/data_card.md §7` (known biases)
- `docs/first_principles_decomposition.md §6` (decision vs classification framing)

**Must discuss:**

- Why LR was selected under the noise-band guard (non-finding + simplicity)
- Why the policy beats static-0.5 baselines (cost rule, not classifier)
- Error analysis: dominant error type at the 0.5 cut, why it does not
  affect the policy result
- Cost-matrix tradeoffs (what the sensitivity sweep revealed)
- Connection to the framing: decision problem, not classification problem
- Honest acknowledgment of what the results do not show

**Must not:** claim production readiness; claim generalization to other
fraud domains; claim the classifier alone is superior.

- [ ] Draft 1–1.5 pages
- [ ] Reference the sensitivity sweep's minimum advantage
- [ ] Name the dominant error type and explain why the policy handles it

### 3.6 `paper/references.md` — IEEE numbered list

**Purpose:** The authoritative reference list.

**Seed citations** (from `introduction_draft.md` and `reference_sheet.md §6`):

1. Bangko Sentral ng Pilipinas, *Digital Payments Transformation Roadmap 2020–2023*, 2023.
2. Elkan, "The Foundations of Cost-Sensitive Learning," IJCAI 2001.
3. Chapelle, "Modeling delayed feedback in display advertising," KDD 2014.
4. Jesus et al., "Turning the Tables: Biased, Imbalanced, Dynamic Tabular Datasets for ML Evaluation," NeurIPS 2022.
5. Dal Pozzolo et al., "Calibrating probability with an unbalanced class: An application to fraud detection," IEEE CIDM 2015.

**Additions required by Phase 3.2 (Related Work):** any additional
citations introduced there.

**Rule:** citations numbered in order of first appearance in the
assembled paper. The list must match the body exactly — no orphan
references, no uncited entries.

- [ ] Seed the five core citations
- [ ] Add any Related Work citations in order
- [ ] Verify every in-text citation in `paper_imrad.md` resolves
- [ ] Verify no reference is uncited in the body

---

## Phase 4 — Verification (DoD Checks)

- [ ] `pytest -q` → 58 passed
- [ ] `python -m src.pipeline --analyses` reproduces the 2026-09-29 numbers
- [ ] `models/best_model.pkl` loads and is a `LogisticRegression` instance
- [ ] `models/preprocessing.pkl` loads
- [ ] `models/feature_columns.json`, `feature_defaults.json`, `feature_importances.json` present
- [ ] `reports/decision_backtest.md` no longer contains "No hyperparameter tuning"
- [ ] `reports/decision_backtest.md` shows LGBM+0.5 as strongest baseline
- [ ] `reports/bootstrap.md` shows CI [53.95%, 62.13%]
- [ ] `reports/sensitivity.md` shows minimum 47.76% at `review_cost=0.04`
- [ ] Calibration run prints ECE = 0.0033
- [ ] Deployed Streamlit URL opens and returns predictions matching local
- [ ] `git status` clean
- [ ] `git grep -n "0.0040\|0.5336\|0.8766\|LightGBM defaults\|5 baselines\|mvp_backtest\|--primary" docs/ documentation/ paper/` returns only historical archive hits

---

## Phase 5 — Original S1–S6 Submission Packaging

These are the items from the earlier TODO. They are now downstream of
Phases 0–4 and can only start once the paper layer is accurate.

### S1. Generate `paper/paper.docx`

**Input:** `paper/paper_imrad.md`
**Output:** `paper/paper.docx`
**Format:** IEEE conference two-column, 6–10 pages excluding appendices,
numbered citations in order of first appearance.

- [ ] Draft complete
- [ ] Section order matches IEEE format
- [ ] Every number cross-checked against `reports/decision_backtest.md`,
      `reports/bootstrap.md`, `reports/sensitivity.md`
- [ ] Related Work cites BAF, ULB, IEEE-CIS with positioning rationale
- [ ] Limitations section names synthetic data and single delay regime

### S2. Generate `paper/paper.pdf`

- [ ] PDF renders correctly
- [ ] Page count within 6–10 excluding appendices
- [ ] Figures and tables legible in print and on screen
- [ ] Citations resolve correctly

### S3. Sign `documentation/contribution_record.md`

- [ ] All members listed
- [ ] Tasks reflect actual work
- [ ] Signatures present

### S4. Sign `documentation/ownership_declaration.md`

- [ ] Declaration reads correctly
- [ ] Instructor signature
- [ ] All member signatures
- [ ] Date completed

### S5. Assemble ZIP archive

Layout required:

```
GROUPNAME_PROJECTTITLE/
├── README.md
├── paper/
│   ├── paper.docx
│   └── paper.pdf
├── documentation/
│   ├── data_dictionary.md
│   ├── technical_documentation.md
│   ├── app_guide.md
│   ├── contribution_record.md
│   └── ownership_declaration.md
├── src/
├── tests/
├── configs/
├── models/
├── reports/
└── requirements.txt
```

Rules:

- Do not include `data/original/Base.csv`
- Do not include `data/processed/` or `data/interim/`
- Include `models/*.pkl` and `models/*.json`
- Include the deployed URL in `README.md` and `documentation/app_guide.md`
- Exclude `docs/archive/` from the ZIP

- [ ] Folder structure correct
- [ ] No oversized files
- [ ] ZIP opens cleanly
- [ ] README inside ZIP points to the deployed URL

### S6. Final checklist against course PDF

- [ ] Deployable application (Streamlit URL works)
- [ ] Source code (repo link + ZIP)
- [ ] Technical documentation
- [ ] Dataset package (original, processed, data dictionary, source, license)
- [ ] IMRaD paper (DOCX + PDF)
- [ ] Contribution record
- [ ] Ownership declaration (signed PDF)
- [ ] All filenames match course PDF requirements
- [ ] All declared URLs open successfully

---

## Definition of Done — 2026-09-29

- [ ] Phase 0 complete (source strings fixed, pipeline re-run)
- [ ] Phase 1 complete (all four paper-layer files corrected)
- [ ] Phase 2 complete (app_guide rewritten, data_card counts fixed)
- [ ] Phase 3 complete (six missing paper files created)
- [ ] Phase 4 complete (all verification checks pass)
- [ ] Phase 5 unblocked (submission packaging can begin)
- [ ] `pytest -q` → 58 passed
- [ ] `python -m src.pipeline --analyses` produces the 2026-09-29 numbers
- [ ] `git status` clean
- [ ] Paper team GO SIGNAL issued

---

## Suggested Commit Sequence

1. `fix(backtest): correct hardcoded limitation string`
2. `docs(sensitivity): correct docstring baseline count`
3. `chore(pipeline): re-run with corrected reports`
4. `docs(paper): correct classifier, tuning, baselines, internal pointers in reference_sheet`
5. `docs(paper): correct classifier name in abstract`
6. `docs(paper): correct baseline count and static-0.5 figure in introduction`
7. `docs(paper): fix report path and length target in blueprint`
8. `docs(app): rewrite model card against v1.0 framework`
9. `docs(data_card): apply flagged count corrections`
10. `docs(paper): add related_work, methodology, results_narrative, discussion_notes, references, paper_imrad`
11. `docs: mark TODO 2026-09-29 items complete`

---

## Notes and Rules

- The framework is frozen at v1.0. Do **not** change `problem_framing.md`,
  `data_card.md` (except §2.2), `decision_policy.md`,
  `evaluation_protocol.md`, or any pipeline source beyond the two string
  fixes in Phase 0.
- The test window has been used once. No further test-window evaluation
  is permitted unless the framework is explicitly reopened.
- Do not regenerate reports between edits. One clean pipeline run after
  Phase 0 is sufficient.
- Do not swap datasets.
- The `docs/archive/` directory is for audit and is not included in the
  submission ZIP. It may retain pre-v1.0 numbers.
- The paper team writes from the corrected paper layer, not from any
  earlier snapshot.
- If a sentence in any paper file states a number, it must appear in
  `reference_sheet.md §1`. If it states a claim, it must appear in §2 or
  §3. This rule is enforced after Phase 1.

---

## Files Created or Modified Today

**Source (2):**
- `src/evaluation/backtest.py` — hardcoded limitation string
- `src/evaluation/sensitivity.py` — docstring

**Paper-layer corrections (3):**
- `docs/paper/reference_sheet.md`
- `docs/paper/abstract_and_index_terms.md`
- `docs/paper/introduction_draft.md`

**Delivery corrections (3):**
- `docs/paper/paper_blueprint.md`
- `documentation/app_guide.md`
- `docs/data_card.md`

**New paper-support files (6):**
- `paper/paper_imrad.md`
- `paper/related_work.md`
- `paper/methodology.md`
- `paper/results_narrative.md`
- `paper/discussion_notes.md`
- `paper/references.md`

**Regenerated by pipeline:**
- `reports/decision_backtest.md`
- `reports/sensitivity.md`
- `reports/bootstrap.md`