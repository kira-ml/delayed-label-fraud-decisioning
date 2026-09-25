# TODO — 2026-09-25

> **Repository:** `delayed-label-fraud-decisioning`  
> **Scope:** Pipeline validation follow-ups from the code review on 2026-09-25  
> **Status:** Open  
> **Priority order:** Critical → Moderate → Minor → Hygiene

Items are ordered so that a reviewer never sees an unresolved correctness or
consistency issue. Do them top to bottom.

---

## Critical — Correctness

### C1. Fix `select_best()` tiebreak in `evaluate_compare.py`

**File:** `src/models/evaluate_compare.py`  
**Function:** `select_best()`  
**Problem:** The tiebreak loop picks the first algorithm in `SIMPLICITY_ORDER`
that exists in `means`, which is always `logistic_regression` — regardless of
whether LR is actually within the noise band of the best classifier.

**Current code:**

```python
for alg in SIMPLICITY_ORDER:
    if alg in means:
        tiebreak = alg
        break
```

**Required behavior:** Tiebreak only among algorithms whose CV cost is inside
the pre-registered 5% relative band of the best classifier. If no algorithm
qualifies, fall back to the best.

**Fix:**

```python
tiebreak_candidates = [
    alg for alg in SIMPLICITY_ORDER
    if alg in means
    and (means[alg] - best_mean) / best_mean < MIN_RELATIVE_EFFECT
]
tiebreak = tiebreak_candidates[0] if tiebreak_candidates else best_alg
```

**Validation:**  
- [ ] Re-run `python -m src.pipeline`  
- [ ] Confirm selected classifier is still `logistic_regression`  
- [ ] Confirm policy cost/txn = `0.007491`  
- [ ] Confirm no change to `models/best_model.pkl` behavior

---

## Moderate — Protocol and Code Consistency

### M1. Fix class-weight tables in two docs

**Files:** `docs/evaluation_protocol.md` §5, `docs/data_card.md` §9.2

**Problem:** Both tables list `class_weight='balanced'` for LR and
`class_weight='balanced_subsample'` for RF. The code in `train_compare.py`
deliberately uses **no class weights** for any classifier, because reweighting
distorts calibrated probabilities. Both docs also state the rule:
"Any weighting that materially distorts calibrated probabilities is rejected."
The table contradicts the rule.

**Fix:** Update both tables to reflect no `class_weight` for all three
classifiers. Add one line citing the calibration rule as the reason.

- [ ] Update `docs/evaluation_protocol.md` §5 table  
- [ ] Update `docs/data_card.md` §9.2 table  
- [ ] Confirm `train_compare.py` comment still matches

---

### M2. Rename `mvp_backtest.md` → `decision_backtest.md`

**Files:** `src/evaluation/backtest.py`, `README.md`, `docs/README.md`

**Problem:** `mvp_backtest.md` is a legacy filename from the two-layer era.
The report now describes a single decision-pipeline backtest.

**Fix:**

- [ ] Change `OUT = REPORTS / "mvp_backtest.md"` to
      `OUT = REPORTS / "decision_backtest.md"` in `backtest.py`
- [ ] Rename the existing file on disk
- [ ] Update `README.md` link
- [ ] Update `docs/README.md` link
- [ ] Search repo for any other `mvp_backtest` reference

---

### M3. Remove "supplementary" and "Primary" labels

**Files:** `src/common.py`, `src/data/split.py`, `src/models/train_compare.py`

**Problem:** Vocabulary inherited from the retired two-layer architecture.

| File | Change |
|---|---|
| `src/common.py` | Rename `SUPP_TRAIN_MONTHS` → `TRAIN_MONTHS` |
| `src/common.py` | Rename `SUPP_VAL_MONTHS` → `VAL_MONTHS` |
| `src/common.py` | Rename `SUPP_TEST_MONTHS` → `TEST_MONTHS` |
| `src/common.py` | Rename `SUPP_CENSORED_MONTHS` → `CENSORED_MONTHS` |
| `src/common.py` | Remove `ARTIFACTS = Path("artifacts")` (unused) |
| `src/data/split.py` | Docstring: remove "supplementary pipeline" |
| `src/data/split.py` | Update imports of renamed constants |
| `src/models/train_compare.py` | Docstring: remove "Primary" |
| `src/models/train_compare.py` | Report title: `"# Classifier Comparison (Policy Inputs)"` |

- [ ] All renames done  
- [ ] All imports updated  
- [ ] `pytest` still passes (`58 passed`)  
- [ ] Pipeline re-run produces identical numbers

---

## Minor — Stale References

### N1. Fix stale docstrings and section references

| File | Issue | Fix |
|---|---|---|
| `src/evaluation/calibration.py` | Docstring says it reads `artifacts/model.txt` | Update to `models/best_model.pkl` + `models/preprocessing.pkl` |
| `src/evaluation/calibration.py` | Prints `architecture.md §9.2` | Update to `evaluation_protocol.md §17.1` |
| `src/evaluation/sensitivity.py` | Docstring cites `evaluation_protocol.md §12.1` | Should be §14 |
| `src/evaluation/bootstrap.py` | Docstring cites `evaluation_protocol.md §14` | Should be §13.1 |
| `src/models/train_compare.py` | Comment cites `evaluation_protocol.md §4.4` | Should be §5 and §8 |

- [ ] All five updated  
- [ ] Grep repo for `§4.4`, `§12.1`, `architecture.md §9.2`, `artifacts/model.txt`

---

## Minor — Code Quality

### Q1. Share `load_costs()` across evaluation modules

**Files:** `src/evaluation/sensitivity.py`, `src/evaluation/bootstrap.py`

**Problem:** Both define their own `load_costs()`. `src/common.py` already has
one.

- [ ] Import `load_costs` from `src.common` in both files  
- [ ] Delete the local copies  
- [ ] Confirm pipeline still runs

---

### Q2. Clarify `N_SPLITS` in `train_compare.py`

**File:** `src/models/train_compare.py`

**Problem:** `N_SPLITS = 5`, but effective folds = 2 because training has only
3 months. Rename clarifies intent.

- [ ] Rename `N_SPLITS` → `MAX_SPLITS`  
- [ ] Print effective fold count in the report header

---

### Q3. Clarify `--analyses` docstring in `pipeline.py`

**File:** `src/pipeline.py`

**Problem:** `--analyses` runs the pipeline **and** analyses, but the docstring
reads as if it only runs analyses.

- [ ] Update docstring to: "run the pipeline, then calibration, sensitivity,
      and bootstrap"

---

### Q4. Fix daily-log config-count entry

**File:** `docs/daily_log/2026-09-24.md`

**Problem:** Log says "3 algorithms × 4 configs × 2 folds". RF has only 3
configs.

- [ ] Change to "LR: 4 configs, RF: 3 configs, LGBM: 4 configs; 2 folds"

---

## Submission — P2 (unchanged from 2026-09-24 log)

- [ ] Generate `paper/paper.docx` from `paper/paper_imrad.md`
- [ ] Generate `paper/paper.pdf`
- [ ] Sign `documentation/contribution_record.md`
- [ ] Sign `documentation/ownership_declaration.md`
- [ ] Assemble ZIP in `GROUPNAME_PROJECTTITLE/` layout
- [ ] Final checklist against course PDF

---

## Definition of Done

- [ ] All Critical items resolved  
- [ ] All Moderate items resolved  
- [ ] All Minor items resolved  
- [ ] `pytest` reports `58 passed`  
- [ ] `python -m src.pipeline` runs clean end-to-end  
- [ ] Policy cost/txn = `0.007491`  
- [ ] Bootstrap CI = `[56.00%, 64.16%]`  
- [ ] Sensitivity minimum = `50.38%`  
- [ ] ECE = `0.0033`  
- [ ] Selected classifier = `logistic_regression`  
- [ ] No remaining references to `mvp_backtest`, `SUPP_`, `Primary`, or
      `artifacts/model.txt` in source or docs  
- [ ] Reports regenerated with updated titles  
- [ ] Daily log entry for 2026-09-25 written

---

## Suggested Commit Sequence

Keep commits focused so each is reviewable and revertable.

1. `fix(selection): restrict tiebreak to algorithms within noise band`
2. `docs(protocol): remove class_weight from LR/RF tables`
3. `refactor(reports): rename mvp_backtest.md to decision_backtest.md`
4. `refactor(src): remove SUPP_ prefixes and Primary/Supplementary labels`
5. `docs(refs): fix stale section and artifact references`
6. `refactor(eval): share load_costs from src.common`
7. `chore(pipeline): clarify --analyses docstring`
8. `docs(log): correct config count in 2026-09-24 entry`

---

## Notes

- Do **not** re-run the full pipeline more than necessary. One clean run after
  all edits is sufficient, except to validate C1 which needs one run on its own.
- Do **not** regenerate reports between each fix; regenerate once at the end.
- Do **not** touch `problem_framing.md`, `data_card.md` §1–8, or
  `decision_policy.md` — those are frozen v1.0.
- The test window has already been used once. The changes above do not require
  re-evaluating it; only re-running the pipeline against the same split.
