"""
ML risk screening for Edge_Chipping on cover glass units.

Pre-/in-process screening model: predictors are process parameters and
traceability fields only — NOT CTQ outputs (chamfer, chipping size) or
inspection results, which would leak target information.

This model prioritizes which process windows deserve engineering review.
It supports — but does not replace — traceability, SPC, capability study,
DOE, and line validation. Do not use model output for automatic process control.

Note: default 0.5 classification threshold is often suboptimal for imbalanced
defect data; use predicted probabilities and PR-AUC for ranking windows.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

RANDOM_STATE = 42
MIN_WINDOW_COUNT = 100
TOP_FEATURES = 15

NUMERIC_FEATURES = [
    "Tool_Life_Pct",
    "Spindle_Speed_rpm",
    "Feed_Rate_mm_min",
    "Coolant_Pressure_bar",
    "Coolant_Pressure_Stability",
    "Vacuum_Level_kPa",
]

CATEGORICAL_FEATURES = [
    "Machine_ID",
    "Tool_ID",
    "Fixture_ID",
    "Shift",
]

FEATURE_COLUMNS = NUMERIC_FEATURES + CATEGORICAL_FEATURES

WINDOW_GROUP_COLS = [
    "Tool_Life_Bin",
    "Coolant_Stability_Bin",
    "Machine_ID",
    "Fixture_ID",
    "Shift",
]


def project_root() -> Path:
    """Return repository root (parent of src/)."""
    return Path(__file__).resolve().parent.parent


def default_data_path() -> Path:
    return project_root() / "data" / "raw" / "cover_glass_synthetic.csv"


def load_data(path: Path) -> pd.DataFrame:
    """Load synthetic dataset; preserve 'None' as a valid defect label."""
    return pd.read_csv(path, keep_default_na=False)


def add_target_and_bins(df: pd.DataFrame) -> pd.DataFrame:
    """Create model target and process window bins."""
    out = df.copy()
    out["Edge_Chipping"] = (out["Defect_Type"] == "Edge_Chipping").astype(int)
    out["NG"] = (out["Final_Result"] == "NG").astype(int)

    out["Tool_Life_Bin"] = pd.cut(
        out["Tool_Life_Pct"],
        bins=[0, 50, 75, 90, 100],
        labels=["Low_0_50", "Mid_50_75", "High_75_90", "Critical_90_100"],
        include_lowest=True,
        right=True,
    )
    out["Coolant_Stability_Bin"] = pd.cut(
        out["Coolant_Pressure_Stability"],
        bins=[-float("inf"), 0.92, 0.96, float("inf")],
        labels=["Unstable", "Watch", "Stable"],
        right=False,
    )
    return out


def build_preprocessor() -> ColumnTransformer:
    """Scale numeric features; one-hot encode traceability categories."""
    return ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), NUMERIC_FEATURES),
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                CATEGORICAL_FEATURES,
            ),
        ]
    )


def evaluate_model(name: str, y_true: np.ndarray, y_pred: np.ndarray, y_prob: np.ndarray) -> dict:
    """Compute classification metrics and confusion matrix cells (threshold = 0.5)."""
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    metrics = {
        "Model": name,
        "Accuracy": round(accuracy_score(y_true, y_pred), 4),
        "Precision": round(precision_score(y_true, y_pred, zero_division=0), 4),
        "Recall": round(recall_score(y_true, y_pred, zero_division=0), 4),
        "F1": round(f1_score(y_true, y_pred, zero_division=0), 4),
        "TN": int(tn),
        "FP": int(fp),
        "FN": int(fn),
        "TP": int(tp),
    }
    if len(np.unique(y_true)) > 1:
        metrics["ROC_AUC"] = round(roc_auc_score(y_true, y_prob), 4)
        metrics["PR_AUC"] = round(average_precision_score(y_true, y_prob), 4)
    else:
        metrics["ROC_AUC"] = np.nan
        metrics["PR_AUC"] = np.nan
    return metrics


def get_feature_names(preprocessor: ColumnTransformer) -> list[str]:
    """Readable feature names after preprocessing."""
    return list(preprocessor.get_feature_names_out())


def plot_feature_importance(
    feature_names: list[str],
    importances: np.ndarray,
    output_path: Path,
) -> pd.DataFrame:
    """Save bar chart of top Random Forest feature importances."""
    importance_df = (
        pd.DataFrame({"Feature": feature_names, "Importance": importances})
        .sort_values("Importance", ascending=False)
        .head(TOP_FEATURES)
    )

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(
        importance_df["Feature"][::-1],
        importance_df["Importance"][::-1],
        color="steelblue",
        edgecolor="black",
        linewidth=0.4,
    )
    ax.set_xlabel("Importance")
    ax.set_title(
        f"Top {TOP_FEATURES} Features — Random Forest Edge_Chipping Risk (Simulated Data)"
    )
    ax.grid(True, axis="x", alpha=0.3)
    fig.tight_layout()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150)
    plt.close(fig)

    return importance_df


def _summarize_windows(
    scored: pd.DataFrame,
    group_cols: list[str],
) -> pd.DataFrame:
    """Aggregate predicted and actual risk for one grouping level."""
    windows = (
        scored.groupby(group_cols, observed=False)
        .agg(
            Total_Count=("Glass_ID", "count"),
            Actual_Edge_Chipping_Rate=("Edge_Chipping", lambda x: round(x.mean() * 100, 2)),
            Mean_Predicted_Risk=("Predicted_Risk", lambda x: round(x.mean() * 100, 2)),
            NG_Rate=("NG", lambda x: round(x.mean() * 100, 2)),
        )
        .reset_index()
    )
    # Fill unused window dimensions with "All" for a consistent output schema
    for col in WINDOW_GROUP_COLS:
        if col not in windows.columns:
            windows[col] = "All"
    return windows[WINDOW_GROUP_COLS + [
        "Total_Count",
        "Actual_Edge_Chipping_Rate",
        "Mean_Predicted_Risk",
        "NG_Rate",
    ]]


def build_high_risk_windows(df: pd.DataFrame, predicted_risk: np.ndarray) -> pd.DataFrame:
    """
    Summarize predicted risk by engineering process windows.

    Uses several grouping levels (2-way through 5-way) because the highest-risk
    windows are visible at Tool_Life x Coolant level before splitting further.
    """
    scored = df.copy()
    scored["Predicted_Risk"] = predicted_risk

    grouping_levels = [
        ["Tool_Life_Bin", "Coolant_Stability_Bin"],
        ["Tool_Life_Bin", "Coolant_Stability_Bin", "Machine_ID"],
        ["Tool_Life_Bin", "Coolant_Stability_Bin", "Machine_ID", "Fixture_ID"],
        WINDOW_GROUP_COLS,
    ]

    windows = pd.concat(
        [_summarize_windows(scored, cols) for cols in grouping_levels],
        ignore_index=True,
    )
    windows = windows[windows["Total_Count"] >= MIN_WINDOW_COUNT]
    return windows.sort_values("Mean_Predicted_Risk", ascending=False)


def print_report(
    y: pd.Series,
    summary: pd.DataFrame,
    importance_df: pd.DataFrame,
    windows: pd.DataFrame,
    paths: dict[str, Path],
) -> None:
    """Print concise ML risk summary to stdout."""
    print("--- ML Edge_Chipping Risk Report (Simulated Data) ---")
    print("Predictors: process + traceability only (no CTQ measurement leakage).")
    print(f"Positive class rate:     {y.mean() * 100:.2f}%")
    print("Note: metrics at 0.5 threshold; PR-AUC better for imbalanced screening.")
    print()

    for _, row in summary.iterrows():
        print(f"{row['Model']}:")
        print(
            f"  Accuracy={row['Accuracy']}, Precision={row['Precision']}, "
            f"Recall={row['Recall']}, F1={row['F1']}"
        )
        print(f"  ROC-AUC={row['ROC_AUC']}, PR-AUC={row['PR_AUC']}")
        print(
            f"  Confusion matrix (0.5): TN={row['TN']}, FP={row['FP']}, "
            f"FN={row['FN']}, TP={row['TP']}"
        )
    print()

    print("Top 10 feature importances (Random Forest):")
    for _, row in importance_df.head(10).iterrows():
        print(f"  {row['Feature']}: {row['Importance']:.4f}")
    print()

    print(f"Top 10 high-risk windows (n >= {MIN_WINDOW_COUNT}):")
    for _, row in windows.head(10).iterrows():
        print(
            f"  {row['Tool_Life_Bin']} | {row['Coolant_Stability_Bin']} | "
            f"{row['Machine_ID']} | {row['Fixture_ID']} | {row['Shift']}: "
            f"pred={row['Mean_Predicted_Risk']:.2f}%, "
            f"actual={row['Actual_Edge_Chipping_Rate']:.2f}% "
            f"(n={int(row['Total_Count'])})"
        )
    print()
    print(f"Model summary:           {paths['model_summary']}")
    print(f"High-risk windows:       {paths['high_risk']}")
    print(f"Feature importance plot: {paths['importance_fig']}")


def main() -> None:
    root = project_root()
    paths = {
        "model_summary": root / "outputs" / "reports" / "ml_risk_model_summary.csv",
        "high_risk": root / "outputs" / "reports" / "high_risk_windows.csv",
        "importance_fig": root / "outputs" / "figures" / "ml_feature_importance.png",
    }

    df = add_target_and_bins(load_data(default_data_path()))
    X = df[FEATURE_COLUMNS]
    y = df["Edge_Chipping"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
    )

    preprocessor = build_preprocessor()

    log_pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            (
                "model",
                LogisticRegression(max_iter=1000, random_state=RANDOM_STATE, class_weight="balanced"),
            ),
        ]
    )
    rf_pipeline = Pipeline(
        steps=[
            ("preprocessor", build_preprocessor()),
            (
                "model",
                RandomForestClassifier(
                    n_estimators=200,
                    random_state=RANDOM_STATE,
                    class_weight="balanced",
                    n_jobs=-1,
                ),
            ),
        ]
    )

    log_pipeline.fit(X_train, y_train)
    rf_pipeline.fit(X_train, y_train)

    log_pred = log_pipeline.predict(X_test)
    log_prob = log_pipeline.predict_proba(X_test)[:, 1]
    rf_pred = rf_pipeline.predict(X_test)
    rf_prob = rf_pipeline.predict_proba(X_test)[:, 1]

    summary = pd.DataFrame(
        [
            evaluate_model("LogisticRegression", y_test.to_numpy(), log_pred, log_prob),
            evaluate_model("RandomForestClassifier", y_test.to_numpy(), rf_pred, rf_prob),
        ]
    )

    paths["model_summary"].parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(paths["model_summary"], index=False)

    rf_preprocessor = rf_pipeline.named_steps["preprocessor"]
    feature_names = get_feature_names(rf_preprocessor)
    importances = rf_pipeline.named_steps["model"].feature_importances_
    importance_df = plot_feature_importance(feature_names, importances, paths["importance_fig"])

    all_predicted_risk = rf_pipeline.predict_proba(X)[:, 1]
    windows = build_high_risk_windows(df, all_predicted_risk)
    windows.to_csv(paths["high_risk"], index=False)

    print_report(y, summary, importance_df, windows, paths)


if __name__ == "__main__":
    main()
