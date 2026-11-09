"""Donor-disjoint nested CV and frozen transfer; never split cells as samples.
Invoked by run_analysis.py; evaluates 300, 500 and 1000-cell eligibility.
"""

import bootstrap, json, time, platform, threading, os, sys
from pathlib import Path
import numpy as np, pandas as pd, psutil
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import ElasticNet, Ridge
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import KFold, GridSearchCV
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.decomposition import PCA
from threadpoolctl import threadpool_limits
from prepare_benchmark import GROUPS

R = Path(__file__).resolve().parent
D = bootstrap.DATA / "processed"
O = bootstrap.RESULTS
O.mkdir(exist_ok=True)
SEED = 20261030


def model(name):
    if name == "M0_median":
        return None, {}
    if name == "M1c_composition_HGB":
        est = HistGradientBoostingRegressor(
            max_iter=100, max_bins=63, early_stopping=False, random_state=SEED
        )
        grid = {"model__max_leaf_nodes": [7, 15], "model__learning_rate": [0.05, 0.1]}
    elif name == "M1b_composition_Ridge":
        est = Ridge()
        grid = {"model__alpha": [0.1, 1, 10, 100]}
    elif name == "M1_composition_EN":
        est = ElasticNet(l1_ratio=0.5, max_iter=20000, tol=1e-4, random_state=SEED)
        grid = {"model__alpha": [0.01, 0.1, 1, 10]}
    else:
        raise ValueError("Unsupported composition model: " + name)
    return Pipeline([("scale", StandardScaler()), ("model", est)]), grid


def fit_predict(name, X, y, Z, seed=SEED):
    if name == "M0_median":
        return np.repeat(np.median(y), len(Z)), {
            "search_s": 0.0,
            "fit_s": 0.0,
            "predict_s": 0.0,
            "params": {},
        }
    est, grid = model(name)
    cv = KFold(3, shuffle=True, random_state=seed)
    q = GridSearchCV(
        est,
        grid,
        scoring="neg_mean_absolute_error",
        cv=cv,
        refit=False,
        n_jobs=1,
        error_score="raise",
    )
    t = time.perf_counter()
    q.fit(X, y)
    search = time.perf_counter() - t
    est.set_params(**q.best_params_)
    t = time.perf_counter()
    est.fit(X, y)
    fit = time.perf_counter() - t
    t = time.perf_counter()
    p = est.predict(Z)
    pred = time.perf_counter() - t
    return p, {
        "search_s": search,
        "fit_s": fit,
        "predict_s": pred,
        "params": q.best_params_,
    }


def get_data(n, expression=False):
    if expression:
        raise ValueError("This benchmark uses measured cell composition only")
    out = {}
    for c in ["onek1k", "aida"]:
        m = pd.read_csv(D / f"{c}_donors.csv")
        mask = m.n_cells.to_numpy() >= n
        comp = np.load(D / f"{c}_composition_{n}.npy")[mask]
        m = m.loc[mask].reset_index(drop=True)
        out[c] = (
            m,
            {
                key: comp
                for key in [
                    "M0_median",
                    "M1_composition_EN",
                    "M1b_composition_Ridge",
                    "M1c_composition_HGB",
                ]
            },
        )
    return out


def run(n, expression=False, tag="main"):
    data = get_data(n, expression)
    preds = []
    times = []
    splits = []
    for c, (m, features) in data.items():
        y = m.age.to_numpy()
        outer = list(KFold(5, shuffle=True, random_state=SEED).split(y))
        print("CV", c, n, list(features), flush=True)
        for fold, (tr, te) in enumerate(outer):
            splits += [
                {
                    "cohort": c,
                    "donor_id": m.donor_id[i],
                    "fold": fold,
                    "condition": tag,
                    "n_cells": n,
                }
                for i in te
            ]
            for name, X in features.items():
                p, tm = fit_predict(name, X[tr], y[tr], X[te], SEED + fold)
                times.append(
                    {
                        "cohort": c,
                        "model": name,
                        "fold": fold,
                        "n_cells": n,
                        "condition": tag,
                        **tm,
                    }
                )
                preds += [
                    {
                        "cohort": c,
                        "train_cohort": c,
                        "test_cohort": c,
                        "model": name,
                        "donor_id": m.donor_id[i],
                        "age": y[i],
                        "prediction": float(v),
                        "fold": fold,
                        "evaluation": "OOF",
                        "n_cells": n,
                        "condition": tag,
                    }
                    for i, v in zip(te, p)
                ]
            print(c, n, "fold", fold, "done", flush=True)
    for src, (m, features) in data.items():
        for dst, (test, testfeatures) in data.items():
            if src == dst:
                continue
            for name, X in features.items():
                p, tm = fit_predict(name, X, m.age.to_numpy(), testfeatures[name])
                times.append(
                    {
                        "cohort": src,
                        "test_cohort": dst,
                        "model": name,
                        "fold": "full",
                        "n_cells": n,
                        "condition": tag,
                        **tm,
                    }
                )
                preds += [
                    {
                        "cohort": dst,
                        "train_cohort": src,
                        "test_cohort": dst,
                        "model": name,
                        "donor_id": test.donor_id[i],
                        "age": test.age[i],
                        "prediction": float(v),
                        "fold": -1,
                        "evaluation": "external",
                        "n_cells": n,
                        "condition": tag,
                    }
                    for i, v in enumerate(p)
                ]
    pd.DataFrame(preds).to_csv(O / f"predictions_{tag}_{n}.csv", index=False)
    pd.DataFrame(times).to_csv(O / f"timing_{tag}_{n}.csv", index=False)
    pd.DataFrame(splits).to_csv(O / f"folds_{tag}_{n}.csv", index=False)
    return preds


def metrics(df, seed=SEED):
    y = df.age.to_numpy()
    p = df.prediction.to_numpy()
    err = np.abs(y - p)
    rng = np.random.default_rng(seed)
    boot = np.array(
        [err[rng.integers(0, len(err), len(err))].mean() for _ in range(2000)]
    )
    slope, intercept = (
        np.polyfit(p, y, 1) if np.std(p) > 1e-10 else [float("nan"), float("nan")]
    )
    return {
        "n": len(y),
        "MAE": err.mean(),
        "MAE_low": np.quantile(boot, 0.025),
        "MAE_high": np.quantile(boot, 0.975),
        "RMSE": np.sqrt(mean_squared_error(y, p)),
        "R2": r2_score(y, p),
        "calibration_slope": slope,
        "calibration_intercept": intercept,
        "bias_pred_minus_age": np.mean(p - y),
    }


def summarise():
    records = []
    for path in O.glob("predictions_*.csv"):
        d = pd.read_csv(path)
        for keys, g in d.groupby(
            [
                "condition",
                "n_cells",
                "evaluation",
                "train_cohort",
                "test_cohort",
                "model",
            ]
        ):
            base = dict(
                zip(
                    [
                        "condition",
                        "n_cells",
                        "evaluation",
                        "train_cohort",
                        "test_cohort",
                        "model",
                    ],
                    keys,
                )
            )
            records.append({**base, "age_scope": "all", **metrics(g)})
            records.append(
                {
                    **base,
                    "age_scope": "common_19_75",
                    **metrics(g.loc[g.age.between(19, 75)]),
                }
            )
    pd.DataFrame(records).to_csv(O / "metrics.csv", index=False)


if __name__ == "__main__":
    with threadpool_limits(limits=1):
        expr = False
        for n in ([300, 500, 1000] if "--sensitivity" in sys.argv else [500]):
            run(n, expr, "expression" if expr else "composition")
        summarise()
    (O / "environment.json").write_text(
        json.dumps(
            {
                "date": __import__("datetime")
                .datetime.now(__import__("datetime").timezone.utc)
                .isoformat(),
                "python": sys.version,
                "platform": platform.platform(),
                "cpu": platform.processor(),
                "logical_cpus": psutil.cpu_count(),
                "ram_bytes": psutil.virtual_memory().total,
                "threads": 1,
                "seed": SEED,
                "bootstrap_resamples": 2000,
                "ci_scope": "Conditional on fitted out-of-fold predictions; does not include refitting uncertainty",
                "pretrained_status": "Not executed; no performance or resource ranking permitted",
            },
            indent=2,
        )
    )
