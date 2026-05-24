"""
Process capability analysis for Chamfer_Width_mm.

Cp asks: "Does the process spread fit inside the spec width?"
Cpk asks: "Is the process centered AND capable?" (accounts for mean shift)

These are simulated diagnostic metrics. Control limits (from SPC) describe
process stability; spec limits (LSL/USL) describe customer/product requirements.
They answer different questions.

Note: This version uses overall standard deviation for Cp, Cpk, Pp, and Ppk.
A later version could estimate within-subgroup sigma from X-bar/R data.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Simulated chamfer spec limits (illustrative, not proprietary)
LSL = 0.25
USL = 0.35
TARGET = 0.30

TOOL_WEAR_THRESHOLD = 75.0
STABLE_COOLANT_MIN = 0.96
UNSTABLE_COOLANT_MAX = 0.92

HIGH_RISK_MACHINE = "CNC-04"


def project_root() -> Path:
    """Return repository root (parent of src/)."""
    return Path(__file__).resolve().parent.parent


def default_data_path() -> Path:
    return project_root() / "data" / "raw" / "cover_glass_synthetic.csv"


def load_data(path: Path) -> pd.DataFrame:
    """Load synthetic dataset; preserve 'None' as a valid defect label."""
    return pd.read_csv(path, keep_default_na=False)


def safe_capability_indices(mean: float, std: float) -> tuple[float, float, float, float]:
    """
    Compute Cp, Cpk, Pp, Ppk using overall sigma.
    Returns NaN when std is zero (no variation to assess).
    """
    if std == 0 or np.isnan(std):
        return (np.nan, np.nan, np.nan, np.nan)

    cp = (USL - LSL) / (6 * std)
    cpu = (USL - mean) / (3 * std)
    cpl = (mean - LSL) / (3 * std)
    cpk = min(cpu, cpl)

    # First version: Pp/Ppk use same overall sigma as Cp/Cpk
    pp = cp
    ppk = cpk

    return (round(cp, 3), round(cpk, 3), round(pp, 3), round(ppk, 3))


def compute_capability(values: pd.Series, group_name: str) -> dict:
    """Calculate capability metrics for one analysis group."""
    count = len(values)
    mean = values.mean()
    std = values.std(ddof=1) if count > 1 else 0.0

    below_lsl = int((values < LSL).sum())
    above_usl = int((values > USL).sum())
    oos_rate = round((below_lsl + above_usl) / count * 100, 2) if count else np.nan

    cp, cpk, pp, ppk = safe_capability_indices(mean, std)

    return {
        "Group_Name": group_name,
        "Count": count,
        "Mean": round(mean, 4),
        "Std_Overall": round(std, 4) if count > 1 else 0.0,
        "LSL": LSL,
        "USL": USL,
        "Target": TARGET,
        "Cp": cp,
        "Cpk": cpk,
        "Pp": pp,
        "Ppk": ppk,
        "Below_LSL_Count": below_lsl,
        "Above_USL_Count": above_usl,
        "OOS_Rate": oos_rate,
    }


def define_groups(df: pd.DataFrame) -> dict[str, pd.Series]:
    """Return boolean masks for each capability analysis group."""
    return {
        "All_Data": pd.Series(True, index=df.index),
        "CNC_04": df["Machine_ID"] == HIGH_RISK_MACHINE,
        "Low_Tool_Life_Under_75": df["Tool_Life_Pct"] < TOOL_WEAR_THRESHOLD,
        "High_Tool_Life_75_plus": df["Tool_Life_Pct"] >= TOOL_WEAR_THRESHOLD,
        "Stable_Coolant": df["Coolant_Pressure_Stability"] >= STABLE_COOLANT_MIN,
        "Unstable_Coolant": df["Coolant_Pressure_Stability"] < UNSTABLE_COOLANT_MAX,
        "High_Tool_Life_75_plus_and_Unstable_Coolant": (
            (df["Tool_Life_Pct"] >= TOOL_WEAR_THRESHOLD)
            & (df["Coolant_Pressure_Stability"] < UNSTABLE_COOLANT_MAX)
        ),
        "Low_Risk_Baseline": (
            (df["Tool_Life_Pct"] < TOOL_WEAR_THRESHOLD)
            & (df["Coolant_Pressure_Stability"] >= STABLE_COOLANT_MIN)
        ),
    }


def build_capability_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Compute capability table for all defined groups."""
    groups = define_groups(df)
    rows = [
        compute_capability(df.loc[mask, "Chamfer_Width_mm"], name)
        for name, mask in groups.items()
    ]
    return pd.DataFrame(rows)


def plot_distribution_comparison(
    df: pd.DataFrame,
    output_path: Path,
) -> None:
    """Compare chamfer distributions for low-risk vs high-risk process windows."""
    groups = define_groups(df)
    low_risk = df.loc[groups["Low_Risk_Baseline"], "Chamfer_Width_mm"]
    high_risk = df.loc[
        groups["High_Tool_Life_75_plus_and_Unstable_Coolant"], "Chamfer_Width_mm"
    ]

    fig, ax = plt.subplots(figsize=(10, 6))
    bins = np.linspace(LSL - 0.02, USL + 0.02, 30)

    ax.hist(
        low_risk,
        bins=bins,
        alpha=0.6,
        label=f"Low_Risk_Baseline (n={len(low_risk):,})",
        color="steelblue",
        edgecolor="black",
        linewidth=0.4,
    )
    ax.hist(
        high_risk,
        bins=bins,
        alpha=0.6,
        label=f"High wear + unstable coolant (n={len(high_risk):,})",
        color="darkorange",
        edgecolor="black",
        linewidth=0.4,
    )

    ax.axvline(LSL, color="red", linestyle="--", linewidth=1.2, label=f"LSL ({LSL})")
    ax.axvline(TARGET, color="green", linestyle="-", linewidth=1.2, label=f"Target ({TARGET})")
    ax.axvline(USL, color="red", linestyle="--", linewidth=1.2, label=f"USL ({USL})")

    ax.set_xlabel("Chamfer Width (mm)")
    ax.set_ylabel("Count")
    ax.set_title("Chamfer Width Distribution — Low Risk vs High Risk (Simulated Data)")
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def print_report(summary: pd.DataFrame, csv_path: Path, fig_path: Path) -> None:
    """Print concise capability summary to stdout."""
    def row(name: str) -> pd.Series:
        return summary.loc[summary["Group_Name"] == name].iloc[0]

    all_data = row("All_Data")
    low_risk = row("Low_Risk_Baseline")
    high_risk = row("High_Tool_Life_75_plus_and_Unstable_Coolant")

    print("--- Process Capability Report (Simulated Data) ---")
    print(f"Spec limits:             LSL={LSL}, Target={TARGET}, USL={USL} mm")
    print()
    print(f"All_Data:                Cpk={all_data['Cpk']}, Ppk={all_data['Ppk']}, "
          f"OOS={all_data['OOS_Rate']}%")
    print(f"Low_Risk_Baseline:       Cpk={low_risk['Cpk']}, Ppk={low_risk['Ppk']}, "
          f"OOS={low_risk['OOS_Rate']}%")
    print(f"High wear + unstable:    Cpk={high_risk['Cpk']}, Ppk={high_risk['Ppk']}, "
          f"OOS={high_risk['OOS_Rate']}%")
    print()
    print(f"Capability table:        {csv_path}")
    print(f"Distribution figure:     {fig_path}")


def main() -> None:
    root = project_root()
    csv_path = root / "outputs" / "reports" / "capability_summary.csv"
    fig_path = root / "outputs" / "figures" / "chamfer_capability_distribution.png"

    df = load_data(default_data_path())
    summary = build_capability_summary(df)

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(csv_path, index=False)

    plot_distribution_comparison(df, fig_path)
    print_report(summary, csv_path, fig_path)


if __name__ == "__main__":
    main()
