"""Deterministic cleaning and integration of the approved raw source files."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from .config import (
    CANONICAL_SOURCE_FILES,
    COLUMN_RENAME_MAP,
    INTERIM_DATA_DIR,
    PROCESSED_DATA_DIR,
    RAW_CANONICAL_COLUMNS,
    TABLES_DIR,
)
from .data_io import load_named_source
from .validation import (
    MIN_PLAUSIBLE_YEAR,
    convert_numeric_columns,
    identify_invalid_rows,
    validate_clean_dataframe,
    validate_required_columns,
)

SOURCE_REQUIRED_COLUMNS = (
    "model",
    "year",
    "price",
    "transmission",
    "mileage",
    "fuel_type",
    "tax",
    "mpg",
    "engine_size",
)
STRING_COLUMNS = ("model", "transmission", "fuel_type")
REJECTED_COLUMNS = (
    "source_file",
    "source_row_number",
    "brand",
    "model",
    "year",
    "price",
    "transmission",
    "mileage",
    "fuel_type",
    "tax",
    "mpg",
    "engine_size",
    "rejection_reason",
)


def _source_row_numbers(dataframe: pd.DataFrame) -> pd.Series:
    """Return one-based source row numbers, excluding the CSV header."""

    return pd.Series(range(1, len(dataframe) + 1), index=dataframe.index, dtype="int64")


def _cast_final_numeric_types(dataframe: pd.DataFrame) -> pd.DataFrame:
    result = dataframe.copy()
    for column in ("year", "price", "mileage", "tax"):
        result[column] = result[column].astype("int64")
    for column in ("mpg", "engine_size"):
        result[column] = result[column].astype("float64")
    return result


def clean_source(
    raw: pd.DataFrame,
    *,
    brand: str,
    source_file: str,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Clean one approved source and return accepted, rejected, and audit data.

    The function never mutates ``raw``. It keeps all rejected rows with their
    source filename, one-based source row number, normalized values, and a
    semicolon-separated rejection reason.
    """

    working = raw.rename(columns=COLUMN_RENAME_MAP).copy()
    validate_required_columns(working, SOURCE_REQUIRED_COLUMNS, context=source_file)
    working["source_file"] = source_file
    working["brand"] = brand
    working["source_row_number"] = _source_row_numbers(working)

    for column in STRING_COLUMNS:
        working[column] = working[column].astype("string").str.strip()

    working, conversion_failures = convert_numeric_columns(working)
    reasons = identify_invalid_rows(working, conversion_failures=conversion_failures)
    invalid_mask = reasons.ne("")

    rejected = working.loc[invalid_mask, [
        "source_file",
        "source_row_number",
        "brand",
        "model",
        "year",
        "price",
        "transmission",
        "mileage",
        "fuel_type",
        "tax",
        "mpg",
        "engine_size",
    ]].copy()
    rejected["rejection_reason"] = reasons.loc[invalid_mask].astype("string")
    rejected = rejected.reindex(columns=REJECTED_COLUMNS)

    accepted = working.loc[~invalid_mask, list(RAW_CANONICAL_COLUMNS)].copy()
    accepted = _cast_final_numeric_types(accepted)
    accepted = accepted.reindex(columns=RAW_CANONICAL_COLUMNS)

    duplicate_rows = int(working.loc[:, list(RAW_CANONICAL_COLUMNS)].duplicated().sum())
    summary = {
        "source_file": source_file,
        "brand": brand,
        "rows_before": len(raw),
        "rows_rejected": len(rejected),
        "duplicate_rows_identified": duplicate_rows,
        "duplicate_rows_removed": 0,
        "rows_after": len(accepted),
        "reconciliation_difference": len(raw) - len(rejected) - len(accepted),
        "reconciliation_status": "balanced" if len(raw) - len(rejected) == len(accepted) else "ERROR",
        "numeric_conversion_failures": len(conversion_failures),
    }
    return accepted, rejected, summary


def build_clean_dataset() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Build the canonical dataset from the explicit nine-source mapping."""

    clean_frames: list[pd.DataFrame] = []
    rejected_frames: list[pd.DataFrame] = []
    summary_records: list[dict[str, Any]] = []

    for source_file, brand in CANONICAL_SOURCE_FILES.items():
        raw = load_named_source(source_file)
        accepted, rejected, summary = clean_source(raw, brand=brand, source_file=source_file)
        clean_frames.append(accepted)
        rejected_frames.append(rejected)
        summary_records.append(summary)

    clean = pd.concat(clean_frames, ignore_index=True)
    rejected = pd.concat(rejected_frames, ignore_index=True) if rejected_frames else pd.DataFrame(columns=REJECTED_COLUMNS)
    clean = clean.reindex(columns=RAW_CANONICAL_COLUMNS)
    validate_clean_dataframe(clean)

    combined_before = sum(record["rows_before"] for record in summary_records)
    combined_rejected = sum(record["rows_rejected"] for record in summary_records)
    combined_duplicates = int(clean.duplicated(subset=list(RAW_CANONICAL_COLUMNS)).sum())
    summary_records.append(
        {
            "source_file": "canonical_combined",
            "brand": "multiple",
            "rows_before": combined_before,
            "rows_rejected": combined_rejected,
            "duplicate_rows_identified": combined_duplicates,
            "duplicate_rows_removed": 0,
            "rows_after": len(clean),
            "reconciliation_difference": combined_before - combined_rejected - len(clean),
            "reconciliation_status": "balanced" if combined_before - combined_rejected == len(clean) else "ERROR",
            "numeric_conversion_failures": sum(record["numeric_conversion_failures"] for record in summary_records),
        }
    )
    summary = pd.DataFrame(summary_records)
    return clean, rejected, summary


def write_clean_outputs(
    clean: pd.DataFrame,
    rejected: pd.DataFrame,
    summary: pd.DataFrame,
) -> dict[str, Path]:
    """Write canonical, rejected-row, and cleaning-summary outputs."""

    validate_clean_dataframe(clean)
    INTERIM_DATA_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)

    clean_path = PROCESSED_DATA_DIR / "used_cars_clean.csv"
    rejected_path = INTERIM_DATA_DIR / "rejected_rows.csv"
    summary_path = TABLES_DIR / "cleaning_summary.csv"
    clean.to_csv(clean_path, index=False)
    rejected.reindex(columns=REJECTED_COLUMNS).to_csv(rejected_path, index=False)
    summary.to_csv(summary_path, index=False)
    return {"clean": clean_path, "rejected": rejected_path, "summary": summary_path}
