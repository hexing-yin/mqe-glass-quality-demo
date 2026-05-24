"""
Root cause stratification for Edge_Chipping on cover glass units.

After Pareto confirms the dominant defect mode, stratification breaks the
problem down by machine, fixture, shift, and process bins. This descriptive
MQE step reveals where the line fails most often before jumping to modeling.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

MIN_GROUP_SIZE = 500  # minimum sample size for ranking machines/fixtures


def project_root() -> Path:
    """Return repository root (parent of src/)."""
    return Path(__file__).resolve().parent.parent


def default_data_path() -> Path:
    return project_root() / "data" / "raw" / "cover_glass_synthetic.csv"


def load_data(path: Path) -> pd.DataFrame:
    """Load synthetic dataset; preserve 'None' as a valid defect label."""
    return pd.read_csv(path, keep_default_na=False)


def add_flags_and_bins(df: pd.DataFrame) -> pd.DataFrame:
    """Add Edge_Chipping flag and process bins used for stratification."""
    out = df.copy()

    out["Edge_Chipping"] = out["Defect_Type"] == "Edge_Chipping"
    out["NG"] = out["Final_Result"] == "NG"

    # Tool life bins — risk rises around 75% per project assumptions
    out["Tool_Life_Bin"] = pd.cut(
        out["Tool_Life_Pct"],
        bins=[0, 50, 75, 90, 100],
        labels=["Low_0_50", "Mid_50_75", "High_75_90", "Critical_90_100"],
        include_lowest=True,
        right=True,
    )

    # Coolant stability bins — unstable coolant amplifies wear-related chipping
    out["Coolant_Stability_Bin"] = pd.cut(
        out["Coolant_Pressure_Stability"],
        bins=[-float("inf"), 0.92, 0.96, float("inf")],
        labels=["Unstable", "Watch", "Stable"],
        right=False,
    )

    return out


def summarize_groups(
    df: pd.DataFrame,
    group_cols: list[str],
    group_type: str,
) -> pd.DataFrame:
    """Compute count and rate metrics for one grouping dimension."""
    summary = (
        df.groupby(group_cols, observed=False)
        .agg(
            Total_Count=("Glass_ID", "count"),
            NG_Count=("NG", "sum"),
            Edge_Chipping_Count=("Edge_Chipping", "sum"),
        )
        .reset_index()
    )

    summary["NG_Rate"] = (summary["NG_Count"] / summary["Total_Count"] * 100).round(2)
    summary["Edge_Chipping_Rate"] = (
        summary["Edge_Chipping_Count"] / summary["Total_Count"] * 100
    ).round(2)

    if len(group_cols) == 1:
        summary["Group_Value"] = summary[group_cols[0]].astype(str)
    else:
        summary["Group_Value"] = summary[group_cols[0]].astype(str)
        for col in group_cols[1:]:
            summary["Group_Value"] = summary["Group_Value"] + " | " + summary[col].astype(str)

    summary["Group_Type"] = group_type

    return summary[
        [
            "Group_Type",
            "Group_Value",
            "Total_Count",
            "NG_Count",
            "Edge_Chipping_Count",
            "NG_Rate",
            "Edge_Chipping_Rate",
        ]
    ]


def build_stratification_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Build combined stratification table for all requested groupings."""
    parts = [
        summarize_groups(df, ["Machine_ID"], "Machine_ID"),
        summarize_groups(df, ["Fixture_ID"], "Fixture_ID"),
        summarize_groups(df, ["Shift"], "Shift"),
        summarize_groups(df, ["Tool_Life_Bin"], "Tool_Life_Bin"),
        summarize_groups(df, ["Coolant_Stability_Bin"], "Coolant_Stability_Bin"),
        summarize_groups(
            df,
            ["Tool_Life_Bin", "Coolant_Stability_Bin"],
            "Tool_Life_Bin_x_Coolant_Stability_Bin",
        ),
        summarize_groups(
            df,
            ["Machine_ID", "Fixture_ID"],
            "Machine_ID_x_Fixture_ID",
        ),
    ]
    return pd.concat(parts, ignore_index=True)


def print_report(df: pd.DataFrame, summary: pd.DataFrame, output_path: Path) -> None:
    """Print concise stratification findings to stdout."""
    total_rows = len(df)
    ng_count = df["NG"].sum()
    ng_rate = ng_count / total_rows * 100
    chip_count = df["Edge_Chipping"].sum()
    chip_rate = chip_count / total_rows * 100

    print("--- Edge_Chipping Stratification Report (Simulated Data) ---")
    print(f"Total rows:            {total_rows:,}")
    print(f"NG rate:               {ng_rate:.2f}%")
    print(f"Edge_Chipping rate:    {chip_rate:.2f}%")
    print()

    machines = summary[
        (summary["Group_Type"] == "Machine_ID") & (summary["Total_Count"] >= MIN_GROUP_SIZE)
    ].sort_values("Edge_Chipping_Rate", ascending=False)
    print(f"Top 5 machines by Edge_Chipping_Rate (n >= {MIN_GROUP_SIZE}):")
    for _, row in machines.head(5).iterrows():
        print(
            f"  {row['Group_Value']}: {row['Edge_Chipping_Rate']:.2f}% "
            f"({int(row['Edge_Chipping_Count']):,}/{int(row['Total_Count']):,})"
        )
    print()

    fixtures = summary[
        (summary["Group_Type"] == "Fixture_ID") & (summary["Total_Count"] >= MIN_GROUP_SIZE)
    ].sort_values("Edge_Chipping_Rate", ascending=False)
    print(f"Top 5 fixtures by Edge_Chipping_Rate (n >= {MIN_GROUP_SIZE}):")
    for _, row in fixtures.head(5).iterrows():
        print(
            f"  {row['Group_Value']}: {row['Edge_Chipping_Rate']:.2f}% "
            f"({int(row['Edge_Chipping_Count']):,}/{int(row['Total_Count']):,})"
        )
    print()

    tool_bins = summary[summary["Group_Type"] == "Tool_Life_Bin"].sort_values("Group_Value")
    print("Edge_Chipping_Rate by Tool_Life_Bin:")
    for _, row in tool_bins.iterrows():
        print(f"  {row['Group_Value']}: {row['Edge_Chipping_Rate']:.2f}%")
    print()

    coolant_bins = summary[summary["Group_Type"] == "Coolant_Stability_Bin"].sort_values(
        "Group_Value"
    )
    print("Edge_Chipping_Rate by Coolant_Stability_Bin:")
    for _, row in coolant_bins.iterrows():
        print(f"  {row['Group_Value']}: {row['Edge_Chipping_Rate']:.2f}%")
    print()

    interaction = summary[
        summary["Group_Type"] == "Tool_Life_Bin_x_Coolant_Stability_Bin"
    ].sort_values("Edge_Chipping_Rate", ascending=False)
    worst = interaction.iloc[0]
    print("Worst Tool_Life_Bin + Coolant_Stability_Bin interaction:")
    print(
        f"  {worst['Group_Value']}: {worst['Edge_Chipping_Rate']:.2f}% "
        f"({int(worst['Edge_Chipping_Count']):,}/{int(worst['Total_Count']):,})"
    )
    print()
    print(f"Summary saved to: {output_path}")


def main() -> None:
    root = project_root()
    data_path = default_data_path()
    output_path = root / "outputs" / "reports" / "chipping_stratification_summary.csv"

    df = add_flags_and_bins(load_data(data_path))
    summary = build_stratification_summary(df)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(output_path, index=False)

    print_report(df, summary, output_path)


if __name__ == "__main__":
    main()
