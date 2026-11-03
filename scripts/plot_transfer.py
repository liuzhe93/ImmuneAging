import sys, argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from immune_ageing.core import pd, np
import os

os.environ.setdefault("MPLCONFIGDIR", str(ROOT / "outputs" / "mpl_cache"))
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams.update({"svg.fonttype": "none", "pdf.fonttype": 42})
p = argparse.ArgumentParser()
p.add_argument("--results", default=str(ROOT / "outputs"))
p.add_argument("--output", default=str(ROOT / "outputs" / "figures"))
a = p.parse_args()
r = Path(a.results)
out = Path(a.output)
out.mkdir(parents=True, exist_ok=True)
z = pd.read_csv(r / "all_metrics.csv")
w = pd.read_csv(r / "age_standardised_metrics.csv")
z = z[(z.model == "M1_composition_EN") & (z.training_age == "all")]
w = w[(w.model == "M1_composition_EN") & (w.scheme == "five_year")]
fig, axes = plt.subplots(2, 3, figsize=(10, 6))
records = []
for i, rep in enumerate(["fine17", "coarse5"]):
    for j, mode in enumerate(["all", "weighted", "source_common"]):
        q = (
            z[z.representation == rep]
            if mode == "all"
            else w[
                (w.representation == rep)
                & (w.training_age == ("common" if mode == "source_common" else "all"))
            ]
        )
        col = "MAE" if mode == "all" else "weighted_MAE"
        arr = np.zeros((2, 2))
        for ti, train in enumerate(["aida", "onek1k"]):
            for tj, test in enumerate(["aida", "onek1k"]):
                v = float(
                    q[(q.train_cohort == train) & (q.test_cohort == test)][col].iloc[0]
                )
                arr[ti, tj] = v
                records.append(
                    dict(
                        representation=rep,
                        condition=mode,
                        train=train,
                        test=test,
                        MAE=v,
                    )
                )
                axes[i, j].text(
                    tj, ti, f"{v:.2f}", ha="center", va="center", fontsize=13
                )
        # Rectangle cells remain editable vector objects in SVG and PDF.
        for row in range(2):
            for column in range(2):
                colour = plt.cm.YlOrRd(np.clip((arr[row, column] - 5) / 20, 0, 1))
                axes[i, j].add_patch(
                    plt.Rectangle(
                        (column - 0.5, row - 0.5),
                        1,
                        1,
                        facecolor=colour,
                        edgecolor="none",
                        zorder=0,
                    )
                )
        axes[i, j].set_xlim(-0.5, 1.5)
        axes[i, j].set_ylim(1.5, -0.5)
        axes[i, j].set_aspect("equal")
        axes[i, j].set_xticks([0, 1], ["AIDA", "OneK1K"])
        axes[i, j].set_yticks([0, 1], ["AIDA", "OneK1K"])
        axes[i, j].set_title(
            ("17 groups" if i == 0 else "5 shared groups")
            + "\n"
            + {
                "all": "All eligible ages",
                "weighted": "Weighted common test ages",
                "source_common": "Common source and weighted test ages",
            }[mode],
            fontsize=10,
        )
        axes[i, j].set_xlabel("Test cohort")
        axes[i, j].set_ylabel("Train cohort")
fig.tight_layout()
for ext in ["png", "svg", "pdf"]:
    fig.savefig(out / ("Figure_3_frozen_transfer." + ext), dpi=240)
pd.DataFrame(records).to_csv(out / "Figure_3_source.csv", index=False)
