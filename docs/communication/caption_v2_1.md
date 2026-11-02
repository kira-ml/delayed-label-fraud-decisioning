Four weeks ago I posted V2: six tests with kill criteria written before they ran.
Three survived. One fragile. Two killed.
I said the headline was bounded, not overturned.

This week I found the flaw I should have caught first: the baseline.

V1 compared the policy against a 50% cut-off. At a 1.1% fraud rate, that is barely better than approve-all. The 57.91% was mostly threshold placement.

I rebuilt the comparison against a strong simple baseline: a cost-optimal threshold tuned on validation.

The defensible advantage is 22.29% (95% CI 19.71–24.95), not 57.91%.

The gain decomposes:
• ~34% from moving to a cost-optimal threshold
• ~23% from adding a manual-review action
• ~22% from conditioning the loss on the transaction amount

What this changes: the headline.
What it does not change: the six V2 verdicts — with the same caveats. Capacity, delay, drift, and the two non-findings all stand. The model, cost matrix, split, and policy are unchanged.

If you saw the V2 one-pager: the six verdicts are unchanged, with the same caveats. Only the headline moved.

The lesson: robustness testing is not only "does it survive harder conditions?" It is also "is the comparison fair?" I stress-tested the first four weeks ago and missed the second.

V2.1 is live: updated one-pager, ablation report, and repo.
Open to data science / ML internships.
#MachineLearning #FraudDetection #DataScience
