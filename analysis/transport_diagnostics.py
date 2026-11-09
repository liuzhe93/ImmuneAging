import bootstrap, json
import numpy as np, pandas as pd
from scipy.stats import spearmanr
from sklearn.model_selection import KFold
from run_benchmark import D, O, SEED, fit_predict, metrics
from prepare_benchmark import GROUPS
from pathlib import Path

R = Path(__file__).resolve().parent
pred = pd.read_csv(O / "predictions_composition_500.csv")
bands = np.array([19, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 76])
names = [f"{a}-{b-1}" for a, b in zip(bands[:-1], bands[1:])]
meta = {}
fractions = {}
distribution = []
association = []
for c in ["aida", "onek1k"]:
    m = pd.read_csv(D / f"{c}_donors.csv")
    keep = m.n_cells >= 500
    X = np.load(D / f"{c}_composition_500.npy")[keep]
    m = m.loc[keep].reset_index(drop=True)
    meta[c] = m
    fractions[c] = X
    assert np.max(abs(X.sum(axis=1) - 1)) < 1e-12
    for j, g in enumerate(GROUPS):
        r, p = spearmanr(m.age, X[:, j])
        association.append(
            {
                "cohort": c,
                "feature": g,
                "n": len(m),
                "rho": r,
                "p_descriptive": p,
                "zero_fraction": float(np.mean(X[:, j] == 0)),
            }
        )
        distribution.append(
            {
                "cohort": c,
                "feature": g,
                "n": len(m),
                "median": np.median(X[:, j]),
                "q25": np.quantile(X[:, j], 0.25),
                "q75": np.quantile(X[:, j], 0.75),
                "mean": X[:, j].mean(),
            }
        )
    counts = []
    for c, m in meta.items():
        a = pd.cut(m.age, bands, right=False, labels=names)
        counts.append(a.value_counts(sort=False).to_numpy())
# Called only after both cohorts are present.
counts = np.array(
    [
        pd.cut(meta[c].age, bands, right=False, labels=names)
        .value_counts(sort=False)
        .to_numpy()
        for c in ["aida", "onek1k"]
    ]
)
probs = counts / counts.sum(axis=1)[:, None]
q = np.min(probs, axis=0)
q = q / q.sum()
assert (counts > 0).all()
weights = []
for j, c in enumerate(["aida", "onek1k"]):
    for k, b in enumerate(names):
        weights.append(
            {
                "cohort": c,
                "age_band": b,
                "n": int(counts[j, k]),
                "test_probability": probs[j, k],
                "target_probability": q[k],
                "donor_weight": q[k] / probs[j, k],
            }
        )
w = pd.DataFrame(weights)
w.to_csv(O / "age_standardisation_weights.csv", index=False)
weighted = []
strat = []
for (ev, src, dst, model), g in pred.groupby(
    ["evaluation", "train_cohort", "test_cohort", "model"]
):
    for band, z in g.assign(
        age_band=pd.cut(g.age, bands, right=False, labels=names)
    ).groupby("age_band", observed=True):
        if not len(z):
            continue
        err = z.prediction - z.age
        strat.append(
            {
                "evaluation": ev,
                "train_cohort": src,
                "test_cohort": dst,
                "model": model,
                "age_band": str(band),
                "n": len(z),
                "MAE": abs(err).mean(),
                "bias_prediction_minus_observed": err.mean(),
            }
        )
    z = g.loc[g.age.between(19, 75)].copy()
    z["age_band"] = pd.cut(z.age, bands, right=False, labels=names).astype(str)
    ww = z.age_band.map(
        w[w.cohort == dst].set_index("age_band").donor_weight
    ).to_numpy()
    y = z.age.to_numpy()
    p = z.prediction.to_numpy()
    rng = np.random.default_rng(SEED)
    bs = []
    for i in range(2000):
        ix = rng.integers(0, len(z), len(z))
        bs.append(np.average(abs(p[ix] - y[ix]), weights=ww[ix]))
    weighted.append(
        {
            "evaluation": ev,
            "train_cohort": src,
            "test_cohort": dst,
            "model": model,
            "n": len(z),
            "effective_n": ww.sum() ** 2 / (ww**2).sum(),
            "weighted_MAE": np.average(abs(p - y), weights=ww),
            "low": np.quantile(bs, 0.025),
            "high": np.quantile(bs, 0.975),
            "weighted_bias_prediction_minus_observed": np.average(p - y, weights=ww),
        }
    )
pd.DataFrame(weighted).to_csv(O / "age_standardised_metrics.csv", index=False)
pd.DataFrame(strat).to_csv(O / "age_stratified_errors.csv", index=False)
pd.DataFrame(distribution).to_csv(O / "composition_distribution.csv", index=False)
pd.DataFrame(association).to_csv(O / "composition_age_association.csv", index=False)
# Collapse eight T-lineage columns into a single total, retaining all other fractions.
rows = []
summary = []
for c, m in meta.items():
    X = fractions[c]
    coarse = np.c_[X[:, :8].sum(axis=1), X[:, 8:]]
    assert np.allclose(coarse.sum(axis=1), 1)
    for fold, (tr, te) in enumerate(KFold(5, shuffle=True, random_state=SEED).split(m)):
        p, _ = fit_predict(
            "M1_composition_EN",
            coarse[tr],
            m.age.to_numpy()[tr],
            coarse[te],
            SEED + fold,
        )
        rows += [
            {
                "cohort": c,
                "donor_id": m.donor_id[i],
                "age": m.age[i],
                "prediction": float(v),
                "fold": fold,
                "representation": "total_T_plus_nonT",
            }
            for i, v in zip(te, p)
        ]
    z = pd.DataFrame(rows)
    z = z[z.cohort == c].merge(
        pred[
            (pred.evaluation == "OOF")
            & (pred.cohort == c)
            & (pred.model == "M1_composition_EN")
        ][["donor_id", "prediction"]],
        on="donor_id",
        suffixes=("", "_full"),
        validate="one_to_one",
    )
    delta = (abs(z.prediction - z.age) - abs(z.prediction_full - z.age)).to_numpy()
    rng = np.random.default_rng(SEED)
    boot = [delta[rng.integers(0, len(delta), len(delta))].mean() for _ in range(2000)]
    summary.append(
        {
            "cohort": c,
            "n": len(z),
            "coarse_MAE": abs(z.prediction - z.age).mean(),
            "full_MAE": abs(z.prediction_full - z.age).mean(),
            "delta_MAE": delta.mean(),
            "low": np.quantile(boot, 0.025),
            "high": np.quantile(boot, 0.975),
            "closure_max_error": float(
                np.max(abs(X[:, :8].sum(axis=1) - (1 - X[:, 8:].sum(axis=1))))
            ),
        }
    )
pd.DataFrame(rows).to_csv(O / "T_collapsed_predictions.csv", index=False)
pd.DataFrame(summary).to_csv(O / "T_collapsed_comparison.csv", index=False)
print(
    pd.DataFrame(weighted)
    .query("evaluation=='external' and model=='M1_composition_EN'")
    .to_string(index=False)
)
print(pd.DataFrame(summary).to_string(index=False))
