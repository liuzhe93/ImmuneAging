import bootstrap, json, hashlib
from pathlib import Path
import numpy as np, pandas as pd, matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from run_benchmark import O, SEED

R = Path(__file__).resolve().parent
F = bootstrap.location("supplementary_root", "supplementary")
F.mkdir(exist_ok=True)
plt.rcParams.update(
    {
        "font.size": 10,
        "font.family": "DejaVu Sans",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
    }
)
colors = {"aida": "#267D9A", "onek1k": "#C06A31"}


def save(fig, name):
    for ext in ["png", "svg", "pdf"]:
        fig.savefig(F / (name + "." + ext), bbox_inches="tight", dpi=300)
    plt.close(fig)


d = pd.read_csv(O / "composition_distribution.csv")
std = pd.read_csv(O / "composition_standardised.csv")
features = sorted(d.feature.unique())
fig, ax = plt.subplots(1, 2, figsize=(10, 7))
for k, c in enumerate(colors):
    z = d[d.cohort == c].set_index("feature").loc[features]
    yy = np.arange(len(z)) + (k - 0.5) * 0.18
    ax[0].errorbar(
        z["median"] * 100,
        yy,
        xerr=np.array([z["median"] - z.q25, z.q75 - z["median"]]) * 100,
        fmt="o",
        ms=4,
        color=colors[c],
        label=c,
    )
    z = std[std.cohort == c].set_index("feature").loc[features]
    ax[1].plot(z.standardised_mean_fraction * 100, yy, "o", color=colors[c], label=c)
for j, a in enumerate(ax):
    a.set(
        yticks=np.arange(len(features)),
        yticklabels=features,
        xlabel="Fraction (%)",
        title=[
            "A  Raw median and interquartile range",
            "B  Age-band standardized mean",
        ][j],
    )
    a.legend(frameon=False)
fig.tight_layout()
save(fig, "Figure_S5_compartment_distributions")
fig, ax = plt.subplots(figsize=(7, 7))
for k, c in enumerate(colors):
    z = std[std.cohort == c].set_index("feature").loc[features]
    ax.plot(
        z.common_age_spearman_rho,
        np.arange(len(z)) + (k - 0.5) * 0.18,
        "o",
        color=colors[c],
        label=c,
    )
ax.axvline(0, color="grey", ls="--")
ax.set(
    yticks=np.arange(len(features)),
    yticklabels=features,
    xlabel="Spearman correlation with age",
    title="Ages 19–75 within each cohort",
    xlim=(-0.8, 0.5),
)
ax.legend(frameon=False)
fig.tight_layout()
save(fig, "Figure_S6_age_fraction_associations")
pred = pd.read_csv(O / "predictions_composition_500.csv")
bins = [19, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 76]
labels = [f"{a}-{b-1}" for a, b in zip(bins[:-1], bins[1:])]
centres = [(a + b - 1) / 2 for a, b in zip(bins[:-1], bins[1:])]
fig, ax = plt.subplots(2, 2, figsize=(10, 7))
records = []
for row, c in enumerate(colors):
    z = pred[
        (pred.evaluation == "external")
        & (pred.test_cohort == c)
        & (pred.model == "M1_composition_EN")
    ].copy()
    z["band"] = pd.cut(z.age, bins, right=False, labels=labels)
    for k, band in enumerate(labels):
        q = z[z.band == band]
        e = (q.prediction - q.age).to_numpy()
        rng = np.random.default_rng(SEED)
        bm = []
        bb = []
        for rep in range(2000):
            ix = rng.integers(0, len(q), len(q))
            bm.append(abs(e[ix]).mean())
            bb.append(e[ix].mean())
        for col, val, bs in [(0, abs(e).mean(), bm), (1, e.mean(), bb)]:
            lo, hi = np.quantile(bs, [0.025, 0.975])
            ax[row, col].errorbar(
                centres[k],
                val,
                yerr=[[val - lo], [hi - val]],
                fmt="o",
                color=colors[c],
                capsize=2,
            )
        records.append(
            {
                "test_cohort": c,
                "age_band": band,
                "n": len(q),
                "MAE": abs(e).mean(),
                "MAE_low": np.quantile(bm, 0.025),
                "MAE_high": np.quantile(bm, 0.975),
                "prediction_minus_observed_bias": e.mean(),
                "bias_low": np.quantile(bb, 0.025),
                "bias_high": np.quantile(bb, 0.975),
            }
        )
    for col in range(2):
        ax[row, col].set(
            title=c + " frozen external elastic net",
            xlabel="Age band midpoint (years)",
            ylabel="MAE (years)" if col == 0 else "Predicted minus observed age",
        )
        ax[row, 1].axhline(0, color="grey", ls="--")
fig.tight_layout()
save(fig, "Figure_S7_age_stratified_external_errors")
pd.DataFrame(records).to_csv(O / "age_stratified_bootstrap.csv", index=False)
from lxml import etree

source = bootstrap.location("repertoire_source", "evidence_review/repertoire.xml")
tree = etree.parse(str(source))
ledger = []
for i, p in enumerate(tree.xpath("//p"), 1):
    text = " ".join("".join(p.itertext()).split())
    if "MAE) values were compared" in text or "LightGBM model performed best" in text:
        ledger.append(
            {
                "doi": "10.1111/acel.70580",
                "source_file": "repertoire.xml",
                "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "paragraph_number": i,
                "xml_xpath": tree.getpath(p),
                "section": " > ".join(p.xpath("ancestor::sec/title/text()")),
                "reported_fact": "Nine algorithms compared on the CMUCH external test set; best algorithm selected for the final clock.",
                "interpretation": "The CMUCH results informed algorithm selection, so this is a model-selection holdout rather than an untouched final evaluation for the selected algorithm.",
                "short_quote": (
                    "values were compared within an external test set"
                    if len(ledger) == 0
                    else ""
                ),
                "note": "Explicitly described by the authors; evaluation interpretation is ours.",
            }
        )
pd.DataFrame(ledger).to_csv(O / "Table_S12_repertoire_evidence.csv", index=False)
for src, dst in [
    ("composition_distribution.csv", "Table_S7_compartment_distributions.csv"),
    (
        "composition_standardised.csv",
        "Table_S8_age_associations_and_standardised_fractions.csv",
    ),
    ("age_standardised_metrics.csv", "Table_S9_age_standardised_metrics.csv"),
    ("age_stratified_bootstrap.csv", "Table_S10_age_stratified_errors.csv"),
    ("T_collapsed_comparison.csv", "Table_S11_T_resolution_control.csv"),
]:
    (O / dst).write_bytes((O / src).read_bytes())
print(
    "Three diagnostic supplementary figures, six tables and source-level evidence ledger written"
)
