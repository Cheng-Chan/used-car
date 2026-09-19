"""Validation helpers for source schemas, numeric conversion, and row rules."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import pandas as pd

from .config import NUMERIC_COLUMNS, RAW_CANONICAL_COLUMNS, REFERENCE_YEAR

MIN_PLAUSIBLE_YEAR = 1970


class DataValidationError(ValueError):
    """Raised when a dataframe cannot satisfy a required data contract."""


def validate_required_columns(
    dataframe: pd.DataFrame,
    required_columns: Sequence[str],
    *,
    context: str = "dataframe",
) -> None:
    """Raise a useful error when required columns are absent."""

    missing = [column for column in required_columns if column not in dataframe.columns]
    if missing:
        available = ", ".join(map(str, dataframe.columns))
        raise DataValidationError(
            f"{context} is missing required columns: {missing}. Available columns: [{available}]"
        )


def convert_numeric_columns(
    dataframe: pd.DataFrame,
    columns: Sequence[str] = NUMERIC_COLUMNS,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Convert numeric fields and separately record failed conversions.

    ``errors='coerce'`` is used only together with a failure table that retains
    the source row index, field name, and original value.
    """

    result = dataframe.copy()
    failures: list[dict[str, Any]] = []
    for column in columns:
        if column not in result.columns:
            continue
        original = result[column]
        converted = pd.to_numeric(original, errors="coerce")
        failed = converted.isna() & original.notna()
        for row_index in result.index[failed]:
            failures.append(
                {
                    "row_index": row_index,
                    "column": column,
                    "original_value": original.loc[row_index],
                }
            )
        result[column] = converted
    return result, pd.DataFrame(failures, columns=["row_index", "column", "original_value"])


def identify_invalid_rows(
    dataframe: pd.DataFrame,
    *,
    conversion_failures: pd.DataFrame | None = None,
    min_year: int = MIN_PLAUSIBLE_YEAR,
    reference_year: int = REFERENCE_YEAR,
) -> pd.Series:
    """Return a reason string for each row violating an explicit rule."""

    reasons: dict[Any, list[str]] = {index: [] for index in dataframe.index}

    def add_reason(mask: pd.Series, message: str) -> None:
        for index in dataframe.index[mask.fillna(False)]:
            reasons[index].append(message)

    if conversion_failures is not None and not conversion_failures.empty:
        for row_index, group in conversion_failures.groupby("row_index", sort=False):
            if row_index in reasons:
                fields = ", ".join(group["column"].astype(str))
                reasons[row_index].append(f"numeric conversion failed: {fields}")

    for column in RAW_CANONICAL_COLUMNS:
        if column == "source_file":
            continue
        if column in dataframe.columns:
            add_reason(dataframe[column].isna(), f"missing required value: {column}")

    rules = {
        "price": (lambda series: series <= 0, "price must be greater than 0"),
        "mileage": (lambda series: series < 0, "mileage must be non-negative"),
        "tax": (lambda series: series < 0, "tax must be non-negative"),
        "mpg": (lambda series: series < 0, "mpg must be non-negative"),
        "engine_size": (lambda series: series < 0, "engine_size must be non-negative"),
        "year": (lambda series: series < min_year, f"year must be at least {min_year}"),
    }
    for column, (predicate, message) in rules.items():
        if column in dataframe.columns:
            add_reason(predicate(dataframe[column]), message)
    if "year" in dataframe.columns:
        add_reason(dataframe["year"] > reference_year, f"year must not exceed reference year {reference_year}")

    return pd.Series(
        ["; ".join(reasons[index]) for index in dataframe.index],
        index=dataframe.index,
        name="rejection_reason",
        dtype="string",
    )


def validate_clean_dataframe(
    dataframe: pd.DataFrame,
    *,
    min_year: int = MIN_PLAUSIBLE_YEAR,
    reference_year: int = REFERENCE_YEAR,
) -> None:
    """Validate a final canonical dataframe and raise on any invalid rows."""

    validate_required_columns(dataframe, RAW_CANONICAL_COLUMNS, context="clean canonical dataframe")
    if dataframe[list(RAW_CANONICAL_COLUMNS)].isna().any().any():
        raise DataValidationError("clean canonical dataframe contains missing required values")
    reasons = identify_invalid_rows(dataframe, min_year=min_year, reference_year=reference_year)
    invalid_count = int(reasons.ne("").sum())
    if invalid_count:
        examples = reasons[reasons.ne("")].head(3).tolist()
        raise DataValidationError(f"clean canonical dataframe contains {invalid_count} invalid rows: {examples}")
