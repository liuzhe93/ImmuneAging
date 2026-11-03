import bootstrap, json
import numpy as np, pandas as pd, matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
from run_benchmark import R, D, O, SEED

F = bootstrap.FIGURES
F.mkdir(exist_ok=True)
plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 10.5,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "savefig.facecolor": "white",
    }
)
COL = {"aida": "#267D9A", "onek1k": "#C06A31"}
TITLE = {"aida": "AIDA v1", "onek1k": "OneK1K"}
MODELS = [
    "M0_median",
    "M1_composition_EN",
    "M1b_composition_Ridge",
    "M1c_composition_HGB",
]
LABEL = ["Median", "Elastic net", "Ridge", "Gradient boosting"]


def save(fig, name):
    for ext in ["png", "pdf", "svg"]:
        fig.savefig(F / (name + "." + ext), dpi=300, bbox_inches="tight")
    plt.close(fig)


def bootdelta(d):
    rng = np.random.default_rng(SEED)
    b = np.array([np.mean(d[rng.integers(0, len(d), len(d))]) for _ in range(2000)])
    return [np.mean(d), *np.quantile(b, [0.025, 0.975])]


def summary_curve(g, keys):
    return (
        g.assign(error=abs(g.prediction - g.age))
        .groupby(keys, as_index=False)
        .error.mean()
    )


meta = {c: pd.read_csv(D / f"{c}_donors.csv") for c in COL}
elig = pd.concat([pd.read_csv(D / f"{c}_eligibility.csv") for c in COL])
elig.to_csv(O / "figure1_eligibility.csv", index=False)
fig, ax = plt.subplots(2, 2, figsize=(10, 7))
positions = np.arange(5)
for j, c in enumerate(COL):
    e = elig[elig.cohort == c]
    ax[0, 0].bar(
        positions + (j - 0.5) * 0.36,
        e.retained,
        width=0.36,
        color=COL[c],
        label=TITLE[c],
    )
    for x, n in zip(positions + (j - 0.5) * 0.36, e.retained):
        ax[0, 0].text(x, n + 12, str(n), ha="center", fontsize=7)
    m = meta[c]
    ax[0, 1].hist(
        m.loc[m.n_cells >= 500, "age"],
        bins=np.arange(15, 101, 5),
        histtype="step",
        lw=1.8,
        color=COL[c],
        label=TITLE[c],
    )
    for k, sex in enumerate(["female", "male"]):
        n = int(((m.n_cells >= 500) & (m.sex == sex)).sum())
        ax[1, 0].bar(j * 3 + k, n, color=COL[c], alpha=1 if k == 0 else 0.55)
        ax[1, 0].text(j * 3 + k, n + 7, str(n), ha="center", fontsize=8)
    vals = m.n_cells.to_numpy()
    xx = np.sort(vals)
    yy = np.arange(1, len(xx) + 1) / len(xx)
    ax[1, 1].plot(xx, yy, label=TITLE[c], color=COL[c])
ax[0, 0].set(
    xticks=positions,
    xticklabels=["100", "300", "500", "1,000", "3,000"],
    xlabel="Minimum retained atlas cells per donor",
    ylabel="Eligible donors",
    ylim=(0, 1120),
    title="A  Coverage changes sharply at 3,000 cells",
)
ax[0, 0].legend(frameon=False, fontsize=8)
ax[0, 1].set(
    xlabel="Age (years)", ylabel="Donors", title="B  Primary cohort age distributions"
)
ax[0, 1].legend(frameon=False, fontsize=8)
ax[1, 0].set(
    xticks=[0, 1, 3, 4],
    xticklabels=["AIDA\nfemale", "AIDA\nmale", "OneK1K\nfemale", "OneK1K\nmale"],
    ylabel="Donors",
    title="C  Primary cohort sex composition",
)
ax[1, 1].set(
    xscale="log",
    xlabel="Retained cells per donor",
    ylabel="Cumulative fraction of donors",
    title="D  Atlas cellular coverage",
)
ax[1, 1].axvline(500, color="grey", ls="--", lw=1)
fig.tight_layout()
save(fig, "Figure_1_cohort_coverage")
metrics = pd.read_csv(O / "metrics.csv")
main = metrics[(metrics.n_cells == 500) & (metrics.age_scope == "all")]
pred = pd.read_csv(O / "predictions_composition_500.csv")
oof = pred[pred.evaluation == "OOF"]
fig, ax = plt.subplots(2, 3, figsize=(11, 7))
for row, c in enumerate(COL):
    mm = (
        main[(main.evaluation == "OOF") & (main.test_cohort == c)]
        .set_index("model")
        .loc[MODELS]
    )
    ax[row, 0].errorbar(
        mm.MAE,
        np.arange(4),
        xerr=np.array([mm.MAE - mm.MAE_low, mm.MAE_high - mm.MAE]),
        fmt="o",
        color=COL[c],
        capsize=3,
    )
    ax[row, 0].set(
        yticks=np.arange(4),
        yticklabels=LABEL,
        xlabel="MAE (years)",
        title=TITLE[c] + "  OOF accuracy",
    )
    ax[row, 0].invert_yaxis()
    p = oof[(oof.cohort == c) & (oof.model == "M1_composition_EN")]
    ax[row, 1].scatter(p.age, p.prediction, s=8, alpha=0.35, color=COL[c])
    ax[row, 1].plot([15, 100], [15, 100], color="grey", ls="--")
    ax[row, 1].set(
        xlabel="Observed age",
        ylabel="Predicted age",
        title="Elastic net  donor predictions",
        xlim=(15, 100),
        ylim=(15, 100),
    )
    q = (
        p.assign(bin=pd.qcut(p.prediction, 10, duplicates="drop"))
        .groupby("bin", observed=True)
        .agg(pred=("prediction", "mean"), age=("age", "mean"), n=("age", "size"))
    )
    ax[row, 2].plot(q.pred, q.age, "o-", color=COL[c])
    ax[row, 2].plot([15, 100], [15, 100], color="grey", ls="--")
    ax[row, 2].set(
        xlabel="Mean predicted age in decile",
        ylabel="Mean observed age in decile",
        title="Age agreement",
        xlim=(15, 100),
        ylim=(15, 100),
    )
fig.tight_layout()
save(fig, "Figure_2_matched_prediction")
res = pd.read_csv(O / "resource_repeats.csv")
res["search_fit_s"] = res.search_s + res.fit_s
fig, axs = plt.subplots(2, 2, figsize=(10, 7))
ax = axs.ravel()
colors = ["#267D9A", "#718048", "#C06A31"]
for j, name in enumerate(MODELS[1:]):
    for c in COL:
        z = res[(res.model == name) & (res.cohort == c)]
        q = z.groupby("training_donors").search_fit_s.agg(["median", "min", "max"])
        ax[0].plot(
            q.index,
            q["median"],
            marker="o",
            color=colors[j],
            ls="-" if c == "aida" else "--",
            label=LABEL[j + 1] + (" AIDA" if c == "aida" else " OneK1K"),
        )
        z = z[z.training_donors == z.training_donors.max()]
        ax[1].scatter(
            z.search_fit_s.median(),
            z.MAE.median(),
            color=colors[j],
            marker="o" if c == "aida" else "^",
            s=55,
        )
        None
        ax[2].scatter(
            z.predict_s.median() * 1000,
            z.peak_process_RSS_MiB.median(),
            color=colors[j],
            marker="o" if c == "aida" else "^",
            s=55,
        )
ax[0].set(
    xlabel="Training donors",
    ylabel="Inner search + final fit (seconds)",
    yscale="log",
    title="A  Measured warm model-stage time",
)
ax[0].legend(frameon=False, fontsize=8)
ax[1].set(
    xlabel="Search + fit (seconds; log scale)",
    ylabel="Fixed-holdout MAE (years)",
    xscale="log",
    title="B  Accuracy and measured fitting cost",
)
ax[2].set(
    xlabel="Batch prediction time (milliseconds)",
    ylabel="Peak process RSS (MiB)",
    title="C  Process memory and prediction time",
)
for j, name in enumerate(MODELS[1:]):
    for k, c in enumerate(COL):
        z = res[(res.model == name) & (res.cohort == c)]
        z = z[z.training_donors == z.training_donors.max()]
        x = j * 3 + k
        for h, field in enumerate(["search_s", "fit_s", "predict_s"]):
            ax[3].bar(
                x + (h - 1) * 0.22,
                z[field].median(),
                width=0.22,
                color=["#267D9A", "#718048", "#C06A31"][h],
                label=["Search", "Fit", "Prediction"][h] if x == 0 else None,
            )
ax[3].set(
    xticks=[0, 1, 3, 4, 6, 7],
    xticklabels=["EN A", "EN O", "Ridge A", "Ridge O", "HGB A", "HGB O"],
    ylabel="Stage time (seconds)",
    yscale="log",
    title="D  Stages at largest training size",
)
ax[3].tick_params(axis="x", labelsize=8)
ax[3].legend(frameon=False, fontsize=8)
fig.tight_layout()
save(fig, "Figure_4_measured_cost")
cells = pd.read_csv(O / "matched_cell_predictions.csv")
learn = pd.read_csv(O / "learning_predictions.csv")
fig, ax = plt.subplots(2, 2, figsize=(10, 7))
curve = []
for j, c in enumerate(COL):
    for row, source, key in [(0, cells, "n_cells"), (1, learn, "training_donors")]:
        q = summary_curve(source[source.cohort == c], [key, "replicate"])
        z = q.groupby(key).error.agg(["mean", "min", "max"])
        ax[row, j].plot(z.index, z["mean"], "o-", color=COL[c])
        ax[row, j].fill_between(z.index, z["min"], z["max"], color=COL[c], alpha=0.15)
        ax[row, j].set(
            xlabel="Cells per donor" if row == 0 else "Training donors",
            ylabel="MAE (years)",
            title=TITLE[c]
            + ("  fixed donors and folds" if row == 0 else "  fixed 20% holdout"),
        )
        curve += [
            {
                "cohort": c,
                "experiment": "cell_depth" if row == 0 else "donor_learning",
                "x": int(k),
                "mean_MAE": v["mean"],
                "min_repeat": v["min"],
                "max_repeat": v["max"],
            }
            for k, v in z.iterrows()
        ]
pd.DataFrame(curve).to_csv(O / "learning_curve_summary.csv", index=False)
fig.tight_layout()
save(fig, "Figure_5_low_resource")
delta = pd.read_csv(O / "deposited_paired_differences.csv")
abl = pd.read_csv(O / "ablation_predictions.csv")
abl_summary = []
for (c, removed), z in abl.groupby(["cohort", "removed"]):
    base = oof[(oof.cohort == c) & (oof.model == "M1_composition_EN")][
        ["donor_id", "age", "prediction"]
    ]
    z = z.merge(base, on="donor_id", suffixes=("", "_base"), validate="one_to_one")
    diff = abs(z.prediction - z.age) - abs(z.prediction_base - z.age)
    v = bootdelta(diff.to_numpy())
    abl_summary.append(
        {
            "cohort": c,
            "removed": removed,
            "n": len(z),
            "delta_MAE": v[0],
            "low": v[1],
            "high": v[2],
        }
    )
ab = pd.DataFrame(abl_summary)
ab.to_csv(O / "ablation_summary.csv", index=False)
coarse = pd.read_csv(O / "T_collapsed_comparison.csv").rename(
    columns={"cohort": "cohort"}
)
coarse["removed"] = "T_subsets_merged"
ab = pd.concat(
    [ab, coarse[["cohort", "removed", "n", "delta_MAE", "low", "high"]]],
    ignore_index=True,
)
# Paired model differences, used instead of inferring significance from separate CIs.
paired = []
for c in COL:
    base = oof[(oof.cohort == c) & (oof.model == "M1_composition_EN")]
    for name in [MODELS[2], MODELS[3]]:
        z = oof[(oof.cohort == c) & (oof.model == name)].merge(
            base, on="donor_id", suffixes=("", "_base"), validate="one_to_one"
        )
        v = bootdelta(
            (abs(z.prediction - z.age) - abs(z.prediction_base - z.age)).to_numpy()
        )
        paired.append(
            {
                "cohort": c,
                "comparison": name + "_minus_EN",
                "n": len(z),
                "delta_MAE": v[0],
                "low": v[1],
                "high": v[2],
            }
        )
pd.DataFrame(paired).to_csv(O / "paired_model_differences.csv", index=False)
print("Created baseline quantitative figures and source tables", flush=True)
