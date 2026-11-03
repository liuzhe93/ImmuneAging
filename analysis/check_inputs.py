"""Validate downloaded metadata and author-released prediction archives."""

import bootstrap, json, hashlib, zipfile, shutil
from pathlib import Path

R = bootstrap.ROOT
source = json.loads((R / "inputs/data_sources.json").read_text())
expected_values = json.loads((R / "inputs/metadata_value_checksums.json").read_text())
records = []


def checksum(p, algorithm="sha256"):
    h = hashlib.new(algorithm)
    with p.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


for cohort, total in [("onek1k", 1248980), ("aida", 1058909)]:
    fields = [
        "donor_id",
        "cell_type",
        "cell_type_ontology_term_id",
        "sex",
        "disease",
    ] + (["age"] if cohort == "onek1k" else ["development_stage"])
    for field in fields:
        p = bootstrap.EVIDENCE / f"{cohort}_{field}.json"
        if not p.is_file():
            raise FileNotFoundError(
                f"Missing metadata {p}; extract the obs fields from the pinned h5ad release first."
            )
        values = json.loads(p.read_text(encoding="utf8"))
        value_hash = hashlib.sha256(
            json.dumps(values, ensure_ascii=True, separators=(",", ":")).encode()
        ).hexdigest()
        if value_hash != expected_values[p.name]:
            raise ValueError(
                "Metadata values or cell order differ from the pinned release: "
                + p.name
            )
        if len(values) != total:
            raise ValueError(
                f"{p.name}: expected {total} cells, received {len(values)}"
            )
        records.append(
            {
                "cohort": cohort,
                "file": p.name,
                "cells": len(values),
                "sha256": checksum(p),
            }
        )
deposited = bootstrap.resolve(bootstrap.cfg["deposited_root"])
target = bootstrap.DATA / "deposited"
target.mkdir(exist_ok=True)
for row in source["deposited_predictions"]["files"]:
    p = deposited / row["file"]
    if not p.is_file():
        raise FileNotFoundError(
            f"Missing {p}; obtain the six files from Zenodo record 10405106."
        )
    digest = checksum(p, "md5")
    if digest != row["md5"]:
        raise ValueError("MD5 mismatch: " + str(p))
    copy = target / p.name
    if not copy.exists() or checksum(copy, "md5") != digest:
        shutil.copy2(p, copy)
    if p.suffix == ".zip":
        out = target / p.stem
        out.mkdir(exist_ok=True)
        with zipfile.ZipFile(p) as z:
            for member in z.infolist():
                if not (out / member.filename).resolve().is_relative_to(out.resolve()):
                    raise ValueError("Unsafe archive member")
            z.extractall(out)
    records.append({"file": p.name, "md5": digest, "bytes": p.stat().st_size})
(bootstrap.OUT / "logs").mkdir(exist_ok=True)
(bootstrap.OUT / "logs/input_manifest.json").write_text(
    json.dumps(records, indent=2), encoding="utf8"
)
print(
    "Exact atlas cell counts and all six deposited-file checksums verified", flush=True
)
