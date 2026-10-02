"""Cross-reference H4 drift results against V1's feature importances.

Answers one question: is the drift on features the V1 classifier
actually relies on, or on marginal features?

Reads:  reports/v2/intermediate/h4_drift.json
        models/feature_importances.json
Writes: reports/v2/intermediate/h4_importance_crossref.json

Run: python -m src.v2.feature_importance_drift
"""
from __future__ import annotations

import json
from pathlib import Path

IN_DRIFT = Path("reports/v2/intermediate/h4_drift.json")
IN_IMP = Path("models/feature_importances.json")
OUT = Path("reports/v2/intermediate/h4_importance_crossref.json")


def main() -> None:
    drift = json.loads(IN_DRIFT.read_text(encoding="utf-8"))
    imp = json.loads(IN_IMP.read_text(encoding="utf-8"))

    imp_by_feat = dict(zip(imp["features"], imp["importances"]))
    total_imp = sum(imp_by_feat.values()) or 1.0

    # Max PSI per feature across all adjacent month pairs.
    max_psi_per_feat: dict[str, float] = {}
    max_psi_pair_per_feat: dict[str, list[int]] = {}
    for pair in drift["pairs"]:
        p = [pair["ref_month"], pair["cmp_month"]]
        for f in pair["features"]:
            if f["psi"] > max_psi_per_feat.get(f["feature"], 0.0):
                max_psi_per_feat[f["feature"]] = f["psi"]
                max_psi_pair_per_feat[f["feature"]] = p

    rows = []
    for feat in drift["features"]:
        imp_val = float(imp_by_feat.get(feat, 0.0))
        imp_share = imp_val / total_imp
        psi = max_psi_per_feat.get(feat, 0.0)
        rows.append({
            "feature": feat,
            "importance": imp_val,
            "importance_share": imp_share,
            "max_psi": psi,
            "max_psi_pair": max_psi_pair_per_feat.get(feat, [None, None]),
            "drifted": psi >= drift["psi_drift_threshold"],
        })

    rows.sort(key=lambda r: r["importance"], reverse=True)

    drifted_imp_share = sum(r["importance_share"] for r in rows if r["drifted"])
    total_imp_share = sum(r["importance_share"] for r in rows)
    top5 = rows[:5]
    top5_drifted = sum(1 for r in top5 if r["drifted"])

    print(f"[crossref] Total features: {len(rows)}")
    print(f"[crossref] Drifted: {sum(1 for r in rows if r['drifted'])}")
    print(f"[crossref] Importance share of drifted features: "
          f"{drifted_imp_share:.4f} of {total_imp_share:.4f} "
          f"({drifted_imp_share / total_imp_share:.2%})")
    print(f"[crossref] Top 5 features: {top5_drifted} of 5 drifted")
    print()
    print(f"{'feature':<35}{'imp_share':>12}{'max_psi':>12}{'drifted':>10}")
    print("-" * 69)
    for r in rows[:15]:
        print(f"{r['feature']:<35}{r['importance_share']:>12.4f}"
              f"{r['max_psi']:>12.4f}{str(r['drifted']):>10}")

    OUT.write_text(
        json.dumps({
            "rows": rows,
            "drifted_importance_share": drifted_imp_share,
            "total_importance_share": total_imp_share,
            "top5_drifted_count": top5_drifted,
        }, indent=2),
        encoding="utf-8",
    )
    print(f"\n[crossref] Wrote {OUT}")


if __name__ == "__main__":
    main()