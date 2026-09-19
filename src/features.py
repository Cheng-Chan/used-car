"""Feature engineering and descriptive EDA summaries for the clean dataset."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd

from .config import (
    PROCESSED_DATA_DIR,
    RAW_CANONICAL_COLUMNS,
    REFERENCE_YEAR,
    TABLES_DIR,
)
from .validation import DataValidationError, validate_required_columns

ENRICHED_COLUMNS = (
    "brand",
    "model",
    "year",
    "vehicle_age",
    "price",
    "transmission",
    "mileage",
    "fuel_type",
    "tax",
    "mpg",
    "engine_size",
    "source_file",
)
EDA_NUMERIC_COLUMNS = ("year", "vehicle_age", "price", "mileage", "tax", "mpg", "engine_size")


def add_vehicle_age(
    dataframe: pd.DataFrame,
    reference_year: int = REFERENCE_YEAR,
) -> pd.DataFrame:
    """Return a copy with ``vehicle_age = reference_year - year``.

    The assignment fixes the default reference year at 2024. Negative ages
    are rejected rather than clamped, and the input dataframe is never
    modified in place.
    """

    if not isinstance(reference_year, (int, np.integer)):
        raise TypeError("reference_year must be an integer")
    validate_required_columns(dataframe, ["year"], context="vehicle-age input")

    original_year = dataframe["year"]
    numeric_year = pd.to_numeric(original_year, errors="coerce")
    conversion_failures = numeric_year.isna() & original_year.notna()
    if conversion_failures.any():
        count = int(conversion_failures.sum())
        raise DataValidationError(f"vehicle-age input contains {count} non-numeric year value(s)")
    if numeric_year.isna().any():
        count = int(numeric_year.isna().sum())
        raise DataValidationError(f"vehicle-age input contains {count} missing year value(s)")
    if (numeric_year % 1 != 0).any():
        raise DataValidationError("vehicle-age input contains non-integer year value(s)")

    years = numeric_year.astype("int64")
    ages = pd.Series(reference_year, index=years.index, dtype="int64") - years
    if ages.lt(0).any():
        count = int(ages.lt(0).sum())
        raise DataValidationError(
            f"vehicle-age calculation produced {count} negative age(s) for reference year {reference_year}"
        )

    result = dataframe.copy()
    if "vehicle_age" in result.columns:
        result = result.drop(columns=["vehicle_age"])
    insert_position = result.columns.get_loc("year") + 1
    result.insert(insert_position, "vehicle_age", ages.astype("int64"))
    return result


def _numeric_series(dataframe: pd.DataFrame, column: str) -> pd.Series:
    original = dataframe[column]
    numeric = pd.to_numeric(original, errors="coerce")
    failures = numeric.isna() & original.notna()
    if failures.any():
        raise DataValidationError(f"EDA column {column!r} contains non-numeric values")
    return numeric


def _distribution_record(series: pd.Series) -> dict[str, Any]:
    values = series.dropna()
    if values.empty:
        return {
            "count": 0,
            "mean": np.nan,
            "median": np.nan,
            "standard_deviation": np.nan,
            "minimum": np.nan,
            "q1": np.nan,
            "q3": np.nan,
            "maximum": np.nan,
            "iqr": np.nan,
            "below_lower_iqr_count": 0,
            "above_upper_iqr_count": 0,
        }
    q1 = values.quantile(0.25)
    q3 = values.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    return {
        "count": int(values.count()),
        "mean": values.mean(),
        "median": values.median(),
        "standard_deviation": values.std(),
        "minimum": values.min(),
        "q1": q1,
        "q3": q3,
        "maximum": values.max(),
        "iqr": iqr,
        "below_lower_iqr_count": int(values.lt(lower).sum()),
        "above_upper_iqr_count": int(values.gt(upper).sum()),
    }


def summarize_numeric_distributions(
    dataframe: pd.DataFrame,
    columns: Iterable[str] = EDA_NUMERIC_COLUMNS,
) -> pd.DataFrame:
    """Return descriptive statistics and IQR review counts by numeric field."""

    records = []
    for column in columns:
        validate_required_columns(dataframe, [column], context="numeric EDA input")
        records.append({"column": column, **_distribution_record(_numeric_series(dataframe, column))})
    return pd.DataFrame(records)


def _group_numeric_summary(dataframe: pd.DataFrame, group_column: str, value_column: str) -> pd.DataFrame:
    validate_required_columns(dataframe, [group_column, value_column], context="grouped EDA input")
    working = dataframe[[group_column, value_column]].copy()
    working[value_column] = _numeric_series(working, value_column)
    grouped = working.groupby(group_column, dropna=False, observed=False)[value_column]
    result = grouped.agg(
        car_count="count",
        average=lambda values: values.mean(),
        median=lambda values: values.median(),
        standard_deviation=lambda values: values.std(),
        minimum=lambda values: values.min(),
        q1=lambda values: values.quantile(0.25),
        q3=lambda values: values.quantile(0.75),
        maximum=lambda values: values.max(),
    ).reset_index()
    result["iqr"] = result["q3"] - result["q1"]
    return result.sort_values(group_column, kind="stable").reset_index(drop=True)


def _category_counts(dataframe: pd.DataFrame, column: str) -> pd.DataFrame:
    validate_required_columns(dataframe, [column], context="categorical EDA input")
    return (
        dataframe[column]
        .value_counts(dropna=False)
        .rename_axis(column)
        .reset_index(name="listing_count")
    )


def build_eda_tables(dataframe: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Build the Phase 4 overview, distribution, category, and group tables."""

    validate_required_columns(dataframe, ENRICHED_COLUMNS, context="enriched EDA input")
    overview = pd.DataFrame(
        [
            {
                "listing_count": len(dataframe),
                "brand_count": dataframe["brand"].nunique(dropna=True),
                "unique_model_count": dataframe["model"].nunique(dropna=True),
                "year_min": _numeric_series(dataframe, "year").min(),
                "year_max": _numeric_series(dataframe, "year").max(),
                "vehicle_age_min": _numeric_series(dataframe, "vehicle_age").min(),
                "vehicle_age_max": _numeric_series(dataframe, "vehicle_age").max(),
            }
        ]
    )
    listing_count_by_brand = _category_counts(dataframe, "brand").rename(columns={"brand": "brand"})
    return {
        "dataset_overview": overview,
        "numeric_distribution_summary": summarize_numeric_distributions(dataframe),
        "fuel_type_distribution": _category_counts(dataframe, "fuel_type"),
        "transmission_distribution": _category_counts(dataframe, "transmission"),
        "listing_count_by_brand": listing_count_by_brand,
        "price_summary_by_brand": _group_numeric_summary(dataframe, "brand", "price"),
        "mileage_summary_by_brand": _group_numeric_summary(dataframe, "brand", "mileage"),
        "price_summary_by_fuel_type": _group_numeric_summary(dataframe, "fuel_type", "price"),
        "price_summary_by_transmission": _group_numeric_summary(dataframe, "transmission", "price"),
    }


def write_eda_outputs(
    enriched: pd.DataFrame,
    tables: dict[str, pd.DataFrame],
) -> dict[str, Path]:
    """Write the enriched dataset and Phase 4 EDA tables."""

    validate_required_columns(enriched, ENRICHED_COLUMNS, context="enriched output")
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    enriched_path = PROCESSED_DATA_DIR / "used_cars_enriched.csv"
    enriched.reindex(columns=ENRICHED_COLUMNS).to_csv(enriched_path, index=False)
    paths: dict[str, Path] = {"enriched": enriched_path}
    for name, table in tables.items():
        path = TABLES_DIR / f"{name}.csv"
        table.to_csv(path, index=False)
        paths[name] = path
    return paths
