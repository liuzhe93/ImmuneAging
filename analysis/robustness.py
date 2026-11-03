"""Matched donor learning curves, paired cell-depth experiments and ablations.
All tuning is inside the available training subset. No synthetic expression data.
"""

import bootstrap, json, time, threading, os
import numpy as np, pandas as pd, psutil
from sklearn.model_selection import KFold, train_test_split
from threadpoolctl import threadpool_limits
from run_benchmark import R, D, O, SEED, fit_predict, GROUPS
from prepare_benchmark import load, group


def lowcells():
    out = []
    for c in ["onek1k", "aida"]:
        meta = pd.read_csv(D / f"{c}_donors.csv")
        don = np.asarray(load(c, "donor_id"))
        typ = load(c, "cell_type")
        ids, inv = np.unique(don, return_inverse=True)
        counts = np.zeros((len(ids), len(GROUPS)), int)
        for i, t in zip(inv, typ):
            counts[i, GROUPS.index(group(t))] += 1
        use = np.flatnonzero(meta.n_cells.to_numpy() >= 1000)
        m = meta.iloc[use].reset_index(drop=True)
        counts = counts[use]
        folds = list(KFold(5, shuffle=True, random_state=SEED).split(m))
        for rep in range(5):
            rng = np.random.default_rng(SEED + rep)
            # Drawing sequentially without replacement produces genuinely nested samples.
            left = counts.copy()
            taken = np.zeros_like(counts)
            mat = {}
            previous = 0
            for n in [100, 300, 500, 1000]:
                for i in range(len(m)):
                    draw = rng.multivariate_hypergeometric(left[i], n - previous)
                    taken[i] += draw
                    left[i] -= draw
                mat[n] = taken / n
                previous = n
            for n, X in mat.items():
                for fold, (tr, te) in enumerate(folds):
                    p, _ = fit_predict(
                        "M1_composition_EN",
                        X[tr],
                        m.age.to_numpy()[tr],
                        X[te],
                        SEED + fold,
                    )
                    out += [
                        {
                            "cohort": c,
                            "donor_id": m.donor_id[i],
                            "age": m.age[i],
                            "prediction": v,
                            "replicate": rep,
                            "n_cells": n,
                            "fold": fold,
                        }
                        for i, v in zip(te, p)
                    ]
            print("Matched cell experiment", c, rep, flush=True)
    pd.DataFrame(out).to_csv(O / "matched_cell_predictions.csv", index=False)


def learning():
    out = []
    for c in ["onek1k", "aida"]:
        m = pd.read_csv(D / f"{c}_donors.csv")
        use = m.n_cells >= 500
        X = np.load(D / f"{c}_composition_500.npy")[use]
        m = m.loc[use].reset_index(drop=True)
        y = m.age.to_numpy()
        tr, te = train_test_split(np.arange(len(y)), test_size=0.2, random_state=SEED)
        for rep in range(5):
            rng = np.random.default_rng(SEED + rep)
            shuffled = rng.permutation(tr)
            for n in [50, 100, 200, len(tr)]:
                sub = shuffled[:n]
                p, _ = fit_predict(
                    "M1_composition_EN", X[sub], y[sub], X[te], SEED + rep
                )
                out += [
                    {
                        "cohort": c,
                        "donor_id": m.donor_id[i],
                        "age": y[i],
                        "prediction": v,
                        "replicate": rep,
                        "training_donors": n,
                        "n_cells": 500,
                    }
                    for i, v in zip(te, p)
                ]
        print("Learning done", c, flush=True)
    pd.DataFrame(out).to_csv(O / "learning_predictions.csv", index=False)


def ablation():
    out = []
    drop = {
        "T_lineages": list(range(8)),
        "NK": [8],
        "B_lineages": [9, 10, 11],
        "Monocytes": [12, 13, 14],
        "DC": [15],
    }
    for c in ["onek1k", "aida"]:
        m = pd.read_csv(D / f"{c}_donors.csv")
        use = m.n_cells >= 500
        X = np.load(D / f"{c}_composition_500.npy")[use]
        m = m.loc[use].reset_index(drop=True)
        y = m.age.to_numpy()
        for label, indices in drop.items():
            xx = np.delete(
                X, indices, axis=1
            )  # no renormalisation; other fractions retain original denominator
            for fold, (tr, te) in enumerate(
                KFold(5, shuffle=True, random_state=SEED).split(y)
            ):
                p, _ = fit_predict(
                    "M1_composition_EN", xx[tr], y[tr], xx[te], SEED + fold
                )
                out += [
                    {
                        "cohort": c,
                        "donor_id": m.donor_id[i],
                        "age": y[i],
                        "prediction": v,
                        "removed": label,
                        "fold": fold,
                    }
                    for i, v in zip(te, p)
                ]
        print("Ablation done", c, flush=True)
    pd.DataFrame(out).to_csv(O / "ablation_predictions.csv", index=False)


def runtime(rep_only=None):
    records = []
    for c in ["onek1k", "aida"]:
        m = pd.read_csv(D / f"{c}_donors.csv")
        use = m.n_cells >= 500
        X = np.load(D / f"{c}_composition_500.npy")[use]
        m = m.loc[use].reset_index(drop=True)
        y = m.age.to_numpy()
        tr, te = train_test_split(np.arange(len(y)), test_size=0.2, random_state=SEED)
        for rep in (range(5) if rep_only is None else [rep_only]):
            for size in [50, 100, 200, len(tr)]:
                sub = np.random.default_rng(SEED + rep).permutation(tr)[:size]
                for name in [
                    "M1_composition_EN",
                    "M1b_composition_Ridge",
                    "M1c_composition_HGB",
                ]:
                    peak = [psutil.Process().memory_info().rss]
                    stop = threading.Event()

                    def sample():
                        proc = psutil.Process()
                        while not stop.wait(0.01):
                            peak.append(proc.memory_info().rss)

                    thread = threading.Thread(target=sample)
                    thread.start()
                    try:
                        p, tm = fit_predict(name, X[sub], y[sub], X[te], SEED + rep)
                    finally:
                        stop.set()
                        thread.join()
                    records.append(
                        {
                            "cohort": c,
                            "model": name,
                            "training_donors": size,
                            "test_donors": len(te),
                            "repeat": rep,
                            "MAE": np.mean(abs(y[te] - p)),
                            "peak_process_RSS_MiB": max(peak) / 2**20,
                            "baseline_RSS_MiB": peak[0] / 2**20,
                            "gpu": "not used",
                            **tm,
                        }
                    )
        print("Runtime done", c, flush=True)
    pd.DataFrame(records).to_csv(
        O
        / (
            "resource_repeats.csv"
            if rep_only is None
            else f"resource_repeat_{rep_only}.csv"
        ),
        index=False,
    )


if __name__ == "__main__":
    import sys

    with threadpool_limits(limits=1):
        if "--resource-rep" in sys.argv:
            runtime(int(sys.argv[-1]))
        else:
            lowcells()
            learning()
            ablation()
