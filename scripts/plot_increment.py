import sys, argparse, os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from immune_ageing.core import pd, np

os.environ.setdefault("MPLCONFIGDIR", str(ROOT / "outputs" / "mpl_cache"))
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams.update({"svg.fonttype": "none", "pdf.fonttype": 42})
p = argparse.ArgumentParser()
p.add_argument("--reference", default=str(ROOT.parent / "tables" / "BIB_review_v2"))
p.add_argument("--output", default=str(ROOT / "outputs" / "figures"))
a = p.parse_args()
O = Path(a.reference)
F = Path(a.output)
F.mkdir(parents=True, exist_ok=True)
COL = {"aida": "#267D9A", "onek1k": "#C06A31"}
TITLE = {"aida": "AIDA v1", "onek1k": "OneK1K"}


def save(fig, name):
    for ext in ["png", "pdf", "svg"]:
        fig.savefig(F / (name + "." + ext), dpi=300, bbox_inches="tight")
    plt.close(fig)


delta = pd.read_csv(O / "deposited_paired_differences.csv")
ab = pd.read_csv(O / "ablation_summary.csv")
coarse = pd.read_csv(O / "T_collapsed_comparison.csv").rename(
    columns={"cohort": "cohort"}
)
coarse["removed"] = "T_subsets_merged"
ab = pd.concat(
    [ab, coarse[["cohort", "removed", "n", "delta_MAE", "low", "high"]]],
    ignore_index=True,
)
ab = ab[ab.removed != "T_lineages"].copy()
fig, ax = plt.subplots(2, 1, figsize=(7.5, 8.2), gridspec_kw={"height_ratios": [2, 1]})
eligible = (
    delta[(delta.comparison == "combined_minus_proportion") & (delta.n >= 100)]
    .groupby("lineage")
    .cohort.nunique()
)
lineages = sorted(eligible[eligible == 2].index)
short = (
    lambda s: s.replace("naive thymus-derived ", "naive ")
    .replace(", alpha-beta", "")
    .replace("CD14-low, CD16-positive monocyte", "CD16 monocyte")
    .replace("CD14-positive monocyte", "CD14 monocyte")
    .replace("CD4-positive", "CD4")
    .replace("CD8-positive", "CD8")
    .replace("CD16-negative, CD56-bright natural killer cell, human", "CD56-bright NK")
    .replace("CD16-positive, CD56-dim natural killer cell, human", "CD56-dim NK")
    .replace("plasmacytoid dendritic cell", "pDC")
)
for k, c in enumerate(COL):
    for i, l in enumerate(lineages):
        z = delta[
            (delta.cohort == c)
            & (delta.lineage == l)
            & (delta.comparison == "combined_minus_proportion")
        ]
        if len(z):
            z = z.iloc[0]
            ax[0].errorbar(
                z.delta_MAE,
                i + (k - 0.5) * 0.22,
                xerr=[[z.delta_MAE - z.low], [z.high - z.delta_MAE]],
                fmt="o",
                ms=3,
                color=COL[c],
                capsize=2,
                label=TITLE[c] if i == 0 else None,
            )
    z = ab[ab.cohort == c].set_index("removed").loc[sorted(ab.removed.unique())]
    ax[1].errorbar(
        z.delta_MAE,
        np.arange(len(z)) + (k - 0.5) * 0.2,
        xerr=np.array([z.delta_MAE - z.low, z.high - z.delta_MAE]),
        fmt="o",
        color=COL[c],
        capsize=3,
        label=TITLE[c],
    )
ax[0].set(
    yticks=np.arange(len(lineages)),
    yticklabels=[short(l) for l in lineages],
    xlabel="Combined − proportion MAE (years)",
    title="A  Deposited predictions  paired donor errors",
)
ax[0].tick_params(axis="y", labelsize=8.5)
ax[0].axvline(0, color="grey", ls="--")
ax[0].legend(frameon=False, fontsize=8)
ax[1].set(
    yticks=np.arange(len(ab.removed.unique())),
    yticklabels=[x.replace("_", " ") for x in sorted(ab.removed.unique())],
    xlabel="Modified − full composition MAE (years)",
    title="B  T subset resolution and feature ablation",
)
ax[1].axvline(0, color="grey", ls="--")
ax[1].legend(frameon=False, fontsize=8)
fig.tight_layout()
save(fig, "Figure_6_increment_and_ablation")
