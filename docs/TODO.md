# TODO — 2026-09-29

> **Repository:** `delayed-label-fraud-decisioning`
> **Scope:** P3 submission packaging and final handoff
> **Status:** Open
> **Priority order:** Paper → Signatures → ZIP → Checklist

All TODO 2026-09-28 items are complete. The framework remains
frozen at v1.0. The consistency pass closed today (2026-09-29) after a
measured baseline change was surfaced and corrected. No further code or
methodology changes are in scope.

**Rule:** No pipeline change, no model change, no cost matrix change, no
split change. Everything remaining is packaging and signatures.

---

## What Was Completed Today (2026-09-29)

All items below are done and committed. Recorded here for continuity.

### Code consistency (Tier 1 + Tier 2)

- [x] Centralized `realized_cost` and `choose_actions`; `bootstrap.py` and `sensitivity.py` now import them
- [x] `bootstrap.py` verifies the strongest baseline instead of assuming it
- [x] `choose_actions` raises on `amount_scaled=True` with missing amounts
- [x] Removed dead imports and legacy `data/raw/baf/Base.csv` fallback
- [x] Reconciled ECE to `0.0033` across all live docs

### Documentation hygiene (Tier 1B)

- [x] Moved `docs/architecture.md`, `docs/mvp_2_weeks.md`, `docs/daily_log/` to `docs/archive/`
- [x] Rewrote `docs/README.md` and root `README.md` to point at archive paths
- [x] Added superseded banners to archived files
- [x] Updated `docs/mvp_architecture.md` to v1.1
- [x] Fixed stale refs in `src/common.py`, `evaluate_compare.py` docstring, `docs/data_card.md §5.4`
- [x] Updated `documentation/technical_documentation.md` §3.4, §4, §5, §9

### Baseline correction (Tier 2)

- [x] Verified RF+0.5 and LGBM+0.5 against LR+0.5
- [x] **Finding:** LGBM+0.5 is the strongest baseline (0.017798), not LR+0.5 (0.018737)
- [x] Extended `score.py`, `backtest.py`, `bootstrap.py`, `sensitivity.py` to report all three static-0.5 baselines
- [x] Re-ran the pipeline; reports regenerated with correct numbers

### Paper sweep

- [x] `docs/paper/reference_sheet.md` — all values updated, stale paths fixed
- [x] `docs/paper/introduction_draft.md` — numbers updated
- [x] `docs/paper/abstract_and_index_terms.md` — numbers updated
- [x] `docs/paper/paper_blueprint.md` — verified no changes needed

### New verified numbers (post-correction)

| Fact | Value |
|---|---|
| Selected classifier | LogisticRegression (`C=10.0`, `max_iter=1000`) |
| Selection rule | Noise-band guard: LGBM vs LR gap 1.07% < 5% |
| Policy cost/txn | 0.007491 |
| **Strongest baseline** | **LGBM + static 0.5 = 0.017798** |
| **Policy advantage** | **57.91%** |
| **Bootstrap CI** | **[53.95%, 62.13%]** |
| **Sensitivity minimum** | **47.76% at `review_cost=0.04`** |
| Calibration ECE | 0.0033 |
| Test rows | 227,491 |
| Censored rows | 96,843 (9.68%) |
| Action distribution | 205,395 / 21,371 / 725 |
| Tests | 58 / 58 passing |

---

## Today's Work (2026-09-29)

### S1. Generate `paper/paper.docx`

**Input:** `paper/paper_imrad.md`
**Output:** `paper/paper.docx`
**Format:** IEEE conference paper, 6–10 pages excluding appendices,
numbered citations in order of first appearance.

**Required sections:**

- Title, abstract, keywords
- Introduction (problem, objective, significance, related work)
- Methods (dataset, EDA, preprocessing, three algorithms, tuning,
  metrics, calibration gate, decision policy)
- Results (EDA findings, classifier comparison, calibration, policy
  backtest, bootstrap CI, sensitivity sweep, action distribution)
- Discussion (why LR was selected under the noise-band guard, error
  analysis, cost-matrix tradeoffs, limitations)
- Conclusion and recommendations
- References (IEEE numbered)
- Appendices (data dictionary, contribution record, signed declaration)

**Numbers to use (verified 2026-09-29):**

| Fact | Value |
|---|---|
| Selected classifier | LogisticRegression (`C=10.0`, `max_iter=1000`) |
| Selection rule | Noise-band guard: LGBM vs LR gap 1.07% < 5% |
| Policy cost/txn | 0.007491 |
| Strongest baseline | LGBM + static 0.5 = 0.017798 |
| Policy advantage | 57.91% |
| Bootstrap CI | [53.95%, 62.13%] |
| Sensitivity minimum | 47.76% at `review_cost=0.04` |
| Calibration ECE | 0.0033 |
| Brier (test) | 0.011506 |
| Test rows | 227,491 |
| Censored rows | 96,843 (9.68%) |
| Action distribution | 205,395 / 21,371 / 725 |
| Tests | 58 / 58 passing |

**Rule:** every number in the paper must appear in
`docs/paper/reference_sheet.md`. Every claim must be traceable to a v1.0
foundation document.

- [ ] Draft complete
- [ ] Section order matches IEEE format
- [ ] Every number cross-checked against `reports/decision_backtest.md`,
      `reports/bootstrap.md`, and `reports/sensitivity.md`
- [ ] Related Work cites BAF, ULB, IEEE-CIS with positioning rationale
- [ ] Limitations section names synthetic data and single delay regime

---

### S2. Generate `paper/paper.pdf`

**Input:** `paper/paper.docx`
**Output:** `paper/paper.pdf`
**Format:** same as S1.

- [ ] PDF renders correctly
- [ ] Page count within 6–10 excluding appendices
- [ ] Figures and tables legible in print and on screen
- [ ] Citations resolve correctly

---

### S3. Sign `documentation/contribution_record.md`

**Contents required:**

- Member names
- Tasks assigned
- Actual contributions
- Signature per member

- [ ] All members listed
- [ ] Tasks reflect actual work
- [ ] Signatures present

---

### S4. Sign `documentation/ownership_declaration.md`

**Contents required:**

- Statement of original work
- Attribution of external sources
- Instructor signature
- All member signatures

- [ ] Declaration reads correctly
- [ ] Instructor signature
- [ ] All member signatures
- [ ] Date completed

---

### S5. Assemble ZIP archive

**Layout required:**

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

**Rules:**

- Do not include `data/original/Base.csv` (too large, license requires
  separate download)
- Do not include `data/processed/` or `data/interim/` (regenerable)
- Include `models/*.pkl` and `models/*.json` (whitelisted, required by app)
- Include the deployed URL in `README.md` and `documentation/app_guide.md`
- Exclude `docs/archive/` from the ZIP — archived docs are for audit, not
  submission

- [ ] Folder structure correct
- [ ] No oversized files
- [ ] ZIP opens cleanly
- [ ] README inside ZIP points to the deployed URL

---

### S6. Final checklist against course PDF

**Checklist categories:**

- [ ] Deployable application (Streamlit URL works)
- [ ] Source code (repo link + ZIP)
- [ ] Technical documentation
- [ ] Dataset package (original, processed, data dictionary, source,
      license)
- [ ] IMRaD paper (DOCX + PDF)
- [ ] Contribution record
- [ ] Ownership declaration (signed PDF)
- [ ] All filenames match course PDF requirements
- [ ] All declared URLs open successfully

---

## Optional / Deferred (Do Not Start)

Unchanged from 2026-09-28. Each requires a specific measured failure before
it is added, and its own stop criterion written before work starts.

| Item | Gate |
|---|---|
| Additional delay regimes | A measured failure of the 1-month regime |
| Rule-based threshold baseline | A reason to compare against a rule |
| Capacity-aware decisioning | A measured review-queue overflow |
| Rolling-window evaluation | A measured drift that static splits hide |
| Cost-sensitive training | A calibration failure that reweighting would fix |
| Calibration application | ECE > 0.05 after retraining |
| Fairness-aware policy | A measured segment disparity |
| Drift detection | A measured distribution shift |

- [ ] No deferred items started without a measured failure
- [ ] Any started item has its stop criterion written first

---

## Definition of Done — 2026-09-29

- [ ] All blocking S1–S6 items complete
- [ ] `pytest -q` → 58 passed
- [ ] `python -m src.pipeline --analyses` produces the 2026-09-29 numbers
- [ ] All greps from 2026-09-28 still return empty
- [ ] `git status` clean
- [ ] Repository and ZIP archive accessible
- [ ] Final course checklist signed off

---

## Suggested Commit Sequence (for tomorrow)

1. `docs(paper): add IMRaD DOCX and PDF`
2. `docs(submission): sign contribution record and ownership declaration`
3. `chore(submission): assemble ZIP archive`
4. `docs: mark TODO 2026-09-29 items complete`

---

## Notes

- The framework is frozen at v1.0. Do **not** change `problem_framing.md`,
  `data_card.md`, `decision_policy.md`, `evaluation_protocol.md`, or the
  pipeline source.
- The test window has been used once. No further test-window evaluation is
  permitted unless the framework is explicitly reopened.
- Do not regenerate reports between edits. One clean pipeline run after all
  changes is sufficient.
- Do not swap datasets.
- The `docs/archive/` directory is for audit and should not be included in
  the submission ZIP.
- The group paper team must write from the reconciled docs, not from any
  earlier snapshot. All live docs were reconciled on 2026-09-29.

---

## Files Ready for Handoff to Paper Team

| File | Purpose |
|---|---|
| `docs/paper/paper_blueprint.md` | IEEE section map and length budget |
| `docs/paper/reference_sheet.md` | Every number and claim, one page |
| `docs/paper/introduction_draft.md` | Section 1 skeleton |
| `docs/paper/abstract_and_index_terms.md` | Copy-paste-ready abstract |

**Rule for the paper team:** if a sentence states a number, it must appear
in `reference_sheet.md` §1. If it states a claim, it must appear in §2 or
§3.