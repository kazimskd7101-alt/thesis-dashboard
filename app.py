from pathlib import Path

import streamlit as st

from src.charts import (
    chart_accuracy_by_contract,
    chart_confusion_matrix,
    chart_forward_return_distribution,
    chart_probability_over_time,
    chart_signal_bucket_counts,
    chart_xai_bucket_counts,
)
from src.filters import render_filters
from src.image_browser import display_sample_images
from src.load_data import (
    DATA_DIR,
    MASTER_CSV_CANDIDATES,
    add_derived_columns,
    get_column_map,
    load_dashboard_data,
)

st.set_page_config(page_title="Intraday Decision Dashboard", layout="wide")


def render_kpis(df, colmap):
    accuracy = None
    avg_p_up = None
    avg_fwd_ret = None

    if colmap["label"] and colmap["pred"]:
        accuracy = (df[colmap["label"]] == df[colmap["pred"]]).mean() * 100

    if colmap["cnn_p_up"]:
        avg_p_up = df[colmap["cnn_p_up"]].mean() * 100

    if colmap["forward_return"]:
        avg_fwd_ret = df[colmap["forward_return"]].mean() * 100

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rows", f"{len(df):,}")
    c2.metric("Accuracy", "N/A" if accuracy is None else f"{accuracy:.1f}%")
    c3.metric("Avg P(up)", "N/A" if avg_p_up is None else f"{avg_p_up:.1f}%")
    c4.metric("Avg forward return", "N/A" if avg_fwd_ret is None else f"{avg_fwd_ret:.3f}%")


def render_summary_tables(contract_df, split_df, xai_df):
    with st.expander("Summary tables", expanded=False):
        if contract_df is not None and not contract_df.empty:
            st.markdown("**By contract**")
            st.dataframe(contract_df, use_container_width=True)

        if split_df is not None and not split_df.empty:
            st.markdown("**By split**")
            st.dataframe(split_df, use_container_width=True)

        if xai_df is not None and not xai_df.empty:
            st.markdown("**XAI quality buckets**")
            st.dataframe(xai_df, use_container_width=True)


def render_sample_browser(df, colmap, assets_dir: Path):
    st.subheader("Sample browser")

    sort_columns = [c for c in [colmap["anchor_time"], colmap["anchor_idx"]] if c]
    browse_df = df.sort_values(sort_columns).reset_index(drop=True) if sort_columns else df.reset_index(drop=True)

    options = list(range(len(browse_df)))

    def format_option(i: int) -> str:
        row = browse_df.iloc[i]
        parts = [str(i + 1)]
        if colmap["anchor_time"]:
            parts.append(str(row[colmap["anchor_time"]]))
        if colmap["contract"]:
            parts.append(str(row[colmap["contract"]]))
        if colmap["anchor_idx"]:
            parts.append(f"idx {row[colmap['anchor_idx']]}")
        return " | ".join(parts)

    selected_position = st.selectbox("Select sample", options=options, format_func=format_option)
    row = browse_df.iloc[selected_position]

    detail_order = [
        colmap["sample_id"],
        colmap["anchor_idx"],
        colmap["anchor_time"],
        colmap["trade_date"],
        colmap["contract"],
        colmap["split"],
        colmap["label"],
        colmap["pred"],
        colmap["cnn_p_up"],
        colmap["forward_return"],
        colmap["signal_bucket"],
        colmap["confidence_bucket"],
        colmap["xai_bucket"],
        colmap["xai_quality_score"],
        colmap["is_correct"],
        colmap["error_type"],
        colmap["image_filename"],
    ]
    detail_columns = [c for c in detail_order if c and c in browse_df.columns]
    st.dataframe(row[detail_columns].rename("value").to_frame(), use_container_width=True)

    display_sample_images(row=row, colmap=colmap, assets_dir=assets_dir)


def main():
    st.title("Intraday Decision Dashboard")
    st.caption("Minimal thesis dashboard for diagnostics and image/XAI browsing.")

    try:
        master_df, contract_df, split_df, xai_df, assets_dir = load_dashboard_data(
            data_dir=DATA_DIR,
            master_candidates=MASTER_CSV_CANDIDATES,
        )
    except FileNotFoundError as exc:
        st.error(str(exc))
        st.stop()
    except Exception as exc:
        st.error(f"Failed to load dashboard data: {exc}")
        st.stop()

    master_df = add_derived_columns(master_df)
    colmap = get_column_map(master_df)
    filtered_df = render_filters(master_df, colmap)

    if filtered_df.empty:
        st.warning("No rows match the selected filters.")
        st.stop()

    render_kpis(filtered_df, colmap)

    left, right = st.columns((2, 1))

    with left:
        fig = chart_probability_over_time(filtered_df, colmap)
        if fig is not None:
            st.plotly_chart(fig, use_container_width=True)

        fig = chart_accuracy_by_contract(filtered_df, colmap)
        if fig is not None:
            st.plotly_chart(fig, use_container_width=True)

        fig = chart_signal_bucket_counts(filtered_df, colmap)
        if fig is not None:
            st.plotly_chart(fig, use_container_width=True)

    with right:
        fig = chart_confusion_matrix(filtered_df, colmap)
        if fig is not None:
            st.plotly_chart(fig, use_container_width=True)

        fig = chart_xai_bucket_counts(filtered_df, colmap)
        if fig is not None:
            st.plotly_chart(fig, use_container_width=True)

        fig = chart_forward_return_distribution(filtered_df, colmap)
        if fig is not None:
            st.plotly_chart(fig, use_container_width=True)

    render_summary_tables(contract_df, split_df, xai_df)
    render_sample_browser(filtered_df, colmap, assets_dir)


if __name__ == "__main__":
    main()
