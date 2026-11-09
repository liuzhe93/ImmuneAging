"""Refit shared cell categories, source age restrictions and T-cell controls."""

import bootstrap, json, sys

sys.path.insert(0, str(bootstrap.ROOT / "src"))
from immune_ageing.core import *
from immune_ageing.audits import audit_mapping, T_controls
from threadpoolctl import threadpool_limits

out = bootstrap.OUT / "results" / "sensitivity"
out.mkdir(parents=True, exist_ok=True)
D = bootstrap.DATA / "processed"
frames = []
with threadpool_limits(limits=1):
    audit_mapping(D, bootstrap.EVIDENCE, out / "mapping")
    for representation, ages in [
        ("fine17", "all"),
        ("coarse5", "all"),
        ("coarse6", "all"),
        ("fine17", "common"),
        ("coarse5", "common"),
    ]:
        frames.append(run_models(D, out, representation, ages, 2000))
    allpred = pd.concat(frames, ignore_index=True)
    allpred.to_csv(out / "all_predictions.csv", index=False)
    summarise(allpred, 2000).to_csv(out / "all_metrics.csv", index=False)
    age_standardise(allpred, out, 2000)
    T_controls(D, out / "T_controls", frames[0], 2000)
old = pd.read_csv(bootstrap.RESULTS / "predictions_composition_500.csv")
new = frames[0].merge(
    old,
    on=["evaluation", "train_cohort", "test_cohort", "model", "donor_id"],
    suffixes=("_new", "_baseline"),
    validate="one_to_one",
)
if len(new) != len(old) or len(new) != len(frames[0]):
    raise ValueError("Prediction comparison does not cover both complete inputs")
delta = float(abs(new.prediction_new - new.prediction_baseline).max())
assert delta < 1e-8
(out / "acceptance_report.json").write_text(
    json.dumps(
        {
            "implementation": "Separate implementations within the same project",
            "primary_predictions_checked": len(new),
            "maximum_prediction_difference": delta,
            "tolerance": 1e-8,
            "seed": SEED,
            "bootstrap_resamples": 2000,
        },
        indent=2,
    )
)
