"""Derive cohort descriptions and model-stage resource summaries."""

import bootstrap, json, platform, sys
import pandas as pd, importlib.metadata as metadata

D = bootstrap.DATA / "processed"
O = bootstrap.RESULTS
records = []
for c in ["aida", "onek1k"]:
    m = pd.read_csv(D / f"{c}_donors.csv")
    for n in [300, 500, 1000]:
        for status, mask in [("included", m.n_cells >= n), ("excluded", m.n_cells < n)]:
            z = m[mask]
            records.append(
                {
                    "cohort": c,
                    "threshold": n,
                    "status": status,
                    "n": len(z),
                    "mean_age": z.age.mean(),
                    "median_age": z.age.median(),
                    "min_age": z.age.min(),
                    "max_age": z.age.max(),
                    "female_n": (z.sex == "female").sum(),
                    "male_n": (z.sex == "male").sum(),
                }
            )
pd.DataFrame(records).to_csv(O / "selection_demographics.csv", index=False)
r = pd.read_csv(O / "resource_repeats.csv")
out = []
for keys, g in r.groupby(["cohort", "model", "training_donors"]):
    z = dict(zip(["cohort", "model", "training_donors"], keys))
    z["repeats"] = len(g)
    for field in [
        "search_s",
        "fit_s",
        "predict_s",
        "peak_process_RSS_MiB",
        "baseline_RSS_MiB",
        "MAE",
    ]:
        for suffix, value in [
            ("median", g[field].median()),
            ("q25", g[field].quantile(0.25)),
            ("q75", g[field].quantile(0.75)),
        ]:
            z[field + "_" + suffix] = value
    out.append(z)
pd.DataFrame(out).to_csv(O / "resource_summary.csv", index=False)
versions = {
    p: metadata.version(p)
    for p in [
        "numpy",
        "scipy",
        "scikit-learn",
        "h5py",
        "psutil",
        "matplotlib",
        "pandas",
        "reportlab",
        "lxml",
    ]
}
(O / "package_versions.json").write_text(json.dumps(versions, indent=2))
print("Cohort descriptions and newly measured resource summaries saved", flush=True)
