# Carousel copy — V2.1 update

Plain-text copy for `carousel_v2_1.html`. This is the sequel to the V2 post:
it opens by referencing the previous result, then delivers the baseline
correction.

---

## 1 — Hook

**Kicker:** Previously · V2 · four weeks ago

**Headline:** I posted a 57.9% result. The number I can defend is 22.3%.

**Visual:** 57.9% struck through in red → 22.3% in large type.

**Stamp:** CORRECTED

**Subline:** The baseline was a 50% cut-off. At a 1.1% fraud rate, that is barely better than approve-all.

**Footer:** Ken Ira Lacson Talingting · BS Machine Learning · 1 / 10 · Swipe →

---

## 2 — What V2 tested

**Kicker:** What V2 tested

**Headline:** Does the result survive harder operating conditions?

**Stats:**
- 6 — tests with kill criteria written first
- 3 — survived · one fragile · two killed
- 44.25% — under a simulated 2% review cap

**Subline:** Review capacity, label delay, retraining, drift, block-rate disparity, calibration. Kill criteria written before each test ran.

**Footer:** Source: `reports/v2_falsification.md` · 2 / 10

---

## 3 — The question

**Kicker:** Then I asked a different question

**Headline:** Was the baseline fair?

**Stats:**
- 0.50 — the V1 baseline cut-off
- 1.1% — the fraud base rate
- ≈ 0 — applications that reach 0.50

**Subline:** V2 tested harder conditions. It did not test whether the comparison was fair. This update does.

**Footer:** Source: `reports/ablation.md` · 3 / 10

---

## 4 — The gap

**Kicker:** The gap

**Headline:** The baseline was a 50% cut-off.

**Visual:** A score histogram clustered near zero, with a red 0.50 marker far to the right.

**Subline:** At a 1.1% base rate, almost no application reaches 0.50. The 57.9% was mostly threshold placement.

**Footer:** Source: `reports/ablation.md` · 4 / 10

---

## 5 — The fix

**Kicker:** The fix

**Headline:** So I rebuilt the comparison.

**Visual:** Cost-versus-threshold curve, minimum at `t = 0.060`, tuned on validation.

**Subline:** A strong simple baseline: a cost-optimal threshold tuned on validation and applied unchanged to test.

**Footer:** Source: `src/evaluation/baselines.py` · 5 / 10

---

## 6 — The corrected headline

**Kicker:** The corrected headline

**Headline:** 57.9% → 22.3%

**Visual:** Two bars — 57.9% (V1, vs a 50% cut-off) and 22.3% (V2.1, vs a cost-optimal threshold).

**Subline:** Smaller. Defensible. The 22.3% is above the 5% effect-size bar, and the 95% CI excludes zero.

**Footer:** Source: `reports/ablation.md` · 6 / 10

---

## 7 — Where the gain comes from

**Kicker:** Where the gain comes from

**Headline:** Three steps, not one.

**Waterfall:**
- Approve-all — 0.018928
- + cost-optimal threshold — 0.012512 (−33.9%)
- + review action — 0.009640 (−23.0%)
- + amount-conditioned loss — 0.007491 (−22.3%)

**Subline:** The steps are sequential, not additive. Threshold placement, then the review action, then amount conditioning.

**Footer:** Source: `reports/ablation.md` · 7 / 10

---

## 8 — What this does to V2

**Kicker:** What this does to V2

**Headline:** The six verdicts are unchanged. The headline shrinks.

**Table:**
- Review capacity — **Survived** — 44.25% under a 2% cap
- Longer label delay — **Survived** — 58.08%*
- Rolling retraining — **Fragile** — LR selected; 4.25% margin
- Feature drift — **Survived** — 9/28; mostly low-importance
- Group disparity — **Killed** — 2.3 pts vs a 5-pt bar
- Stratified calibration — **Killed** — bias ~2.1%

**Subline:** The model, cost matrix, split, and policy are unchanged. So are the caveats.

**Footnote:** *H2 uses a separate 2-month split, so it is not a like-for-like delay comparison. H5 tested block-rate disparity only; review-rate disparity was larger and not pre-registered.

**Footer:** Source: `reports/v2_falsification.md` · 8 / 10

---

## 9 — The lesson

**Kicker:** The lesson

**Headline:** Robustness testing is not only about harder conditions.

**Stamp:** CORRECTED

**Subline:** It is also about a fair comparison. I stress-tested the first four weeks ago and missed the second. The smaller number is the one I can defend.

**Footer:** Ken Ira Lacson Talingting · 9 / 10

---

## 10 — V2.1 is live

**Kicker:** V2.1 is live

**Headline:** An updated case study, an ablation report, and the same six verdicts.

**Stats:**
- 76 — unit and integration tests
- 227,491 — rows in the frozen V1 test window
- 6 — tests with kill criteria written first

**Links:**
- Repo: `github.com/kira-ml/delayed-label-fraud-decisioning`
- Demo: `delayed-label-fraud-decisioning-gefp9s9mbkfdyzhhvescdm.streamlit.app`
- One-pager: V2.1 update in this folder

**Subline:** I'm a third-year ML student. I built a decision system for a delayed-feedback problem — and this is what correcting my own result looked like.

**Footer:** Source of truth: `reports/ablation.md` · `reports/v2_falsification.md` · 10 / 10
