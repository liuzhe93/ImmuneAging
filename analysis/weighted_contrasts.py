import bootstrap
import pandas as pd, numpy as np
from run_benchmark import O, D, SEED
from prepare_benchmark import GROUPS

pred = pd.read_csv(O / "predictions_composition_500.csv")
weights = pd.read_csv(O / "age_standardisation_weights.csv")
bands = [19, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 76]
names = [f"{a}-{b-1}" for a, b in zip(bands[:-1], bands[1:])]
rows = []
comp = []
for c in ["aida", "onek1k"]:
    for model in ["M1_composition_EN", "M1b_composition_Ridge", "M1c_composition_HGB"]:
        a = pred[
            (pred.evaluation == "external")
            & (pred.test_cohort == c)
            & (pred.model == model)
        ]
        b = pred[
            (pred.evaluation == "OOF") & (pred.test_cohort == c) & (pred.model == model)
        ]
        z = a.merge(
            b[["donor_id", "prediction"]],
            on="donor_id",
            suffixes=("", "_internal"),
            validate="one_to_one",
        )
        z = z[z.age.between(19, 75)]
        bs = pd.cut(z.age, bands, right=False, labels=names).astype(str)
        w = bs.map(
            weights[weights.cohort == c].set_index("age_band").donor_weight
        ).to_numpy()
        diff = (
            abs(z.prediction - z.age) - abs(z.prediction_internal - z.age)
        ).to_numpy()
        rng = np.random.default_rng(SEED)
        samples = []
        for i in range(2000):
            ix = rng.integers(0, len(z), len(z))
            samples.append(np.average(diff[ix], weights=w[ix]))
        rows.append(
            {
                "test_cohort": c,
                "model": model,
                "n": len(z),
                "external_minus_internal_weighted_MAE": np.average(diff, weights=w),
                "low": np.quantile(samples, 0.025),
                "high": np.quantile(samples, 0.975),
            }
        )
    m = pd.read_csv(D / f"{c}_donors.csv")
    mask = (m.n_cells >= 500) & m.age.between(19, 75)
    X = np.load(D / f"{c}_composition_500.npy")[mask]
    m = m[mask]
    bs = pd.cut(m.age, bands, right=False, labels=names).astype(str)
    w = bs.map(
        weights[weights.cohort == c].set_index("age_band").donor_weight
    ).to_numpy()
    from scipy.stats import spearmanr

    for j, g in enumerate(GROUPS):
        rho = spearmanr(m.age, X[:, j]).statistic if np.ptp(X[:, j]) > 0 else np.nan
        comp.append(
            {
                "cohort": c,
                "feature": g,
                "n": len(m),
                "standardised_mean_fraction": np.average(X[:, j], weights=w),
                "common_age_spearman_rho": rho,
            }
        )
pd.DataFrame(rows).to_csv(O / "weighted_paired_transfer.csv", index=False)
pd.DataFrame(comp).to_csv(O / "composition_standardised.csv", index=False)
print(pd.DataFrame(rows).to_string(index=False))
