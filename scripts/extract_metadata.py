"""Extract the required obs columns from the exact downloaded h5ad releases."""

import argparse, json, hashlib
from pathlib import Path
import h5py, numpy as np

FIELDS = ["donor_id", "cell_type", "cell_type_ontology_term_id", "sex", "disease"]


def decode(dataset):
    a = dataset[:]
    return [
        (
            x.decode()
            if isinstance(x, bytes)
            else x.item() if isinstance(x, np.generic) else x
        )
        for x in a
    ]


def column(node):
    if isinstance(node, h5py.Dataset):
        return decode(node)
    if "categories" in node and "codes" in node:
        cats = decode(node["categories"])
        return [cats[i] if i >= 0 else None for i in node["codes"][:]]
    if "values" in node:
        return decode(node["values"])
    raise ValueError("Unsupported AnnData obs encoding: " + node.name)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--onek1k", required=True)
    p.add_argument("--aida", required=True)
    p.add_argument("--output", required=True)
    a = p.parse_args()
    out = Path(a.output)
    out.mkdir(parents=True, exist_ok=True)
    for cohort, file, expected in [
        ("onek1k", a.onek1k, 1248980),
        ("aida", a.aida, 1058909),
    ]:
        with h5py.File(file, "r") as h:
            fields = FIELDS + (["age"] if cohort == "onek1k" else ["development_stage"])
            for field in fields:
                values = column(h["obs"][field])
                if len(values) != expected:
                    raise ValueError("Wrong release or incomplete metadata: " + cohort)
                (out / f"{cohort}_{field}.json").write_text(
                    json.dumps(values), encoding="utf8"
                )
        print(
            cohort,
            expected,
            "obs records extracted; expression matrix was not read",
            flush=True,
        )


if __name__ == "__main__":
    main()
