"""
SPC control charts for cover glass CNC quality metrics.

Control charts monitor process stability over time. Control limits are derived
from process variation (within-subgroup or moving-range spread)—they are NOT
the same as product specification limits (LSL/USL). A point outside control
limits suggests a special cause worth investigating.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# High-risk machine identified in stratification analysis
TARGET_MACHINE = "CNC-04"
SUBGROUP_SIZE = 5

# Standard X-bar/R constants for n=5
A2 = 0.577
D3 = 0.0
D4 = 2.114

# Standard I-MR constants
I_MR_FACTOR = 2.66
MR_UCL_FACTOR = 3.267

# I-MR sample size for readable chart
IMR_SAMPLE_SIZE = 500


def project_root() -> Path:
    """Return repository root (parent of src/)."""
    return Path(__file__).resolve().parent.parent


def default_data_path() -> Path:
    return project_root() / "data" / "raw" / "cover_glass_synthetic.csv"


def load_data(path: Path) -> pd.DataFrame:
    """Load synthetic dataset; preserve 'None' as a valid defect label."""
    return pd.read_csv(path, parse_dates=["Process_Time"], keep_default_na=False)


def filter_machine(df: pd.DataFrame, machine_id: str) -> pd.DataFrame:
    """Filter to one machine and sort by process time."""
    machine_df = df[df["Machine_ID"] == machine_id].copy()
    return machine_df.sort_values("Process_Time").reset_index(drop=True)


def build_xbar_r_subgroups(machine_df: pd.DataFrame) -> pd.DataFrame:
    """Build rational subgroups of size n=5 from consecutive sorted parts."""
    n_rows = len(machine_df)
    n_complete = (n_rows // SUBGROUP_SIZE) * SUBGROUP_SIZE
    usable = machine_df.iloc[:n_complete].copy()

    usable["Subgroup_ID"] = np.arange(len(usable)) // SUBGROUP_SIZE + 1

    subgroups = (
        usable.groupby("Subgroup_ID", as_index=False)
        .agg(
            Process_Time_Start=("Process_Time", "min"),
            Process_Time_End=("Process_Time", "max"),
            Xbar_Chamfer_Width_mm=("Chamfer_Width_mm", "mean"),
            R_Chamfer_Width_mm=("Chamfer_Width_mm", lambda x: x.max() - x.min()),
            Mean_Tool_Life_Pct=("Tool_Life_Pct", "mean"),
            Mean_Coolant_Pressure_Stability=("Coolant_Pressure_Stability", "mean"),
        )
        .round(
            {
                "Xbar_Chamfer_Width_mm": 4,
                "R_Chamfer_Width_mm": 4,
                "Mean_Tool_Life_Pct": 1,
                "Mean_Coolant_Pressure_Stability": 3,
            }
        )
    )

    # Process-derived control limits (not spec limits)
    xbar_cl = subgroups["Xbar_Chamfer_Width_mm"].mean()
    r_cl = subgroups["R_Chamfer_Width_mm"].mean()

    subgroups["Xbar_CL"] = round(xbar_cl, 4)
    subgroups["Xbar_UCL"] = round(xbar_cl + A2 * r_cl, 4)
    subgroups["Xbar_LCL"] = round(xbar_cl - A2 * r_cl, 4)
    subgroups["R_CL"] = round(r_cl, 4)
    subgroups["R_UCL"] = round(D4 * r_cl, 4)
    subgroups["R_LCL"] = round(D3 * r_cl, 4)

    subgroups["Xbar_OOC"] = (
        (subgroups["Xbar_Chamfer_Width_mm"] > subgroups["Xbar_UCL"])
        | (subgroups["Xbar_Chamfer_Width_mm"] < subgroups["Xbar_LCL"])
    )
    subgroups["R_OOC"] = (
        (subgroups["R_Chamfer_Width_mm"] > subgroups["R_UCL"])
        | (subgroups["R_Chamfer_Width_mm"] < subgroups["R_LCL"])
    )

    return subgroups


def build_imr_table(machine_df: pd.DataFrame) -> pd.DataFrame:
    """
    Build I-MR table from the latest consecutive records on one machine.

    Caveat: Chipping_Size_um is zero-inflated and right-skewed (mostly zeros,
    occasional large spikes). I-MR assumes approximate normality — use this
    chart as exploratory; a p-chart on defect rate is more appropriate.
    """
    sample = machine_df.tail(IMR_SAMPLE_SIZE).copy().reset_index(drop=True)
    sample["Individual_Chipping_um"] = sample["Chipping_Size_um"]
    sample["Moving_Range_Chipping_um"] = sample["Individual_Chipping_um"].diff().abs()

    i_cl = sample["Individual_Chipping_um"].mean()
    mr_bar = sample["Moving_Range_Chipping_um"].mean()

    sample["I_CL"] = round(i_cl, 2)
    sample["I_UCL"] = round(i_cl + I_MR_FACTOR * mr_bar, 2)
    sample["I_LCL"] = round(max(0.0, i_cl - I_MR_FACTOR * mr_bar), 2)
    sample["MR_CL"] = round(mr_bar, 2)
    sample["MR_UCL"] = round(MR_UCL_FACTOR * mr_bar, 2)
    sample["MR_LCL"] = 0.0

    sample["I_OOC"] = (
        (sample["Individual_Chipping_um"] > sample["I_UCL"])
        | (sample["Individual_Chipping_um"] < sample["I_LCL"])
    )
    sample["MR_OOC"] = (
        (sample["Moving_Range_Chipping_um"] > sample["MR_UCL"])
        | (sample["Moving_Range_Chipping_um"] < sample["MR_LCL"])
    )
    # First moving range has no prior point
    sample.loc[0, "MR_OOC"] = False

    return sample


def build_pchart_subgroups(machine_df: pd.DataFrame) -> pd.DataFrame:
    """
    Build p-chart subgroups for Edge_Chipping rate (n=5 consecutive parts).

    Each subgroup records defect count and proportion — better suited to
    zero-inflated defect data than I-MR on continuous chipping size.
    """
    n_rows = len(machine_df)
    n_complete = (n_rows // SUBGROUP_SIZE) * SUBGROUP_SIZE
    usable = machine_df.iloc[:n_complete].copy()
    usable["Edge_Chipping"] = (usable["Defect_Type"] == "Edge_Chipping").astype(int)
    usable["Subgroup_ID"] = np.arange(len(usable)) // SUBGROUP_SIZE + 1

    subgroups = (
        usable.groupby("Subgroup_ID", as_index=False)
        .agg(
            Process_Time_Start=("Process_Time", "min"),
            Process_Time_End=("Process_Time", "max"),
            Defect_Count=("Edge_Chipping", "sum"),
            Subgroup_Size=("Edge_Chipping", "count"),
        )
    )
    subgroups["P_Edge_Chipping"] = (
        subgroups["Defect_Count"] / subgroups["Subgroup_Size"]
    ).round(4)

    p_bar = subgroups["P_Edge_Chipping"].mean()
    # Standard p-chart limits for constant n=5
    sigma_p = np.sqrt(p_bar * (1 - p_bar) / SUBGROUP_SIZE)
    subgroups["P_CL"] = round(p_bar, 4)
    subgroups["P_UCL"] = round(min(1.0, p_bar + 3 * sigma_p), 4)
    subgroups["P_LCL"] = round(max(0.0, p_bar - 3 * sigma_p), 4)
    subgroups["P_OOC"] = (
        (subgroups["P_Edge_Chipping"] > subgroups["P_UCL"])
        | (subgroups["P_Edge_Chipping"] < subgroups["P_LCL"])
    )
    return subgroups


def plot_pchart(pchart: pd.DataFrame, output_path: Path) -> None:
    """
    Save p-chart for Edge_Chipping rate by subgroup.

    Preferred over I-MR for defect-rate monitoring when chipping size is
    zero-inflated and right-skewed.
    """
    fig, ax = plt.subplots(figsize=(12, 5))

    x = pchart["Subgroup_ID"]
    cl = pchart["P_CL"].iloc[0]
    ucl = pchart["P_UCL"].iloc[0]
    lcl = pchart["P_LCL"].iloc[0]

    ax.plot(x, pchart["P_Edge_Chipping"], marker="o", markersize=3, linewidth=0.8)
    ax.axhline(cl, color="green", linestyle="-", linewidth=1, label="CL")
    ax.axhline(ucl, color="red", linestyle="--", linewidth=1, label="UCL")
    ax.axhline(lcl, color="red", linestyle="--", linewidth=1, label="LCL")

    ooc = pchart[pchart["P_OOC"]]
    if not ooc.empty:
        ax.scatter(
            ooc["Subgroup_ID"],
            ooc["P_Edge_Chipping"],
            color="red",
            s=40,
            zorder=5,
            label="OOC",
        )

    ax.set_xlabel("Subgroup ID (time order)")
    ax.set_ylabel("Edge_Chipping Rate")
    ax.set_title(
        f"p-Chart — Edge_Chipping Rate ({TARGET_MACHINE}, n={SUBGROUP_SIZE}, Simulated Data)"
    )
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(bottom=0)

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def plot_xbar_r(subgroups: pd.DataFrame, output_path: Path) -> None:
    """Save two-panel X-bar and R chart."""
    fig, (ax_xbar, ax_r) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

    x = subgroups["Subgroup_ID"]
    cl = subgroups["Xbar_CL"].iloc[0]
    ucl = subgroups["Xbar_UCL"].iloc[0]
    lcl = subgroups["Xbar_LCL"].iloc[0]

    ax_xbar.plot(x, subgroups["Xbar_Chamfer_Width_mm"], marker="o", markersize=3, linewidth=0.8)
    ax_xbar.axhline(cl, color="green", linestyle="-", linewidth=1, label="CL")
    ax_xbar.axhline(ucl, color="red", linestyle="--", linewidth=1, label="UCL")
    ax_xbar.axhline(lcl, color="red", linestyle="--", linewidth=1, label="LCL")

    xbar_ooc = subgroups[subgroups["Xbar_OOC"]]
    if not xbar_ooc.empty:
        ax_xbar.scatter(
            xbar_ooc["Subgroup_ID"],
            xbar_ooc["Xbar_Chamfer_Width_mm"],
            color="red",
            s=40,
            zorder=5,
            label="OOC",
        )

    ax_xbar.set_ylabel("X-bar (mm)")
    ax_xbar.set_title(
        f"X-bar / R Chart — Chamfer Width ({TARGET_MACHINE}, Simulated Data)"
    )
    ax_xbar.legend(loc="upper right", fontsize=8)
    ax_xbar.grid(True, alpha=0.3)

    r_cl = subgroups["R_CL"].iloc[0]
    r_ucl = subgroups["R_UCL"].iloc[0]
    r_lcl = subgroups["R_LCL"].iloc[0]

    ax_r.plot(x, subgroups["R_Chamfer_Width_mm"], marker="o", markersize=3, linewidth=0.8)
    ax_r.axhline(r_cl, color="green", linestyle="-", linewidth=1, label="CL")
    ax_r.axhline(r_ucl, color="red", linestyle="--", linewidth=1, label="UCL")
    ax_r.axhline(r_lcl, color="red", linestyle="--", linewidth=1, label="LCL")

    r_ooc = subgroups[subgroups["R_OOC"]]
    if not r_ooc.empty:
        ax_r.scatter(
            r_ooc["Subgroup_ID"],
            r_ooc["R_Chamfer_Width_mm"],
            color="red",
            s=40,
            zorder=5,
            label="OOC",
        )

    ax_r.set_xlabel("Subgroup ID (time order)")
    ax_r.set_ylabel("Range (mm)")
    ax_r.legend(loc="upper right", fontsize=8)
    ax_r.grid(True, alpha=0.3)

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def plot_imr(imr: pd.DataFrame, output_path: Path) -> None:
    """Save two-panel I and MR chart."""
    fig, (ax_i, ax_mr) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

    x = range(len(imr))
    i_cl = imr["I_CL"].iloc[0]
    i_ucl = imr["I_UCL"].iloc[0]
    i_lcl = imr["I_LCL"].iloc[0]

    ax_i.plot(x, imr["Individual_Chipping_um"], marker="o", markersize=3, linewidth=0.8)
    ax_i.axhline(i_cl, color="green", linestyle="-", linewidth=1, label="CL")
    ax_i.axhline(i_ucl, color="red", linestyle="--", linewidth=1, label="UCL")
    ax_i.axhline(i_lcl, color="red", linestyle="--", linewidth=1, label="LCL")

    i_ooc = imr[imr["I_OOC"]]
    if not i_ooc.empty:
        ax_i.scatter(i_ooc.index, i_ooc["Individual_Chipping_um"], color="red", s=40, zorder=5)

    ax_i.set_ylabel("Chipping (um)")
    ax_i.set_title(
        f"I / MR Chart — Chipping Size ({TARGET_MACHINE}, latest {IMR_SAMPLE_SIZE}, Simulated)"
    )
    ax_i.legend(loc="upper right", fontsize=8)
    ax_i.grid(True, alpha=0.3)

    mr_cl = imr["MR_CL"].iloc[0]
    mr_ucl = imr["MR_UCL"].iloc[0]

    ax_mr.plot(x, imr["Moving_Range_Chipping_um"], marker="o", markersize=3, linewidth=0.8)
    ax_mr.axhline(mr_cl, color="green", linestyle="-", linewidth=1, label="CL")
    ax_mr.axhline(mr_ucl, color="red", linestyle="--", linewidth=1, label="UCL")
    ax_mr.axhline(0, color="red", linestyle="--", linewidth=1, label="LCL")

    mr_ooc = imr[imr["MR_OOC"]]
    if not mr_ooc.empty:
        ax_mr.scatter(mr_ooc.index, mr_ooc["Moving_Range_Chipping_um"], color="red", s=40, zorder=5)

    ax_mr.set_xlabel("Part index (time order)")
    ax_mr.set_ylabel("Moving Range (um)")
    ax_mr.legend(loc="upper right", fontsize=8)
    ax_mr.grid(True, alpha=0.3)

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def print_report(
    machine_id: str,
    machine_rows: int,
    subgroups: pd.DataFrame,
    imr: pd.DataFrame,
    pchart: pd.DataFrame,
    paths: dict[str, Path],
) -> None:
    """Print concise SPC summary to stdout."""
    print("--- SPC Control Chart Report (Simulated Data) ---")
    print(f"Machine analyzed:        {machine_id}")
    print(f"Rows on machine:         {machine_rows:,}")
    print(f"X-bar/R subgroups:       {len(subgroups):,}")
    print(f"X-bar OOC count:         {subgroups['Xbar_OOC'].sum():,}")
    print(f"R OOC count:             {subgroups['R_OOC'].sum():,}")
    print(f"I chart OOC count:       {imr['I_OOC'].sum():,}")
    print(f"MR chart OOC count:      {imr['MR_OOC'].sum():,}")
    print(f"p-chart OOC count:       {pchart['P_OOC'].sum():,}")
    print()
    print("Note: I-MR on Chipping_Size_um is exploratory — data are zero-inflated")
    print("      and right-skewed. Prefer p-chart for Edge_Chipping rate monitoring.")
    print(f"X-bar/R table:           {paths['xbar_csv']}")
    print(f"I-MR table:              {paths['imr_csv']}")
    print(f"p-chart table:           {paths['pchart_csv']}")
    print(f"X-bar/R chart:           {paths['xbar_fig']}")
    print(f"I-MR chart:              {paths['imr_fig']}")
    print(f"p-chart figure:          {paths['pchart_fig']}")


def main() -> None:
    root = project_root()
    paths = {
        "xbar_csv": root / "outputs" / "reports" / "spc_chamfer_xbar_r_summary.csv",
        "imr_csv": root / "outputs" / "reports" / "spc_chipping_imr_summary.csv",
        "pchart_csv": root / "outputs" / "reports" / "spc_chipping_p_chart_summary.csv",
        "xbar_fig": root / "outputs" / "figures" / "chamfer_xbar_r_chart.png",
        "imr_fig": root / "outputs" / "figures" / "chipping_imr_chart.png",
        "pchart_fig": root / "outputs" / "figures" / "spc_chipping_p_chart.png",
    }

    df = load_data(default_data_path())
    machine_df = filter_machine(df, TARGET_MACHINE)

    # Part A: X-bar/R on chamfer width
    subgroups = build_xbar_r_subgroups(machine_df)
    paths["xbar_csv"].parent.mkdir(parents=True, exist_ok=True)
    subgroups.to_csv(paths["xbar_csv"], index=False)
    plot_xbar_r(subgroups, paths["xbar_fig"])

    # Part B: I-MR on chipping size (latest 500 parts; exploratory only)
    imr = build_imr_table(machine_df)
    imr.to_csv(paths["imr_csv"], index=False)
    plot_imr(imr, paths["imr_fig"])

    # Part C: p-chart on Edge_Chipping rate (full machine history, n=5 subgroups)
    pchart = build_pchart_subgroups(machine_df)
    pchart.to_csv(paths["pchart_csv"], index=False)
    plot_pchart(pchart, paths["pchart_fig"])

    print_report(TARGET_MACHINE, len(machine_df), subgroups, imr, pchart, paths)


if __name__ == "__main__":
    main()
