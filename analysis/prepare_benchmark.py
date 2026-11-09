"""Build donor metadata and nested composition features.
No outcome-dependent feature selection. Exact 300/500/1000 nested samples.
"""

import bootstrap, json, re, time, collections
from pathlib import Path
import numpy as np, pandas as pd

R = Path(__file__).resolve().parent
D = bootstrap.DATA / "processed"
D.mkdir(parents=True, exist_ok=True)
SEED = 20261030
GROUPS = [
    "CD4_naive",
    "CD4_other",
    "CD8_naive",
    "CD8_other",
    "Treg",
    "gdT",
    "MAIT",
    "T_other",
    "NK",
    "B_naive",
    "B_memory",
    "B_other",
    "Mono_CD14",
    "Mono_CD16",
    "Mono_other",
    "DC",
    "Other",
]


def group(s):
    if "naive thymus-derived CD4" in s:
        return "CD4_naive"
    if "naive thymus-derived CD8" in s:
        return "CD8_naive"
    if "regulatory" in s:
        return "Treg"
    if "gamma-delta" in s:
        return "gdT"
    if "mucosal" in s:
        return "MAIT"
    if "CD4" in s:
        return "CD4_other"
    if "CD8" in s:
        return "CD8_other"
    if "T cell" in s or "thymocyte" in s:
        return "T_other"
    if "natural killer" in s or "innate lymphoid" in s:
        return "NK"
    if s == "naive B cell":
        return "B_naive"
    if s == "memory B cell":
        return "B_memory"
    if "B cell" in s or "plasma" in s:
        return "B_other"
    if s == "CD14-positive monocyte":
        return "Mono_CD14"
    if s == "CD14-low, CD16-positive monocyte":
        return "Mono_CD16"
    if "monocyte" in s:
        return "Mono_other"
    if "dendritic" in s:
        return "DC"
    return "Other"


def load(c, key):
    return json.loads((bootstrap.EVIDENCE / f"{c}_{key}.json").read_text())


def prepare(c):
    t = time.perf_counter()
    donors = np.asarray(load(c, "donor_id"))
    types = np.asarray(load(c, "cell_type"))
    sex = np.asarray(load(c, "sex"))
    disease = np.asarray(load(c, "disease"))
    ages = (
        np.asarray(load(c, "age"), float)
        if c == "onek1k"
        else np.asarray(
            [
                float(re.fullmatch(r"(\d+)-year-old stage", s)[1])
                for s in load(c, "development_stage")
            ]
        )
    )
    ids, inv = np.unique(donors, return_inverse=True)
    gmap = {s: GROUPS.index(group(s)) for s in set(types)}
    labels = np.array([gmap[s] for s in types], np.int16)
    order = np.argsort(inv, kind="stable")
    cuts = np.r_[0, np.cumsum(np.bincount(inv))]
    metadata = []
    rank = np.full(len(donors), 32767, np.int16)
    fractions = {
        n: np.full((len(ids), len(GROUPS)), np.nan) for n in [100, 300, 500, 1000]
    }
    for i, donor in enumerate(ids):
        ix = order[cuts[i] : cuts[i + 1]]
        if len(set(ages[ix])) != 1 or len(set(sex[ix])) != 1:
            raise ValueError("Inconsistent donor metadata")
        if set(disease[ix]) != {"normal"}:
            raise ValueError("Nonhealthy donor")
        metadata.append(
            {
                "cohort": c,
                "donor_id": donor,
                "age": ages[ix[0]],
                "sex": sex[ix[0]],
                "n_cells": len(ix),
            }
        )
        rng = np.random.default_rng(
            np.random.SeedSequence([SEED, i, 0 if c == "onek1k" else 1])
        )
        take = rng.permutation(ix)[:1000]
        rank[take] = np.arange(len(take))
        for n in fractions:
            if len(ix) >= n:
                fractions[n][i] = (
                    np.bincount(labels[take[:n]], minlength=len(GROUPS)) / n
                )
    donor_frame = pd.DataFrame(metadata)
    if donor_frame.donor_id.duplicated().any() or not np.isfinite(donor_frame.age).all() or (donor_frame.age < 18).any():
        raise ValueError("Expected unique adult donors with finite ages")
    for n, matrix in fractions.items():
        valid = donor_frame.n_cells.to_numpy() >= n
        if len(matrix) != len(donor_frame) or not np.isfinite(matrix[valid]).all() or not np.allclose(matrix[valid].sum(axis=1), 1):
            raise ValueError(f"Invalid aligned composition matrix at {n} cells")
    pd.DataFrame(metadata).to_csv(D / f"{c}_donors.csv", index=False)
    for n, v in fractions.items():
        np.save(D / f"{c}_composition_{n}.npy", v)
    np.savez_compressed(D / f"{c}_selection.npz", donor_index=inv, cell_rank=rank)
    (D / f"{c}_annotation_mapping.json").write_text(
        json.dumps({s: group(s) for s in sorted(gmap)}, indent=2)
    )
    pd.DataFrame(
        [
            {
                "cohort": c,
                "threshold": n,
                "retained": int(sum(z["n_cells"] >= n for z in metadata)),
                "total": len(ids),
            }
            for n in [100, 300, 500, 1000, 3000]
        ]
    ).to_csv(D / f"{c}_eligibility.csv", index=False)
    (D / f"{c}_metadata_timing.json").write_text(
        json.dumps(
            {
                "seconds": time.perf_counter() - t,
                "stage": "metadata loading, harmonisation and one nested sampling realization",
            }
        )
    )
    print("Prepared metadata", c, len(ids), flush=True)


if __name__ == "__main__":
    for c in ["onek1k", "aida"]:
        prepare(c)
