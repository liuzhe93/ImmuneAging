"""Optional downloader for the pinned atlas h5ad assets and six Zenodo prediction files."""

import argparse, json, hashlib
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[1]


def download(url, path, md5=None):
    if not path.exists():
        temp = path.with_suffix(path.suffix + ".partial")
        with requests.get(url, stream=True, timeout=120) as r:
            r.raise_for_status()
            with temp.open("wb") as f:
                for block in r.iter_content(1024 * 1024):
                    f.write(block)
        temp.replace(path)
    if md5:
        h = hashlib.md5()
        with path.open("rb") as f:
            for block in iter(lambda: f.read(1024 * 1024), b""):
                h.update(block)
        if h.hexdigest() != md5:
            raise ValueError("Checksum mismatch: " + str(path))
    print(path, flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", required=True)
    p.add_argument("--atlas", nargs="*", choices=["onek1k", "aida"], default=[])
    p.add_argument("--predictions", action="store_true")
    a = p.parse_args()
    out = Path(a.output)
    out.mkdir(parents=True, exist_ok=True)
    source = json.loads((ROOT / "inputs/data_sources.json").read_text())
    for c in a.atlas:
        asset = next(
            x
            for x in source[c]["assets"]
            if x.get("filetype") == "H5AD"
            or x.get("url", "").lower().split("?")[0].endswith(".h5ad")
        )
        download(asset["url"], out / (c + ".h5ad"))
    if a.predictions:
        for row in source["deposited_predictions"]["files"]:
            download(row["url"], out / row["file"], row["md5"])


if __name__ == "__main__":
    main()
