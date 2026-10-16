# Presentation Script: Fraud Decision Desk

> **Course:** Introduction to Machine Learning, Final Group Project
> **Institution:** National University Philippines · **Date:** October 17, 2026
> **Length:** about 9 minutes including the live demo
> **Audience:** non-technical. Say "fraud risk", not "probability"; "cheapest option",
> not "argmin". Technical words are kept for Q&A only.
>
> On-screen content: `docs/presentation_slides.md`. The same notes are embedded as
> speaker notes in `docs/presentation.pptx`.

## Who says what

| Speaker | Slides | Part | Time |
|---|---|---|---|
| Ken | 1–3 | Problem and objectives | ≈ 1:50 |
| Lawrence | 4–5 | Methodology | ≈ 1:50 |
| John Kelly | 6–7 | System and live demo | ≈ 3:15 |
| Smith | 8–10 | Results and conclusion | ≈ 2:20 |
| All | 11 | Q&A | — |

## Four numbers everyone must know

| Number | What it means |
|---|---|
| **57.91%** | Lower cost than the best simple rule |
| **53.95% to 62.13%** | 95% confidence range for that reduction |
| **47.76%** | Smallest saving when we changed the cost guesses |
| **96,843 (9.68%)** | Applications set aside because their answer wasn't known yet |

---

## Slide 1 — Title · Ken · 0:20

> Good morning. We are Ken, Lawrence, John Kelly, and Smith. Our project is the
> Fraud Decision Desk: a system that decides what a bank should do with an
> application **right now**, before anyone knows if it is fraud.

## Slide 2 — The problem · Ken · 0:50

> When someone applies for a bank account, the bank has to decide immediately:
> approve or refuse.
>
> But the bank only finds out if it was fraud weeks or even months later, usually
> 30 to 120 days. And some fraud is never reported at all.
>
> So the real question is not "is this fraud?" We can't know that yet. The real
> question is: **what should we do right now?**

## Slide 3 — What we set out to do · Ken · 0:40

> We had four goals.
> One: treat fraud as a decision, not just a prediction.
> Two: choose between three actions: approve, review, or block, by comparing
> what each one would cost.
> Three: test it fairly, on months the system had never seen, and only once.
> And four: be honest about the limits.
>
> Lawrence will explain how it works.

## Slide 4 — Our idea: price every option · Lawrence · 1:00

> Our system works in three steps.
>
> First, a model looks at the application and estimates a fraud risk, say 12.5%.
>
> Second, it puts a price on each option. If we **let it through**, we risk
> losing the money. If we **send it for a manual check**, we pay for the check,
> but we stop most of the loss. If we **block it**, we might turn away a genuine
> customer, and that has a cost too.
>
> Third, it simply **picks the cheapest option** and stamps it.
>
> One important detail: a bigger credit limit means a bigger possible loss. So
> the same risk can get approved for a small amount but checked for a large one.
> You'll see this in the demo.

## Slide 5 — How we tested it fairly · Lawrence · 0:50

> We used one million applications from the Bank Account Fraud dataset. It is a
> synthetic dataset, built to look like real bank data.
>
> We kept time in order, like real life. The system learned from the first three
> months, we tuned it on the next two, and we tested it **once** on the last two
> months: 227,491 applications it had never seen.
>
> We also copied the real delay: fraud answers arrive one month late. That means
> the final month, 96,843 applications or 9.68%, had no answer yet. We set those
> aside instead of pretending they were safe.
>
> John Kelly will now show you the system.

## Slide 6 — The system · John Kelly · 0:45

> Here is the system in one picture.
>
> **In:** the application's details, the requested credit limit, and our fixed
> cost settings.
>
> **Through:** a risk model estimates the fraud risk, then the desk prices the
> three options and picks the cheapest.
>
> **Out:** the fraud risk, a stamp (approved, for review, or blocked), the reason
> behind it, and for a batch, a ranked worklist you can download.
>
> Let me show you.

## Slide 7 — Live demo · John Kelly · 2:30

**Before you start:** open the app in a browser tab before the presentation. If
the internet fails, use the screenshots on this slide and say the same lines.

1. **Check one application → Everyday** (0:30)
   > This is a typical application. The fraud risk is 1.3%. The desk stamps it
   > **APPROVED**. Below, you can see why: letting it through is the cheapest of
   > the three options.

2. **Unusual** (0:15)
   > This one has some warning signs: 12.5% risk. At a small credit limit of 200,
   > it is still approved.

3. **Drag the credit limit up to about 1,000** (0:30)
   > Now watch. I'm only raising the credit limit. The risk stays at 12.5%, but
   > the stamp changes to **FOR REVIEW**. A bigger amount means a bigger possible
   > loss, so a manual check is now the cheapest option.

4. **Suspicious** (0:20)
   > This one was real fraud in the dataset. Risk is almost 30%. The desk
   > **BLOCKS** it.

5. **Check a batch → Use the 500-application sample** (0:35)
   > The desk can also check many at once. Out of 500 applications, 450 are
   > approved, 46 go for review, and 4 are blocked. The worklist puts the most
   > important ones on top, and you can download every decision.

6. **Study results tab** (0:20)
   > And this tab shows what we found when we tested it. Smith will explain.

## Slide 8 — Result: the desk cut costs by more than half · Smith · 1:00

> Here is our main result.
>
> We compared the desk with simpler strategies: approve everyone, block
> everyone, random, and the usual approach of a model with a 50% cut-off.
>
> The best simple rule cost 0.017798 per application. Our desk cost 0.007491.
> That is **57.91% lower**.
>
> And we checked that this isn't luck: with 95% confidence, the real reduction
> is between 53.95% and 62.13%.
>
> Why does the 50% cut-off do so badly? Because only about 1 in 100 applications
> is fraud, so the model almost never says "above 50%". It ends up approving
> nearly everything.

## Slide 9 — It holds up · Smith · 0:40

> We didn't want a result that only works with our exact cost guesses. So we
> halved and doubled each cost, one at a time. The desk was still **at least
> 47.76% cheaper** every time.
>
> We also compared three different models. They were within 1.07% of each
> other, below the 5% bar we set in advance for a real difference. So we chose
> the simplest one. The lesson: the **decision rule** does the work, not a
> fancier model.

## Slide 10 — Conclusion and limits · Smith · 0:40

> To conclude: weighing the cost of each option beats a fixed cut-off, by
> 57.91%. Bigger amounts automatically get more caution. And we reported the
> applications we couldn't judge instead of hiding them.
>
> We also want to be clear about the limits. The data is synthetic, not from a
> real bank. We tested one delay, one month. And the credit limit stands in for
> the amount at risk.
>
> Thank you. We're happy to take your questions.

## Slide 11 — Q&A · All

Prepared answers. Whoever owns the topic answers.

| Question | Who | Answer |
|---|---|---|
| Why not just use accuracy? | Smith | Fraud is about 1% of applications, so "approve everyone" is 99% accurate and still loses money. Cost is what the bank cares about. |
| Why Logistic Regression? | Lawrence | All three models were within 1.07%, below our 5% bar. When it's a tie, we pick the simplest and fastest to explain. |
| Where do the cost numbers come from? | Lawrence | They were fixed before any modelling. Wrongly blocking = 0.1, a manual check = 0.02, loss left after a check = 30%. The loss scale comes from the average credit limit in the training months only (521.16). |
| What if the costs are wrong? | Smith | We halved and doubled each one. The desk stayed at least 47.76% cheaper. |
| How do you know the probabilities are trustworthy? | Lawrence | We required the risk scores to match real fraud rates before using them (calibration error 0.0033, our limit was 0.05). |
| What happened to the last month? | Ken | Its fraud answers would arrive after the data ends, so we set aside 96,843 applications (9.68%) instead of counting them as safe. |
| Is this ready for a real bank? | Ken | No. It's a controlled test on synthetic data with one delay setting. It shows the approach works; a bank would need to test it on its own data. |
| What does "cost unit" mean? | John Kelly | One unit is the loss from one fraudulent application of average size. |

---

## Rehearsal checklist

- [ ] App open in a browser tab before starting; screenshots on slide 7 as backup
- [ ] Each speaker hands off with one line ("Lawrence will explain how it works")
- [ ] Time two full runs; cut demo step 6 if over 9:30
- [ ] Never say: "high accuracy", "production-ready", "real bank data"
