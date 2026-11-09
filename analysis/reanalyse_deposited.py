"""Reanalyse author predictions, without asserting reproduction of training.
Paper DOI 10.1038/s42003-024-07094-5; Zenodo 10405106.
"""

import bootstrap, json
import numpy as np, pandas as pd
from run_benchmark import R, D, O, SEED, metrics

P = bootstrap.DATA / "deposited"
rows = []
checks = []
for c, label in [("aida", "AIDA"), ("onek1k", "eQTL")]:
    meta = pd.read_csv(D / f"{c}_donors.csv").set_index("donor_id")
    cp = P / (
        "predictions_cell_type_proportion_AIDA.csv"
        if c == "aida"
        else "eQTL_predictions_cell_type_proportion.csv"
    )
    prop = pd.read_csv(cp).rename(columns={"donor": "donor_id"})
    multiplicity = prop.groupby("donor_id").size()
    expected = 1 if c == "aida" else 5
    if not (multiplicity == expected).all():
        raise ValueError("Unexpected ensemble multiplicity")
    if not (prop.groupby("donor_id").age.nunique() == 1).all():
        raise ValueError("Age conflict")
    prop = prop.groupby("donor_id").agg(
        age=("age", "first"), proportion=("predicted_age", "mean")
    )
    for path in sorted((P / f"sc_predictions_{label}").glob("*.csv")):
        lineage = path.stem
        sc = pd.read_csv(path).rename(columns={"donor": "donor_id"})
        combo = pd.read_csv(P / f"combined_predictions_{label}" / path.name).rename(
            columns={"donor": "donor_id", "predicted_age": "combined"}
        )
        if not (sc.groupby("donor_id").age.nunique() == 1).all():
            raise ValueError("Inconsistent expression age")
        expr = sc.groupby("donor_id").agg(
            expression=("predicted_age", "mean"),
            n_prediction_rows=("predicted_age", "size"),
        )
        expr["n_cells"] = expr.n_prediction_rows / expected
        merged = prop.join(expr, how="inner").join(
            combo.set_index("donor_id")[["combined", "age"]].rename(
                columns={"age": "combined_age"}
            ),
            how="inner",
        )
        if not np.allclose(merged.age, merged.combined_age):
            raise ValueError("Combined age mismatch")
        err = np.max(
            np.abs(merged.combined - (merged.expression + merged.proportion) / 2)
        )
        checks.append(
            {
                "cohort": c,
                "lineage": lineage,
                "max_absolute_formula_residual": err,
                "ensemble_models": expected,
                "n_merged": len(merged),
            }
        )
        # Formula mismatch can arise from released ensemble aggregation. Never repair it silently.
        merged = merged.join(
            meta[["age", "n_cells"]].rename(
                columns={"age": "metadata_age", "n_cells": "total_cells"}
            ),
            how="inner",
        )
        if not np.allclose(merged.age, merged.metadata_age):
            raise ValueError("Metadata age mismatch")
        merged = merged.loc[(merged.total_cells >= 500) & (merged.n_cells >= 10)]
        for donor, z in merged.iterrows():
            rows.append(
                {
                    "cohort": c,
                    "donor_id": donor,
                    "lineage": lineage,
                    "age": z.age,
                    "proportion": z.proportion,
                    "expression": z.expression,
                    "combined": z.combined,
                    "lineage_cells": z.n_cells,
                    "total_cells": z.total_cells,
                    "evaluation": (
                        "author_OOF" if c == "aida" else "author_external_5model_mean"
                    ),
                    "formula_residual": err,
                }
            )
out = pd.DataFrame(rows)
out.to_csv(O / "deposited_paired_predictions.csv", index=False)
pd.DataFrame(checks).to_csv(O / "deposited_integrity.csv", index=False)
summary = []
for (c, lineage), g in out.groupby(["cohort", "lineage"]):
    if len(g) < 30:
        continue
    base = {
        "cohort": c,
        "lineage": lineage,
        "n": len(g),
        "age_min": g.age.min(),
        "age_max": g.age.max(),
    }
    for name in ["proportion", "expression", "combined"]:
        mm = metrics(g.rename(columns={name: "prediction"}))
        summary.append({**base, "input": name, **mm})
pd.DataFrame(summary).to_csv(O / "deposited_metrics.csv", index=False)
paired = []
for (c, lineage), g in out.groupby(["cohort", "lineage"]):
    if len(g) < 30:
        continue
    for name in ["expression", "combined"]:
        delta = (g[name] - g.age).abs().to_numpy() - (
            g.proportion - g.age
        ).abs().to_numpy()
        rng = np.random.default_rng(SEED)
        boot = np.array(
            [delta[rng.integers(0, len(delta), len(delta))].mean() for _ in range(2000)]
        )
        paired.append(
            {
                "cohort": c,
                "lineage": lineage,
                "comparison": name + "_minus_proportion",
                "n": len(g),
                "delta_MAE": delta.mean(),
                "low": np.quantile(boot, 0.025),
                "high": np.quantile(boot, 0.975),
            }
        )
pd.DataFrame(paired).to_csv(O / "deposited_paired_differences.csv", index=False)
print(
    "Author-prediction reanalysis",
    len(out),
    "donor-lineage rows; maximum formula residual",
    max(z["max_absolute_formula_residual"] for z in checks),
    flush=True,
)
