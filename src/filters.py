from typing import Dict, Optional

import pandas as pd
import streamlit as st


def _sorted_options(series: pd.Series):
    values = [value for value in series.dropna().unique().tolist()]
    return sorted(values)


def render_filters(df: pd.DataFrame, colmap: Dict[str, Optional[str]]) -> pd.DataFrame:
    filtered = df.copy()
    st.sidebar.header("Filters")

    split_col = colmap.get("split")
    contract_col = colmap.get("contract")
    xai_bucket_col = colmap.get("xai_bucket")
    signal_bucket_col = colmap.get("signal_bucket")
    confidence_bucket_col = colmap.get("confidence_bucket")
    anchor_time_col = colmap.get("anchor_time")

    if split_col and split_col in filtered.columns:
        options = _sorted_options(filtered[split_col])
        selected = st.sidebar.multiselect("Split", options, default=options)
        if not selected:
            return filtered.iloc[0:0]
        filtered = filtered[filtered[split_col].isin(selected)]

    if contract_col and contract_col in filtered.columns:
        options = _sorted_options(filtered[contract_col])
        selected = st.sidebar.multiselect("Contract", options, default=options)
        if not selected:
            return filtered.iloc[0:0]
        filtered = filtered[filtered[contract_col].isin(selected)]

    if xai_bucket_col and xai_bucket_col in filtered.columns:
        options = _sorted_options(filtered[xai_bucket_col])
        selected = st.sidebar.multiselect("XAI bucket", options, default=options)
        if not selected:
            return filtered.iloc[0:0]
        filtered = filtered[filtered[xai_bucket_col].isin(selected)]

    if signal_bucket_col and signal_bucket_col in filtered.columns:
        options = _sorted_options(filtered[signal_bucket_col])
        selected = st.sidebar.multiselect("Signal bucket", options, default=options)
        if not selected:
            return filtered.iloc[0:0]
        filtered = filtered[filtered[signal_bucket_col].isin(selected)]

    if confidence_bucket_col and confidence_bucket_col in filtered.columns:
        options = _sorted_options(filtered[confidence_bucket_col])
        selected = st.sidebar.multiselect("Confidence bucket", options, default=options)
        if not selected:
            return filtered.iloc[0:0]
        filtered = filtered[filtered[confidence_bucket_col].isin(selected)]

    if anchor_time_col and anchor_time_col in filtered.columns and filtered[anchor_time_col].notna().any():
        min_date = filtered[anchor_time_col].dt.date.min()
        max_date = filtered[anchor_time_col].dt.date.max()
        start_date, end_date = st.sidebar.date_input(
            "Date range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
        )
        filtered = filtered[
            (filtered[anchor_time_col].dt.date >= start_date)
            & (filtered[anchor_time_col].dt.date <= end_date)
        ]

    return filtered
