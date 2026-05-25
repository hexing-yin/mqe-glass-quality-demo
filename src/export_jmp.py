"""
Export analysis outputs to an Excel workbook for JMP import.

JMP is used for interactive confirmatory analysis during interview demos.
This script packages Python-generated tables into one workbook for manual
import — it does not generate JMP scripts.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

RAW_ROW_LIMIT = 50_000

README_ROWS = [
    ("Purpose", "Synthetic cover glass quality data and analysis summaries for JMP import."),
    ("Data source", "All data is SIMULATED for portfolio and interview use only."),
    ("Not real data", "Does not represent any real company, supplier, or production line."),
    ("Usage", "Import sheets into JMP for manual / live-demo quality analysis."),
    ("Recommended JMP tools", "Distribution, Graph Builder, Fit Y by X, Control Chart Builder, Process Capability"),
    ("raw_data_sample", "Unit-level traceability, process, CTQ, and defect fields (up to 50,000 rows)."),
    ("defect_pareto", "NG defect type counts and cumulative percentages."),
    ("stratification_summary", "Edge_Chipping rates by machine, fixture, shift, and process bins."),
    ("spc_chamfer_xbar_r", "SPC: X-bar/R subgroup summary for chamfer width on CNC-04."),
    ("spc_chipping_imr", "SPC: I-MR values for chipping size on CNC-04 (exploratory; zero-inflated data)."),
    ("spc_chipping_p_chart", "SPC: p-chart subgroup summary for Edge_Chipping rate on CNC-04 (n=5)."),
    ("capability_summary", "Cp/Cpk/Pp/Ppk for chamfer width by process window."),
    ("defect_location_summary", "Edge_Chipping counts and rates by defect location."),
    ("ml_model_summary", "ML model comparison metrics (supporting screening tool only)."),
    ("high_risk_windows", "Grouped predicted vs actual Edge_Chipping risk by process window."),
]


def project_root() -> Path:
    """Return repository root (parent of src/)."""
    return Path(__file__).resolve().parent.parent


def build_readme_sheet() -> pd.DataFrame:
    """Create README sheet content."""
    return pd.DataFrame(README_ROWS, columns=["Topic", "Description"])


def load_raw_sample(path: Path) -> pd.DataFrame:
    """Load raw synthetic dataset (up to 50,000 rows)."""
    df = pd.read_csv(path, keep_default_na=False)
    return df.head(RAW_ROW_LIMIT)


def load_report(path: Path, sheet_name: str) -> pd.DataFrame | None:
    """Load a report CSV; return None and warn if missing."""
    if not path.is_file():
        print(f"WARNING: Missing report for sheet '{sheet_name}': {path}")
        return None
    return pd.read_csv(path)


def print_report(workbook_path: Path, sheet_counts: list[tuple[str, int]]) -> None:
    """Print concise export summary to stdout."""
    print("--- JMP Export Report ---")
    print(f"Workbook path: {workbook_path}")
    print("Sheets created:")
    for name, count in sheet_counts:
        print(f"  {name}: {count:,} rows")


def main() -> None:
    root = project_root()
    raw_path = root / "data" / "raw" / "cover_glass_synthetic.csv"
    reports_dir = root / "outputs" / "reports"
    workbook_path = reports_dir / "jmp_export_cover_glass_quality.xlsx"

    if not raw_path.is_file():
        print(f"ERROR: Raw dataset not found: {raw_path}")
        sys.exit(1)

    # Sheet name -> source file (None means built in code)
    sheet_sources: list[tuple[str, Path | None]] = [
        ("raw_data_sample", raw_path),
        ("defect_pareto", reports_dir / "defect_pareto.csv"),
        ("stratification_summary", reports_dir / "chipping_stratification_summary.csv"),
        ("spc_chamfer_xbar_r", reports_dir / "spc_chamfer_xbar_r_summary.csv"),
        ("spc_chipping_imr", reports_dir / "spc_chipping_imr_summary.csv"),
        ("spc_chipping_p_chart", reports_dir / "spc_chipping_p_chart_summary.csv"),
        ("capability_summary", reports_dir / "capability_summary.csv"),
        ("defect_location_summary", reports_dir / "defect_location_summary.csv"),
        ("ml_model_summary", reports_dir / "ml_risk_model_summary.csv"),
        ("high_risk_windows", reports_dir / "high_risk_windows.csv"),
    ]

    workbook_path.parent.mkdir(parents=True, exist_ok=True)
    sheet_counts: list[tuple[str, int]] = []

    with pd.ExcelWriter(workbook_path, engine="openpyxl") as writer:
        readme = build_readme_sheet()
        readme.to_excel(writer, sheet_name="README", index=False)
        sheet_counts.append(("README", len(readme)))

        raw_df = load_raw_sample(raw_path)
        raw_df.to_excel(writer, sheet_name="raw_data_sample", index=False)
        sheet_counts.append(("raw_data_sample", len(raw_df)))

        for sheet_name, source_path in sheet_sources[1:]:
            assert source_path is not None
            df = load_report(source_path, sheet_name)
            if df is not None:
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                sheet_counts.append((sheet_name, len(df)))

    print_report(workbook_path, sheet_counts)


if __name__ == "__main__":
    main()
