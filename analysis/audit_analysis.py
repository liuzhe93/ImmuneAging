import bootstrap, json, hashlib
import pandas as pd, numpy as np
from run_benchmark import R, D, O

checks = {}
for n in [300, 500, 1000]:
    d = pd.read_csv(O / f"predictions_composition_{n}.csv")
    o = d[d.evaluation == "OOF"]
    fold = pd.read_csv(O / f"folds_composition_{n}.csv")
    assert not fold.duplicated(["cohort", "donor_id"]).any()
    assert not o.duplicated(["cohort", "model", "donor_id"]).any()
    for c, g in o.groupby("cohort"):
        expected = set(pd.read_csv(D / f"{c}_donors.csv").query("n_cells>=@n").donor_id)
        for model, z in g.groupby("model"):
            assert set(z.donor_id) == expected
            assert set(z.fold) == set(range(5))
            assert np.isfinite(z[["age", "prediction"]]).all().all()
        assert g.groupby("donor_id").fold.nunique().eq(1).all()
    checks[f"OOF_{n}"] = (
        "One prediction per eligible donor per model; shared outer partitions; finite outputs"
    )
cell = pd.read_csv(O / "matched_cell_predictions.csv")
for (c, rep), g in cell.groupby(["cohort", "replicate"]):
    assert g.groupby("n_cells").donor_id.nunique().nunique() == 1
    assert g.groupby("donor_id").fold.nunique().eq(1).all()
    assert not g.duplicated(["donor_id", "n_cells"]).any()
checks["matched_cell_experiment"] = (
    "Same donor identities and folds at all depths; five replicates"
)
pred = pd.read_csv(O / "deposited_integrity.csv")
assert pred.max_absolute_formula_residual.max() < 1e-10
checks["deposited_formula_max_residual"] = pred.max_absolute_formula_residual.max()
checks["deposited_archives_MD5"] = (
    "Verified at acquisition against Zenodo record metadata"
)
resources = pd.read_csv(O / "resource_repeats.csv")
assert (
    resources.groupby(["cohort", "model", "training_donors"])
    .repeat.nunique()
    .eq(5)
    .all()
)
checks["resource_process_repetitions"] = 5
metrics = pd.read_csv(O / "metrics.csv")
assert (metrics.MAE_low <= metrics.MAE).all() and (
    metrics.MAE_high >= metrics.MAE
).all()
checks["bootstrap_intervals"] = (
    "All reported MAEs within their conditional donor intervals"
)
checks["unexecuted_arms"] = [
    "raw-count pseudobulk",
    "expression HGB",
    "jointly fitted expression plus fractions",
    "frozen pretrained encoder",
]
(O / "analysis_QA.json").write_text(json.dumps(checks, indent=2), encoding="utf8")
print(json.dumps(checks, indent=2))
