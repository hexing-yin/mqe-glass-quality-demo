"""
Validate the synthetic cover glass quality dataset.

Checks schema, traceability, CTQ ranges, and Phase 1 story assumptions
before downstream Pareto, SPC, and root cause analysis.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

# Expected dataset size (from project plan)
TARGET_ROW_COUNT = 50_000
ROW_COUNT_TOLERANCE = 500  # allow small drift if generation logic changes slightly

# Columns that must be present for Phase 1 analysis
REQUIRED_COLUMNS = [
    "Glass_ID",
    "Lot_ID",
    "Product_Model",
    "Raw_Glass_Batch",
    "Line_ID",
    "Machine_ID",
    "Tool_ID",
    "Fixture_ID",
    "Operator_ID",
    "Shift",
    "Process_Time",
    "Inspection_Station",
    "Tool_Life_Pct",
    "Spindle_Speed_rpm",
    "Feed_Rate_mm_min",
    "Coolant_Pressure_bar",
    "Coolant_Pressure_Stability",
    "Vacuum_Level_kPa",
    "Chamfer_Width_mm",
    "Chipping_Size_um",
    "Thickness_mm",
    "Warpage_mm",
    "CS_MPa",
    "DOL_um",
    "Defect_Type",
    "Defect_Location",
    "AOI_Result",
    "Final_Result",
]

# Traceability and outcome fields must never be missing
KEY_NO_NULL_FIELDS = [
    "Glass_ID",
    "Lot_ID",
    "Machine_ID",
    "Tool_ID",
    "Fixture_ID",
    "Shift",
    "Process_Time",
    "Final_Result",
    "Defect_Type",
]


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str


def project_root() -> Path:
    """Return repository root (parent of src/)."""
    return Path(__file__).resolve().parent.parent


def default_data_path() -> Path:
    return project_root() / "data" / "raw" / "cover_glass_synthetic.csv"


def run_checks(df: pd.DataFrame, data_path: Path) -> list[CheckResult]:
    """Run all validation checks and return results."""
    results: list[CheckResult] = []

    # 1. File exists (checked before load; recorded here for the report)
    results.append(
        CheckResult(
            name="File exists",
            passed=data_path.is_file(),
            detail=str(data_path),
        )
    )

    # 2. Row count near 50,000 — confirms full dataset loaded for yield/SPC work
    row_count = len(df)
    row_ok = abs(row_count - TARGET_ROW_COUNT) <= ROW_COUNT_TOLERANCE
    results.append(
        CheckResult(
            name="Row count near 50,000",
            passed=row_ok,
            detail=f"{row_count:,} rows (target {TARGET_ROW_COUNT:,} ± {ROW_COUNT_TOLERANCE})",
        )
    )

    # 3. Required columns — missing fields would break analysis scripts
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    results.append(
        CheckResult(
            name="Required columns present",
            passed=len(missing) == 0,
            detail="All present" if not missing else f"Missing: {', '.join(missing)}",
        )
    )

    # 4. Glass_ID unique — one row per unit is required for traceability
    dup_count = df["Glass_ID"].duplicated().sum()
    results.append(
        CheckResult(
            name="Glass_ID is unique",
            passed=dup_count == 0,
            detail=f"{dup_count} duplicate(s)",
        )
    )

    # 5. Final_Result values — yield metrics assume OK / NG only
    final_values = set(df["Final_Result"].dropna().unique())
    final_ok = final_values <= {"OK", "NG"}
    results.append(
        CheckResult(
            name="Final_Result is OK or NG",
            passed=final_ok,
            detail=f"Found: {sorted(final_values)}",
        )
    )

    # 6. AOI_Result values — inspection gate uses Pass / Fail
    aoi_values = set(df["AOI_Result"].dropna().unique())
    aoi_ok = aoi_values <= {"Pass", "Fail"}
    results.append(
        CheckResult(
            name="AOI_Result is Pass or Fail",
            passed=aoi_ok,
            detail=f"Found: {sorted(aoi_values)}",
        )
    )

    # 7. Tool_Life_Pct range — invalid tool life breaks wear stratification
    tool_min, tool_max = df["Tool_Life_Pct"].min(), df["Tool_Life_Pct"].max()
    tool_ok = (df["Tool_Life_Pct"] >= 0).all() and (df["Tool_Life_Pct"] <= 100).all()
    results.append(
        CheckResult(
            name="Tool_Life_Pct between 0 and 100",
            passed=tool_ok,
            detail=f"Range: {tool_min:.1f} – {tool_max:.1f}",
        )
    )

    # 8. Chipping_Size_um non-negative — negative chip size is not physical
    chip_min = df["Chipping_Size_um"].min()
    chip_ok = (df["Chipping_Size_um"] >= 0).all()
    results.append(
        CheckResult(
            name="Chipping_Size_um is non-negative",
            passed=chip_ok,
            detail=f"Minimum: {chip_min:.1f} um",
        )
    )

    # 9. Chamfer width broad range — catches unit/scaling errors before capability study
    chamfer_min, chamfer_max = df["Chamfer_Width_mm"].min(), df["Chamfer_Width_mm"].max()
    chamfer_ok = ((df["Chamfer_Width_mm"] >= 0.20) & (df["Chamfer_Width_mm"] <= 0.40)).all()
    results.append(
        CheckResult(
            name="Chamfer_Width_mm in 0.20 – 0.40 mm",
            passed=chamfer_ok,
            detail=f"Range: {chamfer_min:.4f} – {chamfer_max:.4f} mm",
        )
    )

    # 10. Thickness broad range — catches gross data errors
    thick_min, thick_max = df["Thickness_mm"].min(), df["Thickness_mm"].max()
    thick_ok = ((df["Thickness_mm"] >= 0.65) & (df["Thickness_mm"] <= 0.75)).all()
    results.append(
        CheckResult(
            name="Thickness_mm in 0.65 – 0.75 mm",
            passed=thick_ok,
            detail=f"Range: {thick_min:.4f} – {thick_max:.4f} mm",
        )
    )

    # 11. NG rate — Phase 1 story assumes mostly OK parts with a realistic fail window
    ng_rate = (df["Final_Result"] == "NG").mean() * 100
    ng_ok = 2.0 <= ng_rate <= 6.0
    results.append(
        CheckResult(
            name="NG rate between 2% and 6%",
            passed=ng_ok,
            detail=f"NG rate: {ng_rate:.2f}%",
        )
    )

    # 12. Edge_Chipping top NG defect — confirms CNC chipping is the main fail mode
    ng_defects = df.loc[df["Final_Result"] == "NG", "Defect_Type"]
    top_defect = ng_defects.value_counts().idxmax() if len(ng_defects) else None
    top_count = ng_defects.value_counts().max() if len(ng_defects) else 0
    chip_top = top_defect == "Edge_Chipping"
    results.append(
        CheckResult(
            name="Edge_Chipping is top NG defect",
            passed=chip_top,
            detail=f"Top NG defect: {top_defect} ({top_count:,} units)",
        )
    )

    # 13. No missing key fields — traceability and yield analysis need complete records
    null_counts = {col: int(df[col].isna().sum()) for col in KEY_NO_NULL_FIELDS}
    total_nulls = sum(null_counts.values())
    results.append(
        CheckResult(
            name="No missing values in key fields",
            passed=total_nulls == 0,
            detail="None" if total_nulls == 0 else str(null_counts),
        )
    )

    return results


def print_report(df: pd.DataFrame, results: list[CheckResult]) -> None:
    """Print validation report to stdout."""
    print("=== Cover Glass Synthetic Data Validation ===\n")

    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] {result.name}")
        print(f"       {result.detail}")

    print("\n--- Dataset summary ---")
    print(f"Rows:          {len(df):,}")
    print(f"Columns:       {len(df.columns)}")
    ng_rate = (df["Final_Result"] == "NG").mean() * 100
    print(f"NG rate:       {ng_rate:.2f}%")
    print("Top defects (all units):")
    for defect, count in df["Defect_Type"].value_counts().head(5).items():
        print(f"  {defect}: {count:,}")

    all_passed = all(r.passed for r in results)
    print()
    if all_passed:
        print("Validation passed: synthetic dataset is ready for analysis.")
    else:
        failed = [r.name for r in results if not r.passed]
        print(f"Validation failed: {len(failed)} check(s) did not pass.")


def main() -> None:
    data_path = default_data_path()

    if not data_path.is_file():
        print("=== Cover Glass Synthetic Data Validation ===\n")
        print(f"[FAIL] File exists")
        print(f"       File not found: {data_path}")
        print("\nValidation failed: dataset file is missing.")
        sys.exit(1)

    df = pd.read_csv(
        data_path,
        parse_dates=["Process_Time"],
        keep_default_na=False,  # "None" is a valid defect category for OK units
    )
    results = run_checks(df, data_path)
    print_report(df, results)

    if not all(r.passed for r in results):
        sys.exit(1)


if __name__ == "__main__":
    main()
