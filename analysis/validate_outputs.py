"""Check result coverage and compare deterministic summaries with publication fixtures."""

import bootstrap, json
import numpy as np, pandas as pd
from pathlib import Path

R = bootstrap.ROOT
O = bootstrap.RESULTS
S = bootstrap.OUT / "results/sensitivity"
report = []


def compare(label, current, expected, keys, values, tolerance=1e-7):
    a = pd.read_csv(current)
    b = pd.read_csv(expected)
    z = a.merge(b, on=keys, suffixes=("_new", "_expected"), validate="one_to_one")
    if len(z) != len(a) or len(z) != len(b):
        raise ValueError("Row count mismatch: " + label)
    errors = {}
    for col in values:
        x = z[col + "_new"].to_numpy(float)
        y = z[col + "_expected"].to_numpy(float)
        if not np.array_equal(np.isnan(x), np.isnan(y)):
            raise ValueError("Missing-value mismatch: " + label + " " + col)
        difference = float(np.nanmax(abs(x - y))) if np.isfinite(x - y).any() else 0.0
        if difference > tolerance:
            raise ValueError(
                f"{label} {col}: maximum difference {difference} exceeds {tolerance}"
            )
        errors[col] = difference
    report.append(
        {
            "result": label,
            "rows": len(z),
            "maximum_absolute_differences": errors,
            "tolerance": tolerance,
        }
    )


compare(
    "All thresholds and models",
    O / "metrics.csv",
    R / "validation/expected_metrics.csv",
    [
        "condition",
        "n_cells",
        "evaluation",
        "train_cohort",
        "test_cohort",
        "model",
        "age_scope",
    ],
    ["n", "MAE", "MAE_low", "MAE_high", "RMSE", "R2", "bias_pred_minus_age"],
)
compare(
    "Fixed-donor depth and donor learning curves",
    O / "learning_curve_summary.csv",
    R / "validation/expected_learning_curve_summary.csv",
    ["cohort", "experiment", "x"],
    ["mean_MAE", "min_repeat", "max_repeat"],
)
compare(
    "Released prediction lineages",
    O / "deposited_metrics.csv",
    R / "validation/expected_deposited_metrics.csv",
    ["cohort", "lineage", "input"],
    ["n", "MAE", "MAE_low", "MAE_high", "RMSE", "R2"],
)
compare(
    "Released paired error differences",
    O / "deposited_paired_differences.csv",
    R / "validation/expected_deposited_paired_differences.csv",
    ["cohort", "lineage", "comparison"],
    ["n", "delta_MAE", "low", "high"],
)
compare(
    "Shared labels and source ages",
    S / "age_standardised_metrics.csv",
    R / "validation/expected_age_standardised_metrics.csv",
    [
        "representation",
        "training_age",
        "scheme",
        "evaluation",
        "train_cohort",
        "test_cohort",
        "model",
    ],
    [
        "n",
        "ESS",
        "min_weight",
        "max_weight",
        "weighted_MAE",
        "low",
        "high",
        "weighted_bias",
    ],
)
compare(
    "Paired weighted transfer",
    S / "paired_transfer.csv",
    R / "validation/expected_paired_transfer.csv",
    ["representation", "training_age", "scheme", "test_cohort", "model"],
    ["delta_external_minus_internal", "low", "high"],
)
artifacts = []
for folder, prefix, n in [("main", "Figure_", 6), ("supplementary", "Figure_S", 8)]:
    for i in range(1, n + 1):
        for suffix in ["png", "pdf", "svg"]:
            p = list(
                (bootstrap.OUT / "figures" / folder).glob(f"{prefix}{i}_*.{suffix}")
            )
            if len(p) != 1 or p[0].stat().st_size < 1000:
                raise ValueError(f"Missing/ambiguous figure {folder} {i} {suffix}")
            artifacts.append(str(p[0].relative_to(bootstrap.OUT)))
for i in [str(i) for i in range(1, 7)] + ["S" + str(i) for i in range(1, 20)]:
    matches = list((bootstrap.OUT / "tables").glob("Table_" + i + ".csv")) + list(
        (bootstrap.OUT / "tables").glob("Table_" + i + "_*.csv")
    )
    if not matches:
        raise ValueError("Missing table " + i)
submission = bootstrap.OUT / "submission_tables"
for stem in ["S1", "S2", "S3A", "S3B", "S4", "S5", "S6", "S7"]:
    matches = list(submission.glob(f"Table_{stem}_*.csv"))
    if len(matches) != 1 or pd.read_csv(matches[0]).empty:
        raise ValueError(f"Missing or ambiguous submission table {stem}")
report = {
    "all_passed": True,
    "comparisons": report,
    "figure_files": artifacts,
    "resource_measurements": "Measured afresh on the executing machine; elapsed time and memory are not expected to equal the publication hardware.",
    "validation_fixtures": "Aggregate reference summaries are used only at this final check, never for fitting or plotting.",
}
(bootstrap.OUT / "logs/reproduction_acceptance.json").write_text(
    json.dumps(report, indent=2)
)
print(
    "Publication summaries, 42 figure files and all table numbers verified", flush=True
)
