"""Run the scientific workflow from downloaded inputs to publication figures and tables."""

import argparse, json, os, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STAGES = [
    "inputs",
    "features",
    "baseline",
    "robustness",
    "resources",
    "secondary",
    "transport",
    "weighted",
    "support",
    "sensitivity",
    "main_figures",
    "diagnostic_figures",
    "literature_figures",
    "tables",
    "validation",
]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", required=True)
    p.add_argument("--output", help="Override the output root")
    p.add_argument(
        "--stages",
        nargs="+",
        choices=STAGES,
        help="Run selected stages in the listed order",
    )
    a = p.parse_args()
    config = Path(a.config).expanduser().resolve()
    cfg = json.loads(config.read_text())
    out = Path(a.output or cfg["output_root"]).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    (out / "logs").mkdir(exist_ok=True)
    assert (
        cfg["seed"] == 20261030
        and cfg["primary_cells"] == 500
        and cfg["bootstrap_resamples"] == 2000
        and cfg["threads"] == 1
    ), "The publication workflow uses fixed settings."
    env = os.environ.copy()
    env.update(IMMUNE_CONFIG=str(config), IMMUNE_OUTPUT=str(out), PYTHONUTF8="1")
    for key in [
        "OMP_NUM_THREADS",
        "MKL_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
    ]:
        env[key] = "1"
    env["MPLCONFIGDIR"] = str(out / "logs/mpl_cache")
    A = ROOT / "analysis"
    S = ROOT / "scripts"
    baseline = out / "results/baseline"
    sensitivity = out / "results/sensitivity"
    fig = out / "figures/main"
    commands = {
        "inputs": [(A / "check_inputs.py", [])],
        "features": [(A / "prepare_benchmark.py", [])],
        "baseline": [(A / "run_benchmark.py", ["--sensitivity"])],
        "robustness": [(A / "robustness.py", [])],
        "resources": [(A / "resource_process_repeats.py", [])],
        "secondary": [(A / "reanalyse_deposited.py", [])],
        "transport": [(A / "transport_diagnostics.py", [])],
        "weighted": [(A / "weighted_contrasts.py", [])],
        "support": [(A / "support_tables.py", [])],
        "sensitivity": [(A / "sensitivity_models.py", [])],
        "main_figures": [
            (A / "make_quantitative_figures.py", []),
            (
                S / "plot_transfer.py",
                ["--results", str(sensitivity), "--output", str(fig)],
            ),
            (
                S / "plot_increment.py",
                ["--reference", str(baseline), "--output", str(fig)],
            ),
        ],
        "diagnostic_figures": [(A / "make_diagnostic_figures.py", [])],
        "literature_figures": [(A / "plot_literature.py", [])],
        "tables": [(A / "export_tables.py", [])],
        "validation": [(A / "audit_analysis.py", []), (A / "validate_outputs.py", [])],
    }
    history = []
    record = out / "logs/pipeline_runs.json"
    if record.exists():
        history = json.loads(record.read_text())
    for stage in a.stages or STAGES:
        start = time.time()
        print("Running " + stage, flush=True)
        with (out / "logs" / f"{stage}.log").open("w", encoding="utf8") as log:
            for script, args in commands[stage]:
                result = subprocess.run(
                    [sys.executable, "-u", str(script), *args],
                    cwd=str(ROOT),
                    env=env,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                )
                if result.returncode:
                    print(
                        (out / "logs" / f"{stage}.log").read_text(encoding="utf8")[
                            -8000:
                        ],
                        flush=True,
                    )
                    raise SystemExit(
                        f"Stage {stage} failed; see {out}/logs/{stage}.log"
                    )
        history.append(
            {"stage": stage, "seconds": time.time() - start, "status": "passed"}
        )
        record.write_text(json.dumps(history, indent=2))
        print("Completed " + stage, flush=True)
    print("Results saved in " + str(out), flush=True)


if __name__ == "__main__":
    main()
