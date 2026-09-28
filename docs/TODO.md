# TODO — 2026-09-28

> **Repository:** `delayed-label-fraud-decisioning`
> **Scope:** Code consistency pass, documentation hygiene, P3 submission
> **Status:** Open
> **Priority order:** Code safety → Doc reconciliation → Doc hygiene → Submission → Optional

All TODO 2026-09-26 blocking items remain open and are carried forward below.
The framework is frozen at v1.0. No model, policy, cost matrix, split, or
verified number changes today unless a specific item explicitly says so.

Today's work is governed by four mental models applied to the current system:

- **Inversion (Via Negativa):** subtract and reconcile; do not add.
- **Map Is Not the Territory:** make docs match the code that actually exists.
- **Asymmetric Betting:** protect the upside (a real finding), cap the
  downside (silent drift), and never fake a barbell.
- **Second-Order Thinking:** every fix is either *no-number-change* (safe) or
  *possible-number-change* (verify first, then decide).

**Rule:** The test window has been used once. No item below may re-tune,
re-select, re-threshold, or re-score in a way that changes a claim. Adding
a baseline to the *report* is permitted only after verifying it does not
change the identity of the strongest baseline.

---

## Tier 1 — Safe Consistency Fixes (No Number Change)

These are structural and documentation fixes. They must not change any
verified number. Re-run the pipeline after each code change and confirm
byte-identical output before proceeding.

### T1. Centralize `realized_cost` and `choose_actions`

**Problem:** three independent implementations of realized cost
(`backtest.py`, `bootstrap.py`, `sensitivity.py`) and two independent
implementations of the argmin policy (`decide.choose_actions` vs. the
local `policy_actions` in bootstrap and sensitivity). A fix in one will
not propagate to the others.

**Action:**

- Keep `src/policy/decide.py::choose_actions` as the single argmin rule.
- Move the string-action `realized_cost` to one importable location
  (either `src/evaluation/backtest.py` or a new small module under
  `src/evaluation/`).
- Have `bootstrap.py` and `sensitivity.py` import both, replacing their
  local copies.
- Keep the int-action encoding local to the modules that need it, or
  unify on string actions. Whichever is chosen, only one encoding crosses
  module boundaries.

**Verification:**

- [ ] `pytest -q` → 58 passed
- [ ] `python -m src.pipeline --analyses` reproduces the 2026-09-25 numbers exactly
- [ ] No number in `reports/*.md` changed

---

### T2. Make `bootstrap.py` verify the strongest baseline

**Problem:** `bootstrap.py` hardcodes `static_actions(p)` (selected
classifier + 0.5) as the comparison baseline. The protocol says compare
against the **strongest** canonical baseline. The code does not check that
the selected classifier's +0.5 baseline is in fact the strongest. This is a
false barbell: it looks like a strongest-baseline comparison but is not
verified to be one.

**Action:**

- Compute all canonical baselines in `bootstrap.py`, as `backtest.py`
  does.
- Use the strongest as the comparison baseline.
- Assert (or print) which baseline was strongest so the report is
  auditable.

**Verification:**

- [ ] The strongest baseline selected by `bootstrap.py` matches the one
      reported in `reports/decision_backtest.md`
- [ ] The reported CI is unchanged (expected: LR+0.5 remains strongest)
- [ ] If the CI *does* change, stop and open a decision entry below before
      committing

---

### T3. Remove dead code and legacy fallbacks

**Action:**

- [ ] Remove unused `TimeSeriesSplit` import from `train_compare.py`
- [ ] Remove unused `SEED` import from `evaluate_compare.py` (or use it)
- [ ] Remove the legacy `data/raw/baf/Base.csv` fallback from `load.py`;
      `data/original/Base.csv` is the canonical and only path
- [ ] Confirm nothing in `tests/` depends on the removed fallback

**Verification:**

- [ ] `pytest -q` → 58 passed
- [ ] Pipeline re-run reproduces identical output

---

### T4. Make `choose_actions` fail loudly on missing amounts

**Problem:** when `amount_scaled: true` and `amounts=None`, `choose_actions`
silently falls back to constant `fraud_loss`. The policy depends on amount
scaling; a silent fallback hides a misconfiguration.

**Action:**

- [ ] Raise `ValueError` when `amount_scaled: true` and `amounts is None`
- [ ] Confirm no caller relies on the silent fallback (grep for
      `choose_actions(` in `src/` and `tests/`)

**Verification:**

- [ ] `pytest -q` → 58 passed (or updated count if a test is added for
      the new raise)
- [ ] Pipeline re-run reproduces identical output

---

### T5. Reconcile the ECE value across documents

**Problem:** ECE is recorded as **0.0033** in `TODO.md`, `docs/roadmap.md`,
`README.md`, and `docs/daily_log/2026-09-25.md`, and as **0.0040** in
`docs/mvp_architecture.md` §7.3 / §16.2 and `docs/decision_policy.md` §9.2.
Only one can be true for the current run.

**Action:**

- [ ] Run `python -m src.evaluation.calibration` and record the actual
      printed ECE
- [ ] Update every document that reports the other value
- [ ] Do not change the code; the code prints the truth

**Verification:**

- [ ] `git grep -n "0.0033\|0.0040" docs/ README.md` returns one value
      only, and it matches the calibration output

---

### T6. Fix stale and misleading references in code and docs

**Action:**

- [ ] `src/common.py`: replace `evaluation_protocol.md §5.1` with the
      correct section (`§9.2` for the cost matrix) or `decision_policy.md
      §14.1`
- [ ] `src/models/evaluate_compare.py` docstring: remove "primary model"
      (retired two-layer vocabulary); replace with "selected classifier"
- [ ] `docs/data_card.md §5.4`: replace "5-fold expanding-window CV" with
      the actual fold count (2, given `min(MAX_SPLITS=5, months-1=2)`)
- [ ] `docs/mvp_architecture.md §13`: remove deviations that no longer
      exist (`train_baseline.py`, two classifier training paths); the
      as-built `src/` has a single path

**Verification:**

- [ ] `git grep -n "primary model\|5-fold" src/ docs/` returns nothing
      unintended
- [ ] No other doc references the removed deviations

---

### T7. Mark superseded documents (carried from 2026-09-26 D2)

**Files:** `docs/architecture.md`, `docs/mvp_2_weeks.md`

**Action:** add the superseded banner from the 2026-09-26 TODO to the top of
each file.

- [ ] `docs/architecture.md` banner added
- [ ] `docs/mvp_2_weeks.md` banner added (partially present; confirm it
      matches the 2026-09-26 wording)
- [ ] `docs/README.md` already lists both under Superseded (verify)

---

### T8. Add M4 entry to `TODO.md` if still needed (carried from D1)

**Check:** verify `documentation/technical_documentation.md` v1.1 no longer
describes the retired two-pipeline architecture in any section.

- [ ] §5 no longer mentions `--primary` / `--all`
- [ ] §6.2 no longer mentions `--primary`
- [ ] §8 no longer lists `primary_train.parquet` / `primary_test.parquet`
- [ ] §9 no longer mentions `--all`
- [ ] §12 no longer lists `--primary` / `--all`

If any fails, add an M4 entry and fix.

---

### T9. Update `docs/mvp_architecture.md` to v1.1 (carried from D3)

**Changes:**

- [ ] §13 cleaned (see T6)
- [ ] ECE updated to the reconciled value (see T5)
- [ ] Test count confirmed at 58 (or updated)
- [ ] Selected classifier stated as LogisticRegression
- [ ] Action log as-built schema confirmed
- [ ] Unified pipeline confirmed as the sole path
- [ ] Changelog entry added

---

## Tier 1B — Documentation Hygiene (No Number Change)

**Purpose:** remove confusion sources from `docs/` before the paper team
reads them. The paper team writes from the map; dead documents are paper
errors waiting to happen.

**Rule:** nothing in this section changes code, numbers, or claims. It is
purely a re-organization of files that are not read by the pipeline.

**Rule:** nothing is deleted without explicit confirmation. Superseded and
historical files are *archived*, not removed. History is preserved for the
defense.

### T12. Archive superseded and historical documentation

**Problem:** `docs/` currently contains live foundation documents,
as-built documents, superseded documents, and session logs in a single
reading path. A new reader — especially the paper team — cannot tell
which files are current without opening each one. This is a
map-vs-territory defect.

**Proposed layout (target):**

```
docs/
├── README.md                          # updated index — reading orders
├── problem_framing.md
├── first_principles_decomposition.md
├── data_card.md
├── decision_policy.md
├── evaluation_protocol.md
├── mvp_architecture.md
├── roadmap.md
├── paper/
│   ├── paper_blueprint.md
│   ├── reference_sheet.md
│   ├── introduction_draft.md
│   └── abstract_and_index_terms.md
└── archive/                           # out of reading path, kept for audit
    ├── architecture.md
    ├── mvp_2_weeks.md
    └── daily_log/
        ├── 2026-09-24.md
        ├── 2026-09-25.md
        └── 2026-09-26.md
```

**Classification:**

- **Keep in place (live):** `problem_framing.md`,
  `first_principles_decomposition.md`, `data_card.md`,
  `decision_policy.md`, `evaluation_protocol.md`, `mvp_architecture.md`,
  `roadmap.md`, `README.md`, `paper/`
- **Move to `docs/archive/`:** `architecture.md`, `mvp_2_weeks.md`
- **Move to `docs/archive/daily_log/`:** all files currently in
  `docs/daily_log/`
- **Delete:** nothing, unless a file is confirmed orphaned (not referenced
  by any live doc) and the user explicitly approves deletion

**Steps:**

- [ ] Confirm actual `docs/` contents with `find docs -name "*.md" | sort`
- [ ] Create `docs/archive/` and `docs/archive/daily_log/`
- [ ] `git mv docs/architecture.md docs/archive/architecture.md`
- [ ] `git mv docs/mvp_2_weeks.md docs/archive/mvp_2_weeks.md`
- [ ] `git mv docs/daily_log docs/archive/daily_log`
- [ ] Rewrite `docs/README.md` so the reading orders point only at live
      documents, and the Superseded section is replaced with a single line:
      "Historical material is in `docs/archive/`."
- [ ] Update any live doc that references `architecture.md` or
      `mvp_2_weeks.md` at the `docs/` level to point at
      `docs/archive/...` instead (check `mvp_architecture.md §3` repo
      layout, `docs/README.md`, and `roadmap.md`)
- [ ] Update the repo layout block in `docs/mvp_architecture.md §3` to
      reflect the new `docs/archive/` location
- [ ] Confirm nothing in `src/` or `tests/` references the moved paths:
      `git grep -n "architecture.md\|mvp_2_weeks.md\|daily_log" src/ tests/`
- [ ] `pytest -q` → 58 passed
- [ ] `python -m src.pipeline --analyses` reproduces the 2026-09-25 numbers
      (this change should not touch the pipeline; the verification confirms
      it)

**Verification:**

- [ ] `docs/README.md` reading orders reference only live documents
- [ ] `docs/archive/` contains the superseded and historical files
- [ ] No live doc links to `docs/architecture.md` or
      `docs/mvp_2_weeks.md`
- [ ] No live doc links to `docs/daily_log/` (use
      `docs/archive/daily_log/` instead)
- [ ] `git grep -n "docs/architecture.md\|docs/mvp_2_weeks.md\|docs/daily_log"` returns only references that intentionally point at
      the archive path
- [ ] No number in `reports/*.md` changed
- [ ] `git status` shows only file moves and `docs/README.md` edits

**Do not:**

- Do not delete `architecture.md`, `mvp_2_weeks.md`, or any daily log
  unless the user explicitly confirms deletion. Archive is the default.
- Do not rename live documents. Only move dead ones.
- Do not add new documentation files. This task only removes confusion
  sources.
- Do not edit the content of moved files. Their banners already mark them
  superseded or historical; leave them as-is.

---

### T13. Add a one-line note to `docs/README.md` explaining the archive

**Action:**

- [ ] In `docs/README.md`, add below the reading orders:

      > Superseded and historical documents are in `docs/archive/`. They
      > are kept for audit and are not part of the current project
      > definition.

**Verification:**

- [ ] The line appears in `docs/README.md`
- [ ] The line does not appear in any foundation document

---

## Tier 2 — Needs Verification Before Changing

Do **not** commit these until the verification step passes. Each item could,
in principle, change a reported number. If a verification step shows the
number would change, stop and open a decision entry in `docs/daily_log/`
before proceeding.

### T10. Verify whether RF+0.5 or LGBM+0.5 could beat LR+0.5

**Problem:** `evaluation_protocol.md §12` lists three static-0.5 baselines
(LR, RF, LGBM), but `backtest.py` only computes the selected classifier's
+0.5 baseline. The code and the protocol disagree.

**Verification first:**

- [ ] Compute RF+0.5 and LGBM+0.5 realized cost on the test window without
      committing anything to the report
- [ ] Confirm whether either beats LR+0.5

**Decision rule:**

- If **neither beats LR+0.5:** add both to the backtest table as
  supporting baselines. The "strongest baseline" identity is unchanged, so
  no claim changes. Update the report.
- If **one beats LR+0.5:** the strongest baseline changes, the reported
  advantage changes, and every doc that quotes the advantage must be
  updated. This is a claim change. Do not proceed without an explicit
  decision entry and a re-read of the protocol's test-window rule.

**Rule:** adding a baseline to the report is not tuning. Re-reading the test
window to *change which baseline is strongest* is a claim change and must be
justified in writing.

---

### T11. Reconcile `evaluation_protocol.md §12` with the as-built backtest

**Action (choose one, then make code and protocol agree):**

- [ ] Option A: add the two missing static-0.5 baselines to `backtest.py`
      (subject to T10's verification)
- [ ] Option B: amend `evaluation_protocol.md §12` to state that only the
      selected classifier's static-0.5 baseline is reported, and state why
      (the other two are dominated by the selected classifier in this run)

Either option is acceptable. Silent disagreement is not.

---

## Tier 3 — P3 Submission (Blocking, Carried Forward)

These are unchanged from TODO 2026-09-26. They are not blocked by Tier 1 or
Tier 2, but the paper must be written from the reconciled docs.

### S1. Generate `paper/paper.docx`

**Input:** `paper/paper_imrad.md`
**Output:** `paper/paper.docx`
**Format:** IEEE conference paper, 6–10 pages excluding appendices,
numbered citations in order of first appearance.

- [ ] Draft complete
- [ ] Section order matches IEEE format
- [ ] Every number cross-checked against `reports/decision_backtest.md`,
      `reports/bootstrap.md`, and `reports/sensitivity.md`
- [ ] Related Work cites BAF, ULB, IEEE-CIS with positioning rationale
- [ ] Limitations section names synthetic data and single delay regime

---

### S2. Generate `paper/paper.pdf`

- [ ] PDF renders correctly
- [ ] Page count within 6–10 excluding appendices
- [ ] Figures and tables legible in print and on screen
- [ ] Citations resolve correctly

---

### S3. Sign `documentation/contribution_record.md`

- [ ] All members listed
- [ ] Tasks reflect actual work
- [ ] Signatures present

---

### S4. Sign `documentation/ownership_declaration.md`

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

- Do not include `data/original/Base.csv`
- Do not include `data/processed/` or `data/interim/`
- Include `models/*.pkl` and `models/*.json`
- Include the deployed URL in `README.md` and `documentation/app_guide.md`

- [ ] Folder structure correct
- [ ] No oversized files
- [ ] ZIP opens cleanly
- [ ] README inside ZIP points to the deployed URL

---

### S6. Final checklist against course PDF

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

## Tier 4 — Optional / Deferred (Do Not Start)

Unchanged from 2026-09-26. Each requires a specific measured failure before
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

## Definition of Done — 2026-09-28

- [ ] All Tier 1 items complete
- [ ] All Tier 1B items complete
- [ ] `docs/` contains only live documents in the reading path;
      superseded and historical files are in `docs/archive/`
- [ ] Tier 2 verification complete and a written decision recorded
- [ ] All blocking S1–S6 items complete
- [ ] All non-blocking D1–D3 items complete (now T7–T9)
- [ ] `pytest -q` → 58 passed
- [ ] `python -m src.pipeline --analyses` produces verified numbers
- [ ] All greps from 2026-09-25 still return empty
- [ ] ECE value consistent across all documents
- [ ] `git status` clean
- [ ] Repository and ZIP archive accessible
- [ ] Final course checklist signed off

---

## Suggested Commit Sequence

1. `refactor(eval): centralize realized_cost and choose_actions`
2. `fix(bootstrap): compare against verified strongest baseline`
3. `chore: remove dead imports and legacy raw path fallback`
4. `fix(policy): raise on amount_scaled without amounts`
5. `docs: reconcile ECE value across all documents`
6. `docs: fix stale section references and legacy vocabulary`
7. `docs(superseded): add banners to architecture.md and mvp_2_weeks.md`
8. `docs(mvp-arch): update to v1.1`
8b. `docs(archive): move superseded and historical docs out of the reading path`
9. `docs(protocol): reconcile §12 with as-built backtest baselines`
10. `docs(paper): add IMRaD DOCX and PDF`
11. `docs(submission): sign contribution record and ownership declaration`
12. `chore(submission): assemble ZIP archive`
13. `docs: mark TODO 2026-09-28 items complete`

---

## Notes

- The framework is frozen at v1.0. Do **not** change `problem_framing.md`,
  `data_card.md`, `decision_policy.md`, `evaluation_protocol.md`, or the
  pipeline source beyond the specific fixes listed in Tier 1 and Tier 2.
- The test window has been used once. No further test-window evaluation is
  permitted unless the framework is explicitly reopened.
- Do not regenerate reports between edits. One clean pipeline run after all
  changes is sufficient.
- Do not swap datasets.
- Every Tier 1 change must be verified against the 2026-09-25 numbers before
  the next change begins. If a Tier 1 change alters any number, stop and
  diagnose before proceeding.
- Tier 1B is file movement only. It must not touch code, numbers, or claims.
  Nothing is deleted; superseded and historical files are archived.
- Tier 2 changes may alter numbers only if verified first and recorded as a
  decision. Silent number changes are forbidden.
- Tier 4 items remain deferred. Inversion applies: subtract and reconcile,
  do not extend.
- The group paper team must write from the reconciled docs, not from any
  earlier snapshot. Finish Tier 1, Tier 1B, and Tier 2 before handing off.