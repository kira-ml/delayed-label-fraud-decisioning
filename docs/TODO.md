# TODO — 2026-09-26

> **Repository:** `delayed-label-fraud-decisioning`  
> **Scope:** Submission package (P3) plus documentation follow-ups  
> **Status:** Open  
> **Priority order:** Submission → Documentation → Optional

All TODO 2026-09-25 items are closed. The framework is frozen at v1.0.
This TODO tracks the remaining submission work and non-blocking
documentation cleanups. No pipeline or code changes are in scope unless
a specific measured failure appears.

---

## Submission — P3 (Blocking)

### S1. Generate `paper/paper.docx`

**Input:** `paper/paper_imrad.md`  
**Output:** `paper/paper.docx`  
**Format:** IEEE conference paper, 6–10 pages excluding appendices, numbered
citations in order of first appearance.

**Required sections:**

- Title, abstract, keywords
- Introduction (problem, objective, significance, related work)
- Methods (dataset, EDA, preprocessing, three algorithms, tuning, metrics,
  calibration gate, decision policy)
- Results (EDA findings, classifier comparison, calibration, policy
  backtest, bootstrap CI, sensitivity sweep, action distribution)
- Discussion (why LR was selected under the noise-band guard, error
  analysis, cost-matrix tradeoffs, limitations)
- Conclusion and recommendations
- References (IEEE numbered)
- Appendices (data dictionary, contribution record, signed declaration)

**Numbers to use (verified from the 2026-09-25 pipeline run):**

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

## Documentation Follow-Ups (Non-blocking)

### D1. Add M4 entry to `TODO.md` if needed

**Check:** verify `documentation/technical_documentation.md` v1.1 no longer
describes the retired two-pipeline architecture in any section. If any
section still does, log it as M4.

- [ ] §5 no longer mentions `--primary` / `--all`
- [ ] §6.2 no longer mentions `--primary`
- [ ] §8 no longer lists `primary_train.parquet` / `primary_test.parquet`
- [ ] §9 no longer mentions `--all`
- [ ] §12 no longer lists `--primary` / `--all`

If any fails, add an M4 entry and fix.

---

### D2. Mark superseded documents

**Files:** `docs/architecture.md`, `docs/mvp_2_weeks.md`

**Action:** add a banner at the top of each file:

```markdown
> **Superseded.** This document has been replaced by
> `mvp_architecture.md` and the v1.0 foundation documents
> (`problem_framing.md`, `data_card.md`, `decision_policy.md`,
> `evaluation_protocol.md`). It is kept for historical context only.
```

- [ ] `docs/architecture.md` banner added
- [ ] `docs/mvp_2_weeks.md` banner added
- [ ] `docs/README.md` already lists both under Superseded (verify)

---

### D3. Update `docs/mvp_architecture.md` to v1.1

**Changes:**

- §13: remove deviations that no longer exist (two classifier paths,
  `train_baseline.py`, `primary_split.py`, `mvp_backtest.md` name)
- Update ECE to 0.0033
- Update test count to 58
- State selected classifier: LogisticRegression
- State action log as-built schema
- Confirm unified pipeline is the sole path

- [ ] §13 cleaned
- [ ] Numbers match the 2026-09-25 run
- [ ] Changelog entry added

---

## Optional / Deferred

Not required for submission. Each requires a specific measured failure
before it is added, and its own stop criterion written before work starts.

| Item | Gate |
|---|---|
| Additional delay regimes | A measured failure of the 1-month regime |
| Rule-based threshold baseline | A reason to compare against a rule, not just the classifier + 0.5 baseline |
| Capacity-aware decisioning | A measured review-queue overflow |
| Rolling-window evaluation | A measured drift that static splits hide |
| Cost-sensitive training | A calibration failure that reweighting would fix |
| Calibration application | ECE > 0.05 after retraining |
| Fairness-aware policy | A measured segment disparity |
| Drift detection | A measured distribution shift |

**Rule:** none of these are started until a measured failure justifies
them.

- [ ] No deferred items started without a measured failure
- [ ] Any started item has its stop criterion written first

---

## Definition of Done

- [ ] All blocking S1–S6 items complete
- [ ] All non-blocking D1–D3 items complete
- [ ] `pytest -q` → 58 passed
- [ ] `python -m src.pipeline --analyses` produces verified numbers
- [ ] All greps from 2026-09-25 still return empty
- [ ] `git status` clean
- [ ] Repository and ZIP archive accessible
- [ ] Final course checklist signed off

---

## Suggested Commit Sequence

1. `docs(paper): add IMRaD DOCX and PDF`
2. `docs(submission): sign contribution record and ownership declaration`
3. `docs(tech-doc): apply M4 fixes if needed`
4. `docs(superseded): add banners to architecture.md and mvp_2_weeks.md`
5. `docs(mvp-arch): update to v1.1`
6. `chore(submission): assemble ZIP archive`
7. `docs: mark TODO 2026-09-26 items complete`

---

## Notes

- The framework is frozen at v1.0. Do **not** change `problem_framing.md`,
  `data_card.md`, `decision_policy.md`, `evaluation_protocol.md`, or the
  pipeline source. The remaining work is packaging and communication.
- The test window has already been used once. No further test-window
  evaluation is permitted unless the framework is explicitly reopened.
- Do not regenerate reports between edits. One clean pipeline run after all
  changes is sufficient.
- Do not swap datasets. BAF is the correct choice for the delayed-label
  framing; ULB and IEEE-CIS lack the monthly temporal granularity required
  by `data_card.md` §5.
- If a professor or reviewer asks why BAF, the answer is: "It is the only
  public fraud dataset with monthly temporal granularity, which is
  required to evaluate a delayed-label decision policy. ULB has no time
  structure; IEEE-CIS has production data but no monthly delay regime.
  BAF is peer-reviewed from NeurIPS 2022."
