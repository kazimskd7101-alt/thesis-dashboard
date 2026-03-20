from pathlib import Path
from typing import Dict, Optional

import pandas as pd
import streamlit as st


def _existing_path(path: Path) -> Optional[Path]:
    if path.exists() and path.is_file():
        return path
    return None


def _image_path(assets_dir: Path, relative_dir: str, filename: str) -> Optional[Path]:
    if not filename:
        return None
    return _existing_path(assets_dir / relative_dir / filename)


def display_sample_images(row: pd.Series, colmap: Dict[str, Optional[str]], assets_dir: Path):
    image_filename_col = colmap.get("image_filename")
    anchor_idx_col = colmap.get("anchor_idx")

    st.subheader("Images")

    if anchor_idx_col and anchor_idx_col in row.index:
        st.caption(f"anchor_idx: {row[anchor_idx_col]}")

    if not image_filename_col or image_filename_col not in row.index:
        st.info("No image filename column found.")
        return

    filename = row[image_filename_col]
    if pd.isna(filename):
        st.info("No image filename available for this row.")
        return

    raw_path = _image_path(assets_dir, "si_images_20bar_padded/test", str(filename))
    raw_overlay_path = _image_path(assets_dir, "si_xai_final/raw_overlay", str(filename))
    masked_overlay_path = _image_path(assets_dir, "si_xai_final/masked_overlay", str(filename))

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("**Raw image**")
        if raw_path is not None:
            st.image(str(raw_path), use_column_width=True)
        else:
            st.info("File not found in assets/si_images_20bar_padded/test/")

    with c2:
        st.markdown("**Raw overlay**")
        if raw_overlay_path is not None:
            st.image(str(raw_overlay_path), use_column_width=True)
        else:
            st.info("File not found in assets/si_xai_final/raw_overlay/")

    with c3:
        st.markdown("**Masked overlay**")
        if masked_overlay_path is not None:
            st.image(str(masked_overlay_path), use_column_width=True)
        else:
            st.info("File not found in assets/si_xai_final/masked_overlay/")
