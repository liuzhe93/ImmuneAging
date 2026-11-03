"""Shared paths for the empirical analysis stages."""

import json, os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = Path(os.environ["IMMUNE_CONFIG"])
cfg = json.loads(CONFIG.read_text(encoding="utf8"))


def resolve(value):
    p = Path(value).expanduser()
    return p.resolve() if p.is_absolute() else (CONFIG.parent / p).resolve()


OUT = resolve(os.environ.get("IMMUNE_OUTPUT", cfg["output_root"]))
for key in [
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
]:
    os.environ[key] = "1"
os.environ["MPLCONFIGDIR"] = str(OUT / "logs" / "mpl_cache")
DATA = OUT / "data"
EVIDENCE = resolve(cfg["metadata_root"])
RESULTS = OUT / "results" / "baseline"
FIGURES = OUT / "figures" / "main"
for p in [DATA, RESULTS, FIGURES]:
    p.mkdir(parents=True, exist_ok=True)


def location(key, default):
    paths = {
        "supplementary_root": OUT / "figures" / "supplementary",
        "repertoire_source": ROOT / "inputs/source_evidence/repertoire.xml",
    }
    return paths.get(key, OUT / default)


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf8", errors="replace")
