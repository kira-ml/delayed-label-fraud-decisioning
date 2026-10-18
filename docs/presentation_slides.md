# Presentation Slides — Fraud Decision Desk

> On-screen content for each slide. Short phrases only; the speaking script is in
> `docs/presentation_notes.md` (also embedded as PowerPoint speaker notes in
> `docs/presentation.pptx`).
>
> Audience: non-technical panel. Target length: just under 10 minutes including the demo.
> Every number matches `docs/main.tex` and `reports/`.

| # | Slide | Speaker | Time |
|---|---|---|---|
| 1 | Title | Ken | 0:20 |
| 2 | The problem: deciding before you know | Ken | 0:50 |
| 3 | What we set out to do | Ken | 0:40 |
| 4 | Our idea: price every option | Lawrence | 1:00 |
| 5 | How we tested it fairly | Lawrence | 0:50 |
| 6 | What the data looks like | Lawrence | 0:40 |
| 7 | The system: in, through, out | John Kelly | 0:45 |
| 8 | Live demo | John Kelly | 2:30 |
| 9 | Result: the desk cut costs by more than half | Smith | 1:00 |
| 10 | It holds up | Smith | 0:40 |
| 11 | Conclusion and limits | Smith | 0:40 |
| 12 | Thank you / Q&A | All | — |
| 13–14 | Backup: demo screens (only if the app fails) | John Kelly | — |
| 15–20 | Supporting figures (Q&A only) | Owner of the topic | — |
| | **Total** | | **≈ 9:55** |

---

## Slide 1 — Title

- **Fraud Decision Desk**
- Cost-Sensitive Fraud Decisioning Under Delayed and Censored Labels
- Ken Ira Lacson Talingting · Lawrence Abad · John Kelly Nogales · Smith Albert Surio
- College of Computing and Information Technologies, National University Philippines
- Introduction to Machine Learning, Final Project · October 17, 2026

## Slide 2 — The problem: deciding before you know

- A bank must **approve or refuse an application now**
- Whether it was fraud is only known **weeks or months later**
- Some fraud is **never reported** at all
- The real question: **"What should we do right now?"**

Visual: timeline. Decision today → (30–120 days) → truth arrives.

## Slide 3 — What we set out to do

1. Treat fraud as a **decision**, not just a prediction
2. Pick between **approve, review, block** by comparing costs
3. Test it **fairly**: on months the system never saw, used once
4. Report the limits **honestly**

## Slide 4 — Our idea: price every option

- Step 1: estimate the **fraud risk** (e.g. 12.5%)
- Step 2: price each option
  - **Let it through** → risk × possible loss
  - **Manual check** → cost of the check + what a check can't stop
  - **Block** → chance it's a genuine customer × cost of turning them away
- Step 3: **stamp the cheapest**
- Bigger amount → bigger possible loss → **more caution**

Visual: the three stamps APPROVED / FOR REVIEW / BLOCKED.

## Slide 5 — How we tested it fairly

- **1,000,000** applications (Bank Account Fraud dataset, synthetic), 8 months
- Learn from months 0–2 → tune on 3–4 → **test once on 5–6 (227,491 apps)**
- Fraud labels arrive **one month late**
- Month 7 has no answer yet: **96,843 apps (9.68%) set aside, not counted as safe**

Visual: 8-month timeline bar: Learn | Tune | Test | Unknown.

## Slide 6 — What the data looks like

- **Fraud is rare:** about 1 in 90 applications (1.10% of 1,000,000)
- **It drifts:** 0.87% in month 2 → 1.47% in month 7, so we test on later months
- **Amounts vary:** most ask for 200; some ask for up to 2,100

Visual (left): column chart, fraud rate by month 0–7, coloured by Learn / Tune / Test / Unknown.
Visual (right): bar chart, share of applications by requested credit limit (≈200, ≈500, ≈1,000, 1,500, ≈2,000).
Source: `data/original/Base.csv`; matches `reports/eda_summary.json` and paper §VI-A.

## Slide 7 — The system: in, through, out

| In | Through | Out |
|---|---|---|
| Application details (28) | Risk model (Logistic Regression) | Fraud risk % |
| Requested credit limit | Price the 3 options | Stamp: approve / review / block |
| Fixed cost settings | Pick the cheapest | Reason + worklist + CSV |

## Slide 8 — Live demo

- Check one application → watch the stamp change with the credit limit
- Check a batch of 500
- Study results tab

Visual: app screenshots (backup if the internet fails).

## Slide 9 — Result: the desk cut costs by more than half

- **57.91% lower cost** than the best simple rule
- 95% confidence: **53.95% to 62.13%**
- Cost per application: **0.007491** vs **0.017798**

Visual: bar chart, cost per application by strategy (desk highlighted).

## Slide 10 — It holds up

- Halved and doubled every cost guess → still **at least 47.76% cheaper**
- The three models scored within **1.07%** of each other (bar for a real difference: 5%)
- So the **decision rule** does the work, not a fancier model

## Slide 11 — Conclusion and limits

**What we showed**
- Weighing costs beats a fixed 50% cut-off: **57.91%** lower cost
- Bigger amounts get more caution, automatically
- Unknown outcomes reported, not hidden (**9.68%**)

**What we did not show**
- Synthetic data, not a real bank
- One label delay tested (one month)
- Credit limit stands in for the amount at risk

## Slide 12 — Thank you

- Questions?
- App: delayed-label-fraud-decisioning-gefp9s9mbkfdyzhhvescdm.streamlit.app
- Code: github.com/kira-ml/delayed-label-fraud-decisioning

## Slides 13–14 — Backup: demo screens

- App screenshots: Everyday (APPROVED), Suspicious (BLOCKED), Unusual at 1,000 (FOR REVIEW), batch of 500
- Use only if the internet or the app fails during the demo

---

## Slides 15–20 — Supporting figures (Q&A only, not in the timed talk)

| # | Figure | Use when asked | Source |
|---|---|---|---|
| 15 | Cross-validated cost of the three models (1.07% gap vs 5% bar) | "Why Logistic Regression?" | `reports/cv_results.json` = paper Table I |
| 16 | Predicted vs actual fraud in 10 risk groups (ECE 0.0033) | "Are the risk scores trustworthy?" | recomputed on the validation window |
| 17 | Decisions (205,395 / 21,371 / 725) and where the 2,861 frauds went | "What did it actually do?" | `data/processed/action_log.parquet` = paper §VI-F |
| 18 | Top 10 model weights, with how to read categorical sums | "What does the model look at?" | `models/feature_importances.json` (same as the app's model card) |
| 19 | Fraud rate by category | EDA questions | `notebooks/01_eda.ipynb`, Figure 2 |
| 20 | Correlations between features | EDA questions | `notebooks/01_eda.ipynb`, Figure 4 |

---

## Never say on stage

| Don't say | Say instead |
|---|---|
| "High accuracy" | "57.91% lower cost" |
| "Production-ready" / "real bank data" | "Tested on a synthetic benchmark" |
| "Works for any delay" | "Tested with a one-month delay" |
| "Our model is the best" | "The models tied; the decision rule made the difference" |
