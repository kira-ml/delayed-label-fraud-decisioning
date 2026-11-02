# Communication kit

Two tracks: an **update post** that continues the V2 story, and an
**evergreen case study** for applications.

## For the V2.1 update post (connects to the V2 post)

| File | Use |
|---|---|
| [`one_pager_v2_1.html`](one_pager_v2_1.html) | One-page A4 update. Opens with "Previously · V2 · four weeks ago", then the corrected headline. |
| [`carousel_v2_1.html`](carousel_v2_1.html) | Ten 1080×1350 slides. The sequel narrative. |
| [`carousel_v2_1_copy.md`](carousel_v2_1_copy.md) | Editable plain-text copy for the sequel carousel. |
| [`caption_v2_1.md`](caption_v2_1.md) | The LinkedIn caption, written to follow the V2 post. |

## For applications and the portfolio (evergreen)

| File | Use |
|---|---|
| [`one_pager.html`](one_pager.html) | Two-page A4 case study. Attach to applications. |
| [`carousel.html`](carousel.html) | Ten-slide standalone version. |
| [`carousel_copy.md`](carousel_copy.md) | Editable copy for the standalone carousel. |

## Which file when

- **Posting the update this week:** use `one_pager_v2_1.html`,
  `carousel_v2_1.html`, and `caption_v2_1.md`. The first slide says
  "Four weeks ago I posted this" so readers who saw V2 recognize the sequel.
- **Sending an application or portfolio link:** use `one_pager.html`. It is
  self-contained and does not assume the reader saw the V2 post.
- **Do not mix them.** The update leads with the correction; the evergreen
  leads with the method and the evidence.

## Export

### One-pager (A4 PDF)

1. Open the HTML file in Chrome.
2. **Print → Save as PDF.**
3. Paper: **A4**. Margins: **None**. Background graphics: **on**.

### Carousel (1080×1350 PDF)

1. Open the HTML file in Chrome.
2. **Print → Save as PDF.**
3. Paper: **Custom 1080 × 1350 px** if available, or **A4 portrait** with
   scaling; background graphics **on**. Each slide becomes one page.
4. For LinkedIn, upload the PDF as a **document**, or screenshot each slide.

## Source-of-truth rule

Every number in these files comes from:

- `reports/ablation.md` — the fair-baseline comparison and the waterfall
- `reports/v2_falsification.md` — the six verdicts
- `reports/decision_backtest.md` — the V1 backtest
- `reports/bootstrap.md` — the pre-registered V1 interval

If the pipeline changes, regenerate the reports first, then update these
files. **Do not post a number that is not in the repo.**

## Posting sequence

One canonical story, three formats, same week:

1. **GitHub Release** — tag `v2.1.0`, attach the V2.1 one-pager, link
   `reports/ablation.md`. This is the source of truth.
2. **LinkedIn carousel** — `carousel_v2_1.html`, with `caption_v2_1.md`.
3. **Blog post** — the long version: *"I found the flaw in my own fraud
   headline."*
4. **Talk abstract** — *"Falsifying your own ML result: a fraud case study."*
5. **Portfolio page** — the evergreen one-pager, demo video, and links.

Do not post the same content five times. One strong post, one long-form
piece, one permanent page.

## Suggested LinkedIn caption

Use [`caption_v2_1.md`](caption_v2_1.md). It opens by referencing the V2
post, states the correction, and keeps the six verdicts intact.

Short version:

> Four weeks ago I posted V2: six tests with kill criteria written before
> they ran. Three survived, one fragile, two killed.
>
> This week I found the flaw I should have caught first: the baseline.
> V1 compared against a 50% cut-off. At a 1.1% fraud rate, that is barely
> better than approve-all. The defensible advantage is **22.29%**
> (95% CI 19.71–24.95), not 57.91%. The six V2 verdicts are unchanged —
> with the same caveats.
>
> V2.1 is live: [link]

## What to measure

Not likes. Track:

- Saves and comments from practitioners
- Profile views in the week after
- Repo visits and demo clicks
- One meaningful reply ("I work in fraud, and…")
- One conversation that becomes a referral or an interview

## Do not

- Do not post the 57.9% without the 22.3%.
- Do not call the 57.9% "the best simple rule."
- Do not claim production or real-bank impact.
- Do not post before the README and reports match these numbers.
- Do not present V2.1 as a new project. It is an update to V2.
