"""Export main and supplementary CSV tables from computed results and cited inputs."""

import bootstrap, csv, json, shutil
import pandas as pd

R = bootstrap.ROOT
O = bootstrap.RESULTS
S = bootstrap.OUT / "results/sensitivity"
T = bootstrap.OUT / "tables"
T.mkdir(exist_ok=True)
for i in [1, 2, 3, 4, 6]:
    shutil.copy2(R / f"inputs/literature/Table_{i}.csv", T / f"Table_{i}.csv")
m = pd.read_csv(O / "metrics.csv")
z = m[(m.n_cells == 500) & (m.age_scope == "all")]
rows = []
for model, label in [
    ("M0_median", "Median reference"),
    ("M1_composition_EN", "Elastic net"),
    ("M1b_composition_Ridge", "Ridge"),
    ("M1c_composition_HGB", "Gradient boosting"),
]:

    def cell(ev, src, dst):
        a = z[
            (z.model == model)
            & (z.evaluation == ev)
            & (z.train_cohort == src)
            & (z.test_cohort == dst)
        ].iloc[0]
        return f"{a.MAE:.2f} ({a.MAE_low:.2f}–{a.MAE_high:.2f})"

    rows.append(
        [
            label,
            cell("OOF", "aida", "aida"),
            cell("OOF", "onek1k", "onek1k"),
            "AIDA→OneK1K "
            + cell("external", "aida", "onek1k")
            + "; OneK1K→AIDA "
            + cell("external", "onek1k", "aida"),
        ]
    )
with (T / "Table_5.csv").open("w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["Model", "AIDA OOF MAE", "OneK1K OOF MAE", "Frozen external MAE"])
    w.writerows(rows)
shutil.copy2(
    R / "inputs/literature/Table_S1_resources.csv", T / "Table_S1_resources.csv"
)
a = m[m.age_scope == "all"].copy()
a["interpretation"] = (
    "Eligibility thresholds change donor populations; not a paired cell-depth comparison"
)
a.to_csv(T / "Table_S2_threshold_sensitivity.csv", index=False)
alias = {
    3: "deposited_metrics.csv",
    4: "deposited_paired_differences.csv",
    5: "resource_summary.csv",
    6: "selection_demographics.csv",
    7: "composition_distribution.csv",
    8: "composition_standardised.csv",
    9: "age_standardised_metrics.csv",
    10: "age_stratified_bootstrap.csv",
    11: "T_collapsed_comparison.csv",
    12: "Table_S12_repertoire_evidence.csv",
}
for number, name in alias.items():
    shutil.copy2(O / name, T / f"Table_S{number}.csv")
status = json.loads(
    (R / "inputs/literature/execution_status.json").read_text(encoding="utf8")
)
with (T / "Table_S13_execution_status.csv").open(
    "w", newline="", encoding="utf-8-sig"
) as f:
    w = csv.writer(f)
    w.writerow(status["headers"])
    w.writerows(status["rows"])
shutil.copy2(
    S / "mapping/complete_label_mapping.csv", T / "Table_S14_complete_label_mapping.csv"
)
shutil.copy2(
    S / "mapping/mapping_reconstruction_checks.csv",
    T / "Table_S14_reconstruction_checks.csv",
)
a = pd.read_csv(S / "age_standardised_metrics.csv")
a[
    (a.model == "M1_composition_EN")
    & (a.training_age == "all")
    & (a.scheme == "five_year")
].to_csv(T / "Table_S15_shared_annotation.csv", index=False)
b = pd.read_csv(S / "paired_transfer.csv")
b[(b.model == "M1_composition_EN") & (b.representation != "coarse6")].to_csv(
    T / "Table_S16_source_age_and_bands.csv", index=False
)
a[(a.model == "M0_median") & (a.representation == "fine17")].to_csv(
    T / "Table_S17_source_medians_and_weights.csv", index=False
)
shutil.copy2(S / "age_weights.csv", T / "Table_S17_band_counts_and_weights.csv")
shutil.copy2(S / "T_controls/T_control_summary.csv", T / "Table_S18_T_controls.csv")
shutil.copy2(
    S / "T_controls/T_fold_parameters.json", T / "Table_S18_fold_parameters.json"
)
report = json.loads((S / "acceptance_report.json").read_text())
pd.DataFrame([report]).to_csv(T / "Table_S19_replay_acceptance.csv", index=False)
index = []
for p in sorted(T.glob("Table_*.csv")):
    n = p.name.split("_")[1]
    curated = n in ["1", "2", "3", "4", "6", "S1", "S13"]
    index.append(
        {
            "file": p.name,
            "origin": (
                "Cited literature or study-status input"
                if curated
                else "Computed from this run"
            ),
            "path": str(p.relative_to(bootstrap.OUT)),
        }
    )
pd.DataFrame(index).to_csv(T / "table_manifest.csv", index=False)
print("Main tables 1–6 and supplementary tables S1–S19 exported", flush=True)
