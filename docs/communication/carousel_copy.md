# Carousel copy — Delayed-Label Fraud Decisioning

Plain-text copy for the ten slides in `carousel.html`. Edit here first, then
update the HTML. One idea and one number per slide.

---

## 1 — Hook

**Kicker:** Fraud decisioning · 2026

**Headline:** My fraud model cut cost by 57%.

**Big figure:** 57.9%

**Stamp:** QUESTIONABLE

**Subline:** Then I checked the baseline. It was a 50% cut-off — at a 1.1% fraud rate, that is almost approve-all.

**Footer:** Ken Ira Lacson Talingting · BS Machine Learning · 1 / 10

---

## 2 — The setup

**Kicker:** The setup

**Headline:** A million applications. A 1.1% fraud rate. Labels arrive a month late.

**Stats:**
- 1.0M — applications in the BAF dataset
- 1.1% — fraud rate, a severe class imbalance
- 1 mo — label delay, with censored rows excluded

**Subline:** Decide in milliseconds. Learn weeks later. A missed fraud and a false positive do not cost the same.

**Footer:** Source: `docs/data_card.md` · 2 / 10

---

## 3 — The policy

**Kicker:** The policy

**Headline:** Don't classify. Price three actions and pick the cheapest.

**Cards:**
- **Approve** — `p × fraud_loss` — Let it through; absorb the fraud loss if it is fraud.
- **Review** — `review_cost + p × residual_loss` — A human checks it; some loss may remain.
- **Block** — `(1 − p) × false_positive_cost` — Stop it; pay the cost of a wrongly blocked good customer.

**Subline:** The argmin is the source of truth. Derived thresholds are a diagnostic view only.

**Footer:** Source: `src/policy/decide.py` · `configs/costs.yaml` · 3 / 10

---

## 4 — The flaw

**Kicker:** The flaw

**Headline:** The baseline was a 50% cut-off.

**Visual:** A score histogram clustered near zero, with a red 0.50 marker far to the right. Label: "Almost no mass at 0.50."

**Subline:** At a 1.1% base rate, a 0.5 cut-off is almost approve-all. The 57.9% win was mostly threshold placement, not modeling.

**Footer:** Source: `reports/ablation.md` · 4 / 10

---

## 5 — The fix

**Kicker:** The fix

**Headline:** Compare against the best simple rule.

**Visual:** Cost-versus-threshold curve, minimum at `t = 0.060`, tuned on validation.

**Subline:** A cost-optimal threshold tuned on the validation window and applied unchanged to test. It is the strongest rule a competent team would deploy.

**Footer:** Source: `src/evaluation/baselines.py` · 5 / 10

---

## 6 — The real number

**Kicker:** The real number

**Headline:** 57.9% → 22.3%

**Visual:** Two bars — 57.9% against a 0.5 cut-off (neutral), 22.3% against the fair baseline (navy).

**Subline:** Still real. Smaller. Honest. The 22.3% is above the 5% effect-size bar, and the 95% CI excludes zero.

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

## 8 — Then I tried to kill it

**Kicker:** Then I tried to kill it

**Headline:** Six pre-registered tests.

**Table:**
- Review capacity — **Survived** — 44.25% at 2%
- Longer label delay — **Survived** — 58.08%
- Rolling retraining — **Fragile** — gap 4.25%
- Feature drift — **Survived** — max PSI 3.94
- Group disparity — **Killed** — 2.26pp < 5pp
- Stratified calibration — **Killed** — ECE 0.0600

**Subline:** Three survived, one is fragile, two were killed. Non-findings are reported at the same length as survivors.

**Footer:** Source: `reports/v2_falsification.md` · 8 / 10

---

## 9 — The takeaway

**Kicker:** The takeaway

**Headline:** Compare against the best simple rule, not the weakest.

**Stamp:** CORRECTED

**Subline:** Your headline will shrink. Your credibility won't.

**Footer:** Ken Ira Lacson Talingting · 9 / 10

---

## 10 — The artifact

**Kicker:** The artifact

**Headline:** A decision desk, a benchmark, and a falsification study.

**Stats:**
- 76 — tests passing
- 227k — held-out test rows
- 6 — pre-registered hypotheses

**Links:**
- Repo: `github.com/kira-ml/delayed-label-fraud-decisioning`
- Demo: `delayed-label-fraud-decisioning.streamlit.app`
- Case study: two-page PDF in this folder

**Subline:** I'm a third-year ML student. I build decision systems for delayed-feedback problems — and I falsify my own results first.

**Footer:** Source of truth: `reports/ablation.md` · `reports/v2_falsification.md` · 10 / 10
