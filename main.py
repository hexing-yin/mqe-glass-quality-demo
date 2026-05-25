"""
Convenience runner for the full synthetic cover glass MQE analysis pipeline.

Runs data generation, validation, and all analysis modules in order.
Use individual src/*.py scripts when you only need one step.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow imports from src/ without installing as a package
SRC_DIR = Path(__file__).resolve().parent / "src"
sys.path.insert(0, str(SRC_DIR))

from capability import main as run_capability
from export_jmp import main as run_export_jmp
from generate_data import main as run_generate_data
from heatmap import main as run_heatmap
from ml_risk import main as run_ml_risk
from pareto import main as run_pareto
from spc import main as run_spc
from stratify import main as run_stratify
from validate_data import main as run_validate_data

PIPELINE = [
    ("Generate synthetic data", run_generate_data),
    ("Validate dataset", run_validate_data),
    ("Pareto analysis", run_pareto),
    ("Root cause stratification", run_stratify),
    ("SPC control charts", run_spc),
    ("Process capability", run_capability),
    ("Defect location heatmap", run_heatmap),
    ("ML risk screening", run_ml_risk),
    ("JMP export", run_export_jmp),
]


def run_pipeline() -> None:
    """Run each pipeline step; stop on first failure."""
    print("=== Cover Glass MQE Pipeline (Simulated Data) ===\n")

    for step_num, (step_name, step_main) in enumerate(PIPELINE, start=1):
        print(f"--- Step {step_num}/{len(PIPELINE)}: {step_name} ---")
        try:
            step_main()
        except SystemExit as exc:
            code = exc.code if exc.code is not None else 1
            if code != 0:
                print(f"\nPipeline stopped: step {step_num} failed ({step_name}).")
                sys.exit(code)
        except Exception as exc:
            print(f"\nPipeline stopped: step {step_num} failed ({step_name}).")
            print(f"Error: {exc}")
            sys.exit(1)
        print()

    print("=== Pipeline complete ===")


def main() -> None:
    run_pipeline()


if __name__ == "__main__":
    main()
