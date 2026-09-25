import numpy as np
import pandas as pd
from datetime import datetime, timezone
from src.common import DATA_PROCESSED, DATA_INTERIM, REPORTS, load_costs

ACTION_LOG = DATA_PROCESSED / "action_log.parquet"
TEST = DATA_PROCESSED / "test.parquet"
LABELED = DATA_INTERIM / "labeled.parquet"
OUT = REPORTS / "decision_backtest.md"

SEED = 42
RANDOM_ACTIONS = ["approve", "review", "block"]


def realized_cost(actions, y, costs, amounts=None):
    """Realized cost per transaction.

    If costs['amount_scaled'] is true, fraud_loss is per-row:
        fraud_loss_i = amounts_i * fraud_loss_rate
    Otherwise it is the constant from costs['fraud_loss'].
    """
    fp = float(costs["false_positive_cost"])
    rc = float(costs["review_cost"])
    rfl = float(costs["residual_fraud_loss"])

    actions = np.asarray(actions)
    y = np.asarray(y)
    fraud = y == 1
    legit = ~fraud
    cost = np.zeros(len(actions), dtype=float)

    if costs.get("amount_scaled", False):
        if amounts is None:
            raise ValueError("amount_scaled=true requires the amounts array")
        rate = float(costs["fraud_loss_rate"])
        fl = np.asarray(amounts, dtype=float) * rate
    else:
        fl = np.full(len(actions), float(costs["fraud_loss"]))

    cost[fraud & (actions == "approve")] = fl[fraud & (actions == "approve")]
    cost[fraud & (actions == "review")] = rc + rfl
    cost[fraud & (actions == "block")] = 0.0

    cost[legit & (actions == "approve")] = 0.0
    cost[legit & (actions == "review")] = rc
    cost[legit & (actions == "block")] = fp
    return cost


def precision_recall_at(df, frac):
    n = len(df)
    k = max(1, int(np.ceil(frac * n)))
    top = df.nlargest(k, "p_fraud")
    n_fraud = df["fraud_bool"].sum()
    prec = float(top["fraud_bool"].mean())
    rec = float(top["fraud_bool"].sum() / max(n_fraud, 1))
    return prec, rec


def main():
    costs = load_costs()
    amount_scaled = bool(costs.get("amount_scaled", False))

    log = pd.read_parquet(ACTION_LOG)
    test = pd.read_parquet(TEST)[["transaction_id", "fraud_bool", "month", "amount_proxy"]]
    df = log.merge(test, on="transaction_id", how="left")
    assert len(df) == len(log), "merge dropped rows"
    assert df["fraud_bool"].notna().all(), "merge produced NaN labels"

    n = len(df)
    y = df["fraud_bool"].to_numpy()
    p = df["p_fraud"].to_numpy()
    amounts = df["amount_proxy"].to_numpy()

    # Censored counts (dataset-wide)
    labeled = pd.read_parquet(LABELED)
    n_total = len(labeled)
    n_cens = int((~labeled["observed"]).sum())
    cens_rate = n_cens / n_total

    # Baselines
    rng = np.random.default_rng(SEED)
    random_actions = rng.choice(RANDOM_ACTIONS, size=n)
    approve_actions = np.full(n, "approve", dtype=object)
    block_actions = np.full(n, "block", dtype=object)
    static_actions = np.where(p >= 0.5, "block", "approve").astype(object)

    scenarios = {
        "Random": random_actions,
        "Approve-all": approve_actions,
        "Block-all": block_actions,
        "Selected classifier + static 0.5": static_actions,
        "Cost-sensitive policy": df["action"].to_numpy(),
    }

    approve_all_total = realized_cost(approve_actions, y, costs, amounts=amounts).sum()

    rows = []
    for name, actions in scenarios.items():
        c = realized_cost(actions, y, costs, amounts=amounts)
        rows.append({
            "Baseline": name,
            "Cost/txn": c.mean(),
            "Total cost": c.sum(),
            "Fraud $ saved vs approve-all": approve_all_total - c.sum(),
        })

    prec1, rec1 = precision_recall_at(df, 0.01)
    prec5, rec5 = precision_recall_at(df, 0.05)
    prec10, rec10 = precision_recall_at(df, 0.10)

    brier = float(np.mean((p - y) ** 2))
    auc = None
    try:
        from sklearn.metrics import roc_auc_score
        auc = float(roc_auc_score(y, p))
    except Exception:
        pass

    action_counts = df["action"].value_counts().to_dict()

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    L = []
    L.append("# Backtest Report")
    L.append("")
    L.append(f"_Generated: {ts}_")
    L.append("")
    L.append("## Setup")
    L.append("")
    L.append("- Dataset: BAF `Base.csv`")
    L.append("- Delay regime: 1 month (`label_month = month + 1`)")
    L.append("- Split: train months {0,1,2}, val {3,4}, test {5,6}")
    L.append("- Model: selected classifier from the 3-algorithm comparison (models/best_model.pkl)")
    L.append("- Policy: `argmin` of expected cost over `{approve, review, block}`")
    L.append(
        f"- Cost matrix: `fraud_loss={costs['fraud_loss']}`, "
        f"`false_positive_cost={costs['false_positive_cost']}`, "
        f"`review_cost={costs['review_cost']}`, "
        f"`residual_fraud_loss={costs['residual_fraud_loss']}`"
    )
    if amount_scaled:
        L.append(
            f"- Amount scaling: **enabled**, "
            f"`fraud_loss(amount) = amount * {costs['fraud_loss_rate']}`"
        )
    else:
        L.append("- Amount scaling: disabled (constant `fraud_loss`)")
    L.append("")
    L.append("## Data Integrity")
    L.append("")
    L.append(f"- Total transactions: {n_total:,}")
    L.append(f"- Censored (`label_month > 7`): {n_cens:,} ({cens_rate:.2%})")
    L.append(f"- Evaluated test rows (observed labels, months 5-6): {n:,}")
    L.append("")
    L.append("## Results")
    L.append("")
    L.append("| Baseline | Cost/txn | Total cost | Fraud $ saved vs approve-all |")
    L.append("|---|---:|---:|---:|")
    for r in rows:
        L.append(
            f"| {r['Baseline']} | {r['Cost/txn']:.6f} | {r['Total cost']:.2f} | "
            f"{r['Fraud $ saved vs approve-all']:.2f} |"
        )
    L.append("")
    L.append("## Ranking metrics (on the policy's scores)")
    L.append("")
    L.append("| Budget | Precision | Recall |")
    L.append("|---|---:|---:|")
    L.append(f"| @1%  | {prec1:.4f} | {rec1:.4f} |")
    L.append(f"| @5%  | {prec5:.4f} | {rec5:.4f} |")
    L.append(f"| @10% | {prec10:.4f} | {rec10:.4f} |")
    L.append("")
    L.append("## Calibration")
    L.append("")
    L.append(f"- Brier score: **{brier:.6f}**")
    if auc is not None:
        L.append(f"- ROC-AUC (informational only): {auc:.4f}")
    L.append("")
    L.append("## Action distribution")
    L.append("")
    for a in ("approve", "review", "block"):
        L.append(f"- `{a}`: {action_counts.get(a, 0):,}")
    L.append("")
    L.append("## Interpretation")
    L.append("")
    policy_cost = next(r["Cost/txn"] for r in rows if r["Baseline"] == "Cost-sensitive policy")
    strongest_baseline = min(
        (r for r in rows if r["Baseline"] != "Cost-sensitive policy"),
        key=lambda r: r["Cost/txn"],
    )
    beat = policy_cost < strongest_baseline["Cost/txn"]
    L.append(
        f"The cost-sensitive policy achieves **{policy_cost:.6f}** cost per transaction. "
        f"The strongest non-policy baseline is **{strongest_baseline['Baseline']}** "
        f"at **{strongest_baseline['Cost/txn']:.6f}**."
    )
    L.append(
        f"**Result:** the policy does {'**not** ' if not beat else ''}beat the strongest baseline "
        f"on realized cost per transaction under the same split, delay regime, and cost matrix."
    )
    L.append("")
    L.append("## Limitations")
    L.append("")
    L.append("- Single delay regime (1 month).")
    if amount_scaled:
        L.append("- Amount-scaled `fraud_loss` uses `amount_proxy = proposed_credit_limit`.")
    else:
        L.append("- Constant `fraud_loss`; amount-scaled sensitivity not enabled in this run.")
    L.append("- BAF is synthetic data; results are not production estimates.")
    L.append("- Censored labels are excluded, not modelled.")
    L.append("- No hyperparameter tuning, no calibration step, no capacity constraint.")
    L.append("")

    OUT.write_text("\n".join(L), encoding="utf-8")
    print(f"[backtest] wrote {OUT}")
    for r in rows:
        print(f"  {r['Baseline']:<28} cost/txn={r['Cost/txn']:.6f}")


if __name__ == "__main__":
    main()