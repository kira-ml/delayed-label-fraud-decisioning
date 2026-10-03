# Protocol — Drift Monitoring

> **Repository:** `delayed-label-fraud-decisioning`
> **Branch:** `v2`
> **Document:** Phase B protocol — drift detector
> **Status:** v1.0 — draft, gates `src/monitoring/drift_detector.py`
> **Last updated:** 2026-10-03
> **Earned by:** H4 survived (`reports/v2/intermediate/h4_drift.json`)
> **Governing documents:** `docs/v2/evaluation_framework.md` §5.4, §6.4,
> `docs/v2/falsification_plan.md` §3 H4

---

## 0. Why This Protocol Exists

Per `falsification_plan.md` §3 H4's "If survives" clause, H4's survival
authorizes exactly one Phase B build: a drift detector. This document
specifies the protocol **before** implementation. No code is written
until this file is reviewed.

**Rule:** The drift detector is a monitoring component. It does not
change the policy, the cost matrix, the classifier, or any V1
artifact. It observes and reports.

**Rule:** PSI logic is not duplicated. The detector reuses the PSI
functions from `src/v2/drift.py` where possible.

---

## 1. Inputs

- A reference window of transactions (default: months 0–2)
- A comparison window of transactions (default: a configurable later
  month, or the most recent month)
- The list of 28 classifier features from `models/feature_columns.json`

---

## 2. Detection Method

Population Stability Index per feature between two windows:

```
PSI = sum over bins of (actual% - expected%) * ln(actual% / expected%)
```

Binning rules per `evaluation_framework.md` §5.4:

- **Continuous features:** deciles of the reference window's
  distribution; 10 bins; lowest bin closed on both sides
- **Categorical features:** existing categories of the feature;
  categories present in only one window assigned an epsilon frequency
  (`1e-6`) to avoid division by zero; categories absent in both windows
  omitted

---

## 3. Alert Thresholds

Industry-standard thresholds, applied as written:

| PSI range | Classification | Response |
|---|---|---|
| `< 0.1` | none | no action |
| `[0.1, 0.25)` | moderate | log; monitor over consecutive windows |
| `≥ 0.25` | significant | alert; investigate; consider retrain or recalibrate |

These are the same thresholds used in H4 (`falsification_plan.md` §3 H4
and `src/v2/drift.py`). No new thresholds are introduced.

---

## 4. Response Policy

On a significant-drift alert, the response is **not automated**. A
human reviews the drift report and decides among:

1. **Retrain** — fit the classifier on a newer reference window,
   re-run the calibration gate (`src/evaluation/calibration.py`), and
   re-run the backtest.
2. **Recalibrate** — if only `p_fraud` calibration has drifted, apply
   exactly one calibration method (Platt or isotonic) fit on the newer
   validation window.
3. **Alert only** — if the drifted features carry low importance
   (per `models/feature_importances.json`), no action beyond logging.

**Rule:** No retrain, recalibrate, or policy change is triggered
automatically by the detector. The detector is diagnostic.

**Rule:** Any retrain triggered by a drift alert is a **new experiment
with its own protocol**. It does not reuse V1's frozen test window.

---

## 5. Output

The detector writes a machine-readable report with one row per feature
per adjacent window pair:

| Field | Type |
|---|---|
| `feature` | string |
| `ref_window` | string |
| `cmp_window` | string |
| `psi` | float |
| `classification` | `none` / `moderate` / `significant` |
| `ks_statistic` | float or null (continuous only) |
| `ks_pvalue` | float or null (continuous only) |
| `top_importance` | bool (feature in top-5 by LR importance) |

Plus a summary header:

- max PSI across all features and window pairs
- count of features at each classification level
- count of drifted top-5-importance features
- overall alert level (`none` / `moderate` / `significant`)

---

## 6. Verification Plan

- [ ] Unit test PSI on two synthetic distributions with known drift
  (e.g., two normal distributions with a 1σ shift)
- [ ] Unit test PSI on identical distributions returns 0
- [ ] Unit test categorical PSI on an unchanged distribution returns 0
- [ ] Re-run the detector on the BAF month pairs and confirm max PSI
  matches H4's 3.9429 on `velocity_4w`, months 0→1
- [ ] Confirm no classifier is trained or scored by the detector

---

## 7. Integration

- `src/monitoring/drift_detector.py` implements this protocol.
- `docs/v2/documentation_map.md` records the drift-monitoring
  extension.
- A drift summary is added to V1's paper Limitations section.
- `reports/v2_falsification.md` receives an addendum section after
  Phase B.

---

## 8. What This Protocol Does Not Do

- It does not build a drift-correction model.
- It does not retrain automatically.
- It does not modify the policy, the cost matrix, or the classifier.
- It does not detect label drift (only feature drift).
- It does not detect concept drift (only covariate drift).
- It does not schedule itself; execution cadence is a production
  concern outside V2 scope.

---

## 9. Definition of Done

- [ ] `src/monitoring/drift_detector.py` implemented
- [ ] Unit tests cover the cases in §6
- [ ] Detector reproduces H4's max-PSI number
- [ ] `docs/v2/documentation_map.md` records the extension
- [ ] V1 paper Limitations section receives the drift summary
- [ ] `reports/v2_falsification.md` Phase B addendum written
- [ ] `git status` clean