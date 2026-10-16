# Presentation Slides — Fraud Decision Desk

> On-screen content for each slide. Short phrases only; the speaking script is in
> `docs/presentation_notes.md` (also embedded as PowerPoint speaker notes in
> `docs/presentation.pptx`).
>
> Audience: non-technical panel. Target length: about 9 minutes including the demo.
> Every number matches `docs/main.tex` and `reports/`.

| # | Slide | Speaker | Time |
|---|---|---|---|
| 1 | Title | Ken | 0:20 |
| 2 | The problem: deciding before you know | Ken | 0:50 |
| 3 | What we set out to do | Ken | 0:40 |
| 4 | Our idea: price every option | Lawrence | 1:00 |
| 5 | How we tested it fairly | Lawrence | 0:50 |
| 6 | The system: in, through, out | John Kelly | 0:45 |
| 7 | Live demo | John Kelly | 2:30 |
| 8 | Result: the desk cut costs by more than half | Smith | 1:00 |
| 9 | It holds up | Smith | 0:40 |
| 10 | Conclusion and limits | Smith | 0:40 |
| 11 | Thank you / Q&A | All | — |
| 12–13 | Backup: demo screens (only if the app fails) | John Kelly | — |
| | **Total** | | **≈ 9:15** |

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

## Slide 6 — The system: in, through, out

| In | Through | Out |
|---|---|---|
| Application details (28) | Risk model (Logistic Regression) | Fraud risk % |
| Requested credit limit | Price the 3 options | Stamp: approve / review / block |
| Fixed cost settings | Pick the cheapest | Reason + worklist + CSV |

## Slide 7 — Live demo

- Check one application → watch the stamp change with the credit limit
- Check a batch of 500
- Study results tab

Visual: app screenshots (backup if the internet fails).

## Slide 8 — Result: the desk cut costs by more than half

- **57.91% lower cost** than the best simple rule
- 95% confidence: **53.95% to 62.13%**
- Cost per application: **0.007491** vs **0.017798**

Visual: bar chart, cost per application by strategy (desk highlighted).

## Slide 9 — It holds up

- Halved and doubled every cost guess → still **at least 47.76% cheaper**
- The three models scored within **1.07%** of each other (bar for a real difference: 5%)
- So the **decision rule** does the work, not a fancier model

## Slide 10 — Conclusion and limits

**What we showed**
- Weighing costs beats a fixed 50% cut-off: **57.91%** lower cost
- Bigger amounts get more caution, automatically
- Unknown outcomes reported, not hidden (**9.68%**)

**What we did not show**
- Synthetic data, not a real bank
- One label delay tested (one month)
- Credit limit stands in for the amount at risk

## Slide 11 — Thank you

- Questions?
- App: delayed-label-fraud-decisioning-gefp9s9mbkfdyzhhvescdm.streamlit.app
- Code: github.com/kira-ml/delayed-label-fraud-decisioning

## Slides 12–13 — Backup: demo screens

- App screenshots: Everyday (APPROVED), Suspicious (BLOCKED), Unusual at 1,000 (FOR REVIEW), batch of 500
- Use only if the internet or the app fails during the demo

---

## Never say on stage

| Don't say | Say instead |
|---|---|
| "High accuracy" | "57.91% lower cost" |
| "Production-ready" / "real bank data" | "Tested on a synthetic benchmark" |
| "Works for any delay" | "Tested with a one-month delay" |
| "Our model is the best" | "The models tied; the decision rule made the difference" |
