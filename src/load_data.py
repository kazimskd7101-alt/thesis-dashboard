from pathlib import Path
from typing import Dict, Iterable, Optional, Tuple

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"

MASTER_CSV_CANDIDATES = [
    "dashboard_master.csv",
    "dashboard_master_400_app_ready.csv",
    "dashboard_master_app_ready_full.csv",
]
CONTRACT_SUMMARY_CSV = "dashboard_summary_by_contract.csv"
SPLIT_SUMMARY_CSV = "dashboard_summary_by_split.csv"
XAI_BUCKET_CSV = "dashboard_xai_quality_buckets.csv"

COLUMN_CANDIDATES = {
    "sample_id": ["sample_id"],
    "anchor_idx": ["anchor_idx", "idx", "sample_idx"],
    "anchor_time": ["anchor_time", "datetime", "timestamp", "time"],
    "trade_date": ["trade_date", "date"],
    "contract": ["contract", "symbol"],
    "split": ["split"],
    "label": ["label", "y_true", "true_label", "target"],
    "pred": ["pred", "y_pred", "prediction"],
    "cnn_p_up": ["cnn_p_up", "p_up", "prob_up", "prediction_probability"],
    "forward_return": ["forward_return", "forward_return_pct", "ret_fwd_20"],
    "xai_quality_score": ["xai_quality_score"],
    "xai_bucket": ["xai_bucket", "xai_quality_bucket"],
    "signal_bucket": ["signal_bucket"],
    "confidence_bucket": ["confidence_bucket"],
    "image_filename": ["image_filename", "filename", "image_file", "raw_image"],
    "is_correct": ["is_correct"],
    "error_type": ["error_type"],
}


def _first_existing(columns: Iterable[str], candidates: Iterable[str]) -> Optional[str]:
    column_set = set(columns)
    for candidate in candidates:
        if candidate in column_set:
            return candidate
    return None


def get_column_map(df: pd.DataFrame) -> Dict[str, Optional[str]]:
    return {key: _first_existing(df.columns, candidates) for key, candidates in COLUMN_CANDIDATES.items()}


def _read_csv_if_exists(path: Path) -> Optional[pd.DataFrame]:
    if path.exists():
        return pd.read_csv(path)
    return None


def _coerce_datetime_columns(df: pd.DataFrame, colmap: Dict[str, Optional[str]]) -> pd.DataFrame:
    df = df.copy()

    if colmap["anchor_time"] and colmap["anchor_time"] in df.columns:
        df[colmap["anchor_time"]] = pd.to_datetime(df[colmap["anchor_time"]], errors="coerce")

    if colmap["trade_date"] and colmap["trade_date"] in df.columns:
        df[colmap["trade_date"]] = pd.to_datetime(df[colmap["trade_date"]], errors="coerce").dt.date

    return df


def add_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    colmap = get_column_map(df)

    if colmap["label"]:
        df[colmap["label"]] = pd.to_numeric(df[colmap["label"]], errors="coerce")

    if colmap["pred"]:
        df[colmap["pred"]] = pd.to_numeric(df[colmap["pred"]], errors="coerce")

    if colmap["cnn_p_up"]:
        df[colmap["cnn_p_up"]] = pd.to_numeric(df[colmap["cnn_p_up"]], errors="coerce")

    if colmap["forward_return"]:
        df[colmap["forward_return"]] = pd.to_numeric(df[colmap["forward_return"]], errors="coerce")

    if colmap["xai_quality_score"]:
        df[colmap["xai_quality_score"]] = pd.to_numeric(df[colmap["xai_quality_score"]], errors="coerce")

    if colmap["cnn_p_up"] and not colmap["pred"]:
        df["pred"] = (df[colmap["cnn_p_up"]] >= 0.5).astype(int)
        colmap["pred"] = "pred"

    if colmap["label"] and colmap["pred"] and not colmap["is_correct"]:
        df["is_correct"] = df[colmap["label"]] == df[colmap["pred"]]

    if colmap["label"] and colmap["pred"] and not colmap["error_type"]:
        def classify_error(row):
            true_value = row[colmap["label"]]
            pred_value = row[colmap["pred"]]

            if pd.isna(true_value) or pd.isna(pred_value):
                return None

            true_value = int(true_value)
            pred_value = int(pred_value)

            if true_value == 1 and pred_value == 1:
                return "TP"
            if true_value == 0 and pred_value == 0:
                return "TN"
            if true_value == 0 and pred_value == 1:
                return "FP"
            if true_value == 1 and pred_value == 0:
                return "FN"
            return None

        df["error_type"] = df.apply(classify_error, axis=1)

    return _coerce_datetime_columns(df, get_column_map(df))


def _find_master_csv(data_dir: Path, master_candidates: Iterable[str]) -> Path:
    for filename in master_candidates:
        path = data_dir / filename
        if path.exists():
            return path
    searched = ", ".join(master_candidates)
    raise FileNotFoundError(f"Dashboard master CSV not found in {data_dir}. Expected one of: {searched}")


def load_dashboard_data(
    data_dir: Path = DATA_DIR,
    master_candidates: Iterable[str] = MASTER_CSV_CANDIDATES,
) -> Tuple[pd.DataFrame, Optional[pd.DataFrame], Optional[pd.DataFrame], Optional[pd.DataFrame], Path]:
    master_path = _find_master_csv(data_dir, master_candidates)
    master_df = pd.read_csv(master_path)

    contract_df = _read_csv_if_exists(data_dir / CONTRACT_SUMMARY_CSV)
    split_df = _read_csv_if_exists(data_dir / SPLIT_SUMMARY_CSV)
    xai_df = _read_csv_if_exists(data_dir / XAI_BUCKET_CSV)

    master_df = _coerce_datetime_columns(master_df, get_column_map(master_df))

    return master_df, contract_df, split_df, xai_df, ASSETS_DIR
