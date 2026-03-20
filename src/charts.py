from typing import Dict, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def chart_probability_over_time(df: pd.DataFrame, colmap: Dict[str, Optional[str]]):
    time_col = colmap.get("anchor_time")
    p_up_col = colmap.get("cnn_p_up")

    if not time_col or not p_up_col:
        return None

    plot_df = df[[time_col, p_up_col]].dropna().sort_values(time_col)
    if plot_df.empty:
        return None

    fig = px.line(plot_df, x=time_col, y=p_up_col, title="Predicted P(up) over time")
    fig.update_yaxes(title="P(up)", tickformat=".0%")
    fig.update_xaxes(title="Time")
    return fig


def chart_accuracy_by_contract(df: pd.DataFrame, colmap: Dict[str, Optional[str]]):
    contract_col = colmap.get("contract")
    label_col = colmap.get("label")
    pred_col = colmap.get("pred")

    if not contract_col or not label_col or not pred_col:
        return None

    plot_df = df[[contract_col, label_col, pred_col]].dropna().copy()
    if plot_df.empty:
        return None

    plot_df["correct"] = plot_df[label_col] == plot_df[pred_col]
    summary = (
        plot_df.groupby(contract_col)
        .agg(
            rows=(contract_col, "size"),
            accuracy=("correct", lambda s: s.mean() * 100),
        )
        .reset_index()
    )

    fig = px.bar(summary, x=contract_col, y="accuracy", text="rows", title="Accuracy by contract")
    fig.update_yaxes(title="Accuracy (%)")
    fig.update_xaxes(title="Contract")
    return fig


def chart_confusion_matrix(df: pd.DataFrame, colmap: Dict[str, Optional[str]]):
    label_col = colmap.get("label")
    pred_col = colmap.get("pred")

    if not label_col or not pred_col:
        return None

    plot_df = df[[label_col, pred_col]].dropna().copy()
    if plot_df.empty:
        return None

    cm = pd.crosstab(plot_df[label_col].astype(int), plot_df[pred_col].astype(int))
    cm = cm.reindex(index=[0, 1], columns=[0, 1], fill_value=0)

    fig = go.Figure(
        data=go.Heatmap(
            z=cm.values,
            x=["Pred 0", "Pred 1"],
            y=["True 0", "True 1"],
            text=cm.values,
            texttemplate="%{text}",
        )
    )
    fig.update_layout(title="Confusion matrix")
    return fig


def chart_xai_bucket_counts(df: pd.DataFrame, colmap: Dict[str, Optional[str]]):
    bucket_col = colmap.get("xai_bucket")
    if not bucket_col:
        return None

    plot_df = df[[bucket_col]].dropna().copy()
    if plot_df.empty:
        return None

    counts = plot_df[bucket_col].value_counts().reset_index()
    counts.columns = ["bucket", "rows"]

    fig = px.pie(counts, names="bucket", values="rows", title="XAI bucket share")
    return fig


def chart_signal_bucket_counts(df: pd.DataFrame, colmap: Dict[str, Optional[str]]):
    signal_col = colmap.get("signal_bucket")
    if not signal_col:
        return None

    plot_df = df[[signal_col]].dropna().copy()
    if plot_df.empty:
        return None

    counts = plot_df[signal_col].value_counts().reset_index()
    counts.columns = ["signal_bucket", "rows"]

    fig = px.bar(counts, x="signal_bucket", y="rows", title="Signal bucket counts")
    fig.update_xaxes(title="Signal bucket")
    fig.update_yaxes(title="Rows")
    return fig


def chart_forward_return_distribution(df: pd.DataFrame, colmap: Dict[str, Optional[str]]):
    return_col = colmap.get("forward_return")
    if not return_col:
        return None

    plot_df = df[[return_col]].dropna().copy()
    if plot_df.empty:
        return None

    fig = px.histogram(plot_df, x=return_col, nbins=40, title="Forward return distribution")
    fig.update_xaxes(title="Forward return")
    fig.update_yaxes(title="Rows")
    return fig
