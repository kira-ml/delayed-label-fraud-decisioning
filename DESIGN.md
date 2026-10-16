---
name: Fraud Decision Desk
description: A teller's desk that stamps every application APPROVED, FOR REVIEW or BLOCKED and prints the reason beside the stamp.
colors:
  cover: "#13294B"
  cover_deep: "#0C1C36"
  cover_ink: "#EEF2F8"
  cover_muted: "#AFC0DA"
  paper: "#F3F5EF"
  sheet: "#FFFFFF"
  rule: "#D6DBD0"
  rule_strong: "#B9C0B3"
  ink: "#1B2430"
  ink_muted: "#3E4752"
  action: "#1F55D6"
  action_hover: "#1746B4"
  neutral_bar: "#B8C0C9"
  approve: "#1E7A46"
  approve_tint: "#E6F2EA"
  review: "#A8660F"
  review_tint: "#F8EEDC"
  block: "#B42318"
  block_tint: "#FBE9E7"
typography:
  display:
    fontFamily: "'Public Sans', 'Segoe UI', system-ui, sans-serif"
    fontSize: "2.4rem"
    fontWeight: 700
    lineHeight: 1.1
    letterSpacing: "-0.03em"
    fontFeature: "tnum"
  headline:
    fontFamily: "'Public Sans', 'Segoe UI', system-ui, sans-serif"
    fontSize: "1.9rem"
    fontWeight: 700
    lineHeight: 1.1
    letterSpacing: "-0.025em"
  title:
    fontFamily: "'Public Sans', 'Segoe UI', system-ui, sans-serif"
    fontSize: "1.55rem"
    fontWeight: 700
    letterSpacing: "-0.02em"
  title-sm:
    fontFamily: "'Public Sans', 'Segoe UI', system-ui, sans-serif"
    fontSize: "1.12rem"
    fontWeight: 700
    letterSpacing: "-0.01em"
  verdict-line:
    fontFamily: "'Public Sans', 'Segoe UI', system-ui, sans-serif"
    fontSize: "1.25rem"
    fontWeight: 700
  body:
    fontFamily: "'Public Sans', 'Segoe UI', system-ui, sans-serif"
    fontSize: "1.02rem"
    fontWeight: 400
    lineHeight: 1.55
  body-why:
    fontFamily: "'Public Sans', 'Segoe UI', system-ui, sans-serif"
    fontSize: "1.06rem"
    fontWeight: 400
    lineHeight: 1.55
  label-step:
    fontFamily: "'Public Sans', 'Segoe UI', system-ui, sans-serif"
    fontSize: "0.82rem"
    fontWeight: 700
    letterSpacing: "0.06em"
  label-column:
    fontFamily: "'Public Sans', 'Segoe UI', system-ui, sans-serif"
    fontSize: "0.85rem"
    fontWeight: 700
    letterSpacing: "0.05em"
  figure:
    fontFamily: "'JetBrains Mono', 'Consolas', ui-monospace, monospace"
    fontSize: "1em"
    fontWeight: 400
    fontFeature: "tnum"
  figure-date:
    fontFamily: "'JetBrains Mono', 'Consolas', ui-monospace, monospace"
    fontSize: "0.78rem"
    fontWeight: 400
    letterSpacing: "0.12em"
    fontFeature: "tnum"
  stamp:
    fontFamily: "'Barlow Condensed', 'Arial Narrow', sans-serif"
    fontSize: "2.6rem"
    fontWeight: 700
    lineHeight: 1
    letterSpacing: "0.08em"
  stamp-tag:
    fontFamily: "'Barlow Condensed', 'Arial Narrow', sans-serif"
    fontSize: "0.95rem"
    fontWeight: 700
    letterSpacing: "0.06em"
rounded:
  swatch: "3px"
  chip: "4px"
  bar: "6px"
  control: "8px"
  stamp: "10px"
  panel: "10px"
  table: "12px"
  sheet: "14px"
spacing:
  row-y: "0.55rem"
  row-x: "0.4rem"
  cell-y: "0.8rem"
  cell-x: "1rem"
  sheet-y: "1.2rem"
  sheet-x: "1.4rem"
  band-y: "1.1rem"
  band-x: "1.8rem"
  container-max: "1240px"
components:
  header-band:
    backgroundColor: "{colors.cover}"
    textColor: "{colors.cover_ink}"
    typography: "{typography.headline}"
    rounded: "{rounded.sheet}"
    padding: "1.1rem 1.8rem"
  legend-chip:
    backgroundColor: "rgba(255,255,255,0.94)"
    typography: "{typography.stamp-tag}"
    rounded: "{rounded.chip}"
    padding: "0.2rem 0.6rem"
  sheet:
    backgroundColor: "{colors.sheet}"
    textColor: "{colors.ink}"
    rounded: "{rounded.sheet}"
    padding: "1.2rem 1.4rem 1.3rem"
  button-action:
    backgroundColor: "{colors.action}"
    textColor: "{colors.sheet}"
    rounded: "{rounded.control}"
  button-action-hover:
    backgroundColor: "{colors.action_hover}"
    textColor: "{colors.sheet}"
    rounded: "{rounded.control}"
  button-default:
    backgroundColor: "{colors.sheet}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
  stamp-approve:
    textColor: "{colors.approve}"
    typography: "{typography.stamp}"
    rounded: "{rounded.stamp}"
    padding: "0.55rem 1.3rem 0.45rem"
  stamp-review:
    textColor: "{colors.review}"
    typography: "{typography.stamp}"
    rounded: "{rounded.stamp}"
    padding: "0.55rem 1.3rem 0.45rem"
  stamp-block:
    textColor: "{colors.block}"
    typography: "{typography.stamp}"
    rounded: "{rounded.stamp}"
    padding: "0.55rem 1.3rem 0.45rem"
  zone-approve:
    backgroundColor: "{colors.approve_tint}"
    textColor: "{colors.approve}"
    height: "32px"
  zone-review:
    backgroundColor: "{colors.review_tint}"
    textColor: "{colors.review}"
    height: "32px"
  zone-block:
    backgroundColor: "{colors.block_tint}"
    textColor: "{colors.block}"
    height: "32px"
  slip-row:
    textColor: "{colors.ink_muted}"
    padding: "0.55rem 0.4rem"
  slip-row-cheapest:
    textColor: "{colors.ink}"
    padding: "0.55rem 0.4rem"
  slip-track:
    backgroundColor: "{colors.neutral_bar}"
    height: "8px"
  ledger-row:
    textColor: "{colors.ink}"
    padding: "0.55rem 0.4rem"
  ledger-head:
    textColor: "{colors.ink_muted}"
    typography: "{typography.label-column}"
    padding: "0.55rem 0.4rem"
  steps-table:
    backgroundColor: "{colors.sheet}"
    textColor: "{colors.ink_muted}"
    rounded: "{rounded.table}"
    padding: "0.8rem 1rem"
  expander:
    backgroundColor: "{colors.sheet}"
    rounded: "{rounded.panel}"
  uploader-dropzone:
    backgroundColor: "{colors.paper}"
---

# Design System: Fraud Decision Desk

## Overview

**Creative North Star: "The Passbook and the Teller Stamp"**

The desk is a bank counter, not a monitoring console. A navy passbook cover runs across the top with a faint guilloche line field, the ground beneath it is pale security-tint paper, and every piece of work happens on a white ruled sheet with hairline rules. When an application is decided, it is stamped: a rotated, double-bordered stamp in one of three inks, with the date printed in teller figures underneath and the reason written in a plain sentence beside it.

The system is quiet so the stamp can be loud. Everything that is not a decision is navy, ink or grey; colour is spent only on the three verdicts and on the one blue that marks what can be pressed. Figures are printed the way a teller machine prints them, in a tabular monospace, so columns of costs and percentages line up and read as records rather than estimates on a dashboard. Density is moderate and type is large, because the surface is read from the back of a room on a projector.

The world explicitly refuses the dark ML dashboard: no metric tiles, no probability tables up front, no glowing charts. Technical detail exists, but sits inside expanders on the same white paper.

**Key Characteristics:**
- Navy passbook-cover band with a guilloche line field; pale security-tint paper ground; white ruled sheets.
- Three stamp inks (green, ochre, red) reserved for the approve / review / block decision.
- One action blue, reserved for pressable and draggable things.
- Teller-printed tabular mono for every amount, percentage, cost and date.
- Condensed stamp lettering for verdict words only.
- One result owns the right column; flat paper, hairline rules, a single soft shadow under the cover.

## Colors

A navy-and-paper banking palette in which colour means either "this was decided" or "you can press this", and nothing else.

### Primary
- **Passbook Cover Navy** (cover): the desk's own voice. Header band ground, the results headline figure, step numbers and step titles in the steps table, the desk's bar in the strategy chart, and Altair feature-importance bars.
- **Cover Shadow Navy** (cover_deep): only as the tint of the header band's ambient shadow (`rgba(12, 28, 54, 0.18)`).
- **Cover Lettering** (cover_ink): title text on the navy band.
- **Cover Subline** (cover_muted): the one-line promise under the band title.

### Secondary
- **Pressable Blue** (action): primary buttons, the selected segment of the sample picker, the slider thumb and value, selected tab, focus rings (`2px solid`, `2px` offset) and text selection. Set as Streamlit `primaryColor` so native widgets inherit it.
- **Pressed Blue** (action_hover): hover state of primary and download buttons.

### Tertiary
- **Approve Green** (approve) / **Approve Tint** (approve_tint)
- **Review Ochre** (review) / **Review Tint** (review_tint)
- **Block Red** (block) / **Block Tint** (block_tint)

The full-strength inks letter the stamp, the band legend chips, the zone names under the risk scale, the CHEAPEST tag and the cheapest row's bar in the cost slip, the batch mix bar and its legend swatches, and the Decision column of the worklist. The tints fill the risk-zone segments only.

### Neutral
- **Security-Tint Paper** (paper): the app ground (Streamlit `backgroundColor`) and the CSV drop zone.
- **Ruled Sheet White** (sheet): work surfaces, expanders, steps table, stamp underlay, gaps between risk zones.
- **Hairline Rule** (rule): sheet borders, table row rules, expander and dataframe borders, chart grid.
- **Strong Rule** (rule_strong): button outlines, the tab-list baseline, the dashed drop-zone border, chart domain and ticks.
- **Ledger Ink** (ink): body text, headings, the risk-scale marker, the double rule above a ledger total.
- **Muted Ink** (ink_muted): captions, step labels, column heads, non-winning slip rows, step descriptions, axis labels.
- **Neutral Bar** (neutral_bar): every bar that is not the winner: losing cost-slip tracks and baseline strategies in the results chart.

### Named Rules
**The Ink Is the Verdict Rule.** Approve green, review ochre and block red appear only where a decision is being shown. They never decorate, never mark a heading, and never signal success or error for anything else.

**The One Pressable Blue Rule.** Action blue appears only on things the presenter can press, drag, select or focus. A non-interactive element in blue is a lie about what can be clicked.

**The Word Beside the Ink Rule.** Decision meaning is never carried by colour alone. Every ink is paired with a word: the stamp says APPROVED / FOR REVIEW / BLOCKED, the slip says CHEAPEST, the mix bar has a worded legend with counts, the worklist prints the decision word.

**The Grey Loser Rule.** Of any set of compared options, only the winner takes colour (its stamp ink, or cover navy for the desk in the results chart); everything else is the neutral bar.

## Typography

**Display Font:** Public Sans (with Segoe UI, system-ui)
**Body Font:** Public Sans (with Segoe UI, system-ui)
**Label/Mono Font:** JetBrains Mono (with Consolas, ui-monospace) for figures; Barlow Condensed 700 (with Arial Narrow) for stamp lettering

All three faces are self-hosted from `app/static/fonts` and inlined as base64 `@font-face` rules, so the desk works offline in the room.

**Character:** A sober civic sans for everything a person reads, a teller-machine mono for everything a machine prints, and a condensed rubber-stamp face for the verdict. The three never swap jobs.

### Hierarchy
- **Display** (700, 2.4rem, 1.8rem at 760px and below, line-height 1.1, -0.03em): the single results headline ("57.91% lower cost…"); its figure is cover navy, Public Sans with tabular numerals.
- **Headline** (700, 1.9rem, 1.6rem at 760px and below, line-height 1.1, -0.025em): the desk title on the cover band.
- **Title** (700, 1.55rem, -0.02em): tab-level section headings.
- **Title small** (700, 1.12rem, -0.01em): sub-section headings on sheets and pages.
- **Verdict line** (700, 1.25rem): the plain-language action beside the stamp ("Let it through").
- **Body** (400, 1.02rem, line-height 1.55): paragraphs, lists, captions at 0.98rem. The reason sentence is 1.06rem and capped at 62ch; the band subline at 70ch.
- **Step label** (700, 0.82rem, 0.06em, uppercase, muted ink): numbered input steps ("1 · Pick an application") standing in for collapsed widget labels.
- **Column head** (0.85rem, 0.05em, uppercase, muted ink): ledger table headers.
- **Figure** (JetBrains Mono, tabular-nums): costs, percentages, counts, risk-scale ticks, step numbers, chart value labels. The stamp date is 0.78rem at 0.12em tracking.
- **Stamp** (Barlow Condensed 700, 2.6rem, 2rem at 760px and below, 0.08em, line-height 1): the verdict word. Legend chips and the CHEAPEST tag use it at 0.95rem.

### Named Rules
**The Teller Prints Figures Rule.** Every amount, percentage, cost, count and date is set in JetBrains Mono with tabular numerals. The one exception is the display-size results figure, which stays in Public Sans with tabular numerals so the headline reads as one line.

**The Stamp Lettering Is for Verdicts Rule.** Barlow Condensed is used only for decision words: the stamp, the band legend and the CHEAPEST tag. Never for headings, buttons or labels.

## Layout

A centred container capped at 1240px on the paper ground, with 1.2rem top and 4rem bottom padding. The cover band sits first, then the standard Streamlit tab strip, then the tab content.

"Check one application" is a two-sheet desk: a 5 : 7 column split with a large gap. The left sheet holds the numbered inputs (sample picker, credit-limit slider, details expander); the right sheet holds one result, top to bottom: stamp and verdict line (6 : 5 split, vertically centred), the reason sentence, the risk-zone scale, then the cost slip. Inside the right sheet, vertical blocks are spaced 0.55rem.

Table rows across the slip and ledgers share one rhythm (0.55rem by 0.4rem); the steps table breathes more (0.8rem by 1rem). Sheets pad 1.2rem top, 1.4rem sides, 1.3rem bottom; the band pads 1.1rem by 1.8rem.

Responsive: at 760px and below, columns stack, the band tightens to 1.2rem by 1.1rem and its legend wraps under the title, the title drops to 1.6rem, the stamp word to 2rem, the results headline to 1.8rem, the steps table's title column loses its fixed 30% width, and the page gains 3.4rem top padding to clear Streamlit's toolbar. At 420px and below, the three sample-picker segments tighten their padding and type (0.92rem) so all three fit on one row.

**The One Result Owns the Right Column Rule.** The right sheet carries exactly one decision for one application. Inputs never move into it, and no second result competes with the stamp.

## Elevation & Depth

Paper lies flat. Depth comes from tone (paper ground, white sheet, navy cover) and from hairline rules, not shadows. The only shadow in the system sits under the cover band, and the only other layered effect is the stamp's translucent white underlay.

### Shadow Vocabulary
- **Cover lift** (`box-shadow: 0 6px 18px rgba(12, 28, 54, 0.18)`): the header band only, so the passbook cover reads as a separate object resting above the paper.
- **Marker halo** (`box-shadow: 0 0 0 2px #FFFFFF`): a sheet-white ring around the risk-scale marker so it stays legible against any zone tint. A separation ring, not elevation.

### Named Rules
**The Paper Lies Flat Rule.** Sheets, tables, expanders and the stamp carry no drop shadow. A new surface separates with a hairline rule and sheet white, not with lift.

## Shapes

Gently rounded paper. Sheets and the cover band are 14px; the steps table 12px; the stamp, expanders and dataframes 10px; buttons 8px; the risk-scale bar 6px; legend chips 4px; mix-legend swatches 3px. Borders are 1px hairlines in rule colour; the drop zone is a 1.5px dashed strong rule; the legend chips are a 1.5px border in their own ink.

The stamp is the one shape that breaks the grid: a 4px double border in its ink, 10px radius, rotated -5 degrees. Bars end square on the left and round 4px on the right, as if printed from a baseline. A ledger total sits under a 2px ink rule, the bookkeeper's double line.

## Components

### Buttons
Plain and confident; blue only when it is the action.
- **Shape:** gently rounded (8px), weight 600, 1px strong-rule outline.
- **Primary:** action blue fill and border, white text (6.31:1).
- **Hover / Focus:** fill and border shift to pressed blue; every focusable element gets a 2px action-blue outline at 2px offset.
- **Default:** sheet white with the strong-rule outline and ink text (the Streamlit default, re-cornered).

### Segmented control (sample picker)
- **Style:** three equal segments that stretch to the sheet width; the selected segment takes action blue (via the theme), the others stay outlined.

### Cards / Containers (ruled sheets)
- **Corner Style:** 14px.
- **Background:** sheet white on the paper ground.
- **Shadow Strategy:** none (see The Paper Lies Flat Rule).
- **Border:** 1px hairline rule.
- **Internal Padding:** 1.2rem 1.4rem 1.3rem.
- **Expanders** are smaller sheets (10px, hairline border, white), with their summary in weight 600.

### Inputs / Fields
- **Style:** Streamlit native sliders, number inputs and selects themed by `primaryColor` action blue; the CSV drop zone is paper with a 1.5px dashed strong rule.
- **Focus:** the global 2px action-blue outline.
- **Error:** Streamlit's native error and warning callouts, in plain sentences that say what to fix.

### Navigation
- **Style:** standard Streamlit tabs, 0.7rem by 1rem padding, labels 1.02rem weight 600 in muted ink, a strong-rule baseline. The selected tab renders in action blue with its underline, consistent with the One Pressable Blue Rule. On narrow screens the strip scrolls horizontally.

### Header Band (passbook cover)
Navy cover, 14px radius, the cover lift shadow. A guilloche field of nine thin sine polylines (white, 11% opacity, 1.2px) sits behind a left-to-right navy gradient that fades out from 52% to 82% width, so the title stays on solid navy and the line field shows only on the right. Title and one-line promise on the left; on the right, the three legend chips (stamp lettering in each ink on 94% white, 1.5px ink border) tell the viewer the three possible stamps before any application is checked.

### Decision Stamp (signature)
The verdict, stamped. Barlow Condensed word in the decision ink, the date beneath it in teller mono, inside a 4px double border with 10px corners on a 60% white underlay, rotated -5 degrees. It carries `role="img"` and an `aria-label` of "Decision: APPROVED" (or the other verdict).
- **Press-in:** 420ms, `cubic-bezier(.2,.9,.25,1)`: from scale 1.35, transparent and 2px blurred, to an overshoot of scale 0.97 at 70%, settling at 1, all while held at -5 degrees.
- **Replay rule:** the stamp's markup depends only on the action and today's date, so Streamlit keeps the same DOM while the slider moves and the press replays only when the decision itself changes.
- **Reduced motion:** under `prefers-reduced-motion: reduce` the animation is removed and the stamp simply appears.

### Risk-Zone Scale
A 32px bar, 6px corners, split into the approve, review and block zones for the current credit limit, filled with their tints and separated by 2px sheet-white gaps. A 3px ink marker with a white halo shows this application, with "This application: 1.3%" pinned above it (anchored left, centre or right depending on position). Zone names in their full inks sit under each segment; five mono percentage ticks run beneath. The axis is 0 to 40% unless the risk is higher.

### Cost Slip
A ruled three-row ledger: option name, a track bar, the expected cost in mono to four decimals, and a tag column. Rows are separated by hairline rules with a closing rule at the bottom. Only the cheapest row is in full ink with its bar in its decision ink and a CHEAPEST tag in stamp lettering; the other rows are muted with neutral-bar tracks (8px, square left, 4px round right).

### Ledger Tables
Totals and comparison tables: hairline rules between rows, uppercase muted column heads without a top rule, numeric columns right-aligned in mono, a 2px ink rule over the total row, and bold for a highlighted row (the weakest sensitivity case). Capped at 640px unless marked wide.

### Steps Table
The four-step "how it decides" explainer on a white sheet with 12px corners. Each row: a mono step number in cover navy, a bold title in cover navy (30% width on desktop), and a muted description; hairline rules between rows.

### Batch Mix Bar
A 34px proportion bar of approve / review / block counts in full inks with 2px gaps and 6px corners, always followed by a worded legend: swatch, decision word, mono count, muted percentage.

## Do's and Don'ts

### Do:
- **Do** reserve approve green (#1E7A46), review ochre (#A8660F) and block red (#B42318) for decisions, and pair every use with the decision word.
- **Do** keep action blue (#1F55D6) on pressable, draggable, selectable or focusable things only, including the 2px focus outline.
- **Do** set every amount, percentage, cost and date in JetBrains Mono with tabular numerals.
- **Do** place a new work surface on a white ruled sheet (14px corners, 1px hairline rule) over the security-tint paper.
- **Do** give compared options the neutral bar (#B8C0C9) and let only the winner take colour.
- **Do** set ink lettering on sheet white or a near-white chip; the tints are fills, not text grounds (review ochre on its tint is only 3.99:1).
- **Do** let the stamp press only when the decision changes, and drop the animation under reduced motion.

### Don't:
- **Don't** build the dark ML dashboard this desk refuses: metric tiles, probability tables up front, dark glowing panels.
- **Don't** use a stamp ink for headings, success toasts, links or decoration.
- **Don't** use Barlow Condensed for anything but verdict words.
- **Don't** add drop shadows to sheets, tables or the stamp; only the cover band is lifted.
- **Don't** let a decision be told by colour alone, in a chart, a bar or a table cell.
- **Don't** put a second result in the right column beside the stamp.
