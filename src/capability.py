"""
Process capability analysis for Chamfer_Width_mm.

Cp/Cpk use within-subgroup variation (short-term, subgroup ranges).
Pp/Ppk use overall sample variation (long-term, includes drift between subgroups).

These are simulated diagnostic indicators — not certification metrics.
Control limits (SPC) and spec limits (LSL/USL) answer different questions.
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

# Within-subgroup estimation: consecutive subgroups of n=5, sigma_hat = Rbar / d2
SUBGROUP_SIZE = 5
D2_N5 = 2.326


def project_root() -> Path:
    """Return repository root (parent of src/)."""
    return Path(__file__).resolve().parent.parent


def default_data_path() -> Path:
    return project_root() / "data" / "raw" / "cover_glass_synthetic.csv"


def load_data(path: Path) -> pd.DataFrame:
    """Load synthetic dataset; preserve 'None' as a valid defect label."""
    return pd.read_csv(path, parse_dates=["Process_Time"], keep_default_na=False)


def estimate_sigma_within(values: pd.Series, process_times: pd.Series) -> float:
    """
    Estimate within-subgroup sigma from consecutive subgroups (n=5) sorted by time.

    Uses Rbar / d2 with d2 = 2.326 for n=5.
    """
    ordered = (
        pd.DataFrame({"value": values.to_numpy(), "time": process_times.to_numpy()})
        .sort_values("time")
        .reset_index(drop=True)
    )
    vals = ordered["value"].to_numpy()
    n_complete = (len(vals) // SUBGROUP_SIZE) * SUBGROUP_SIZE
    if n_complete < SUBGROUP_SIZE:
        return np.nan

    usable = vals[:n_complete].reshape(-1, SUBGROUP_SIZE)
    ranges = usable.max(axis=1) - usable.min(axis=1)
    r_bar = ranges.mean()
    return float(r_bar / D2_N5)


def cp_cpk_from_sigma(mean: float, sigma: float) -> tuple[float, float]:
    """Compute Cp and Cpk from a sigma estimate; return NaN if sigma invalid."""
    if sigma == 0 or np.isnan(sigma):
        return (np.nan, np.nan)
    cp = (USL - LSL) / (6 * sigma)
    cpk = min((USL - mean) / (3 * sigma), (mean - LSL) / (3 * sigma))
    return (round(cp, 3), round(cpk, 3))


def compute_capability(group_df: pd.DataFrame, group_name: str) -> dict:
    """Calculate capability metrics for one analysis group."""
    values = group_df["Chamfer_Width_mm"]
    count = len(values)
    mean = values.mean()
    std_overall = values.std(ddof=1) if count > 1 else 0.0
    std_within = estimate_sigma_within(values, group_df["Process_Time"])

    below_lsl = int((values < LSL).sum())
    above_usl = int((values > USL).sum())
    oos_rate = round((below_lsl + above_usl) / count * 100, 2) if count else np.nan

    # Cp/Cpk: within-subgroup sigma; Pp/Ppk: overall sigma
    cp, cpk = cp_cpk_from_sigma(mean, std_within)
    pp, ppk = cp_cpk_from_sigma(mean, std_overall)

    return {
        "Group_Name": group_name,
        "Count": count,
        "Mean": round(mean, 4),
        "Std_Overall": round(std_overall, 4) if count > 1 else 0.0,
        "Std_Within": round(std_within, 4) if not np.isnan(std_within) else np.nan,
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
    rows = [compute_capability(df.loc[mask], name) for name, mask in groups.items()]
    return pd.DataFrame(rows)


def plot_distribution_comparison(df: pd.DataFrame, output_path: Path) -> None:
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
    print("Note: Cp/Cpk use within-subgroup sigma (Rbar/d2, n=5); Pp/Ppk use overall sigma.")
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
