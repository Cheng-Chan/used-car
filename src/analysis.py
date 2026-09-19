"""Reusable analytical functions for the required guiding exercises."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr

from .config import PROCESSED_DATA_DIR, TABLES_DIR
from .validation import DataValidationError, validate_required_columns


def _numeric_series(dataframe: pd.DataFrame, column: str) -> pd.Series:
    original = dataframe[column]
    numeric = pd.to_numeric(original, errors="coerce")
    failures = numeric.isna() & original.notna()
    if failures.any():
        raise DataValidationError(f"analysis column {column!r} contains non-numeric values")
    return numeric


def summarize_price_by_fuel_type(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Return price statistics for every observed fuel type."""

    validate_required_columns(dataframe, ["fuel_type", "price"], context="fuel-type price input")
    working = dataframe[["fuel_type", "price"]].copy()
    working["price"] = _numeric_series(working, "price")
    result = (
        working.groupby("fuel_type", dropna=False, observed=False)["price"]
        .agg(
            car_count="count",
            average_price="mean",
            median_price="median",
            minimum_price="min",
            maximum_price="max",
        )
        .reset_index()
    )
    return result.sort_values("fuel_type", kind="stable").reset_index(drop=True)


def required_fuel_type_summary(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Return the required Petrol, Diesel, and Hybrid rows explicitly."""

    required = ["Petrol", "Diesel", "Hybrid"]
    summary = summarize_price_by_fuel_type(dataframe).set_index("fuel_type")
    result = summary.reindex(required).reset_index()
    result["car_count"] = result["car_count"].fillna(0).astype("int64")
    result["category_present"] = result["car_count"].gt(0)
    return result


def calculate_mileage_price_correlation(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Calculate overall Pearson and Spearman mileage-price correlations."""

    validate_required_columns(dataframe, ["mileage", "price"], context="correlation input")
    working = dataframe[["mileage", "price"]].copy()
    working["mileage"] = _numeric_series(working, "mileage")
    working["price"] = _numeric_series(working, "price")
    valid = working.dropna(subset=["mileage", "price"])
    observations = len(valid)
    if observations < 2 or valid["mileage"].nunique() < 2 or valid["price"].nunique() < 2:
        pearson = np.nan
        spearman = np.nan
    else:
        pearson = float(pearsonr(valid["mileage"], valid["price"]).statistic)
        spearman = float(spearmanr(valid["mileage"], valid["price"]).statistic)
    return pd.DataFrame(
        [{
            "pearson_correlation": pearson,
            "spearman_correlation": spearman,
            "observations": observations,
        }]
    )


def calculate_mileage_price_correlation_by_brand(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Calculate the same correlations separately within each brand."""

    validate_required_columns(dataframe, ["brand", "mileage", "price"], context="brand correlation input")
    records: list[dict[str, Any]] = []
    for brand, group in dataframe.groupby("brand", dropna=False, observed=False, sort=True):
        correlation = calculate_mileage_price_correlation(group).iloc[0].to_dict()
        records.append({"brand": brand, **correlation})
    return pd.DataFrame(records).sort_values("brand", kind="stable").reset_index(drop=True)


def summarize_by_transmission(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Return listing count, median price, and mean price by transmission."""

    validate_required_columns(dataframe, ["transmission", "price"], context="transmission input")
    working = dataframe[["transmission", "price"]].copy()
    working["price"] = _numeric_series(working, "price")
    result = (
        working.groupby("transmission", dropna=False, observed=False)["price"]
        .agg(car_count="count", median_price="median", average_price="mean")
        .reset_index()
    )
    return result.sort_values("transmission", kind="stable").reset_index(drop=True)


def filter_diesel_zero_tax(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Return rows satisfying both ``fuel_type == Diesel`` and ``tax == 0``."""

    validate_required_columns(dataframe, ["fuel_type", "tax"], context="Diesel zero-tax input")
    tax = _numeric_series(dataframe, "tax")
    return dataframe.loc[dataframe["fuel_type"].eq("Diesel") & tax.eq(0)].copy()


def summarize_diesel_zero_tax(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Return count, percentage, and median metrics for the zero-tax subset."""

    validate_required_columns(dataframe, ["fuel_type", "tax", "price", "mileage"], context="Diesel zero-tax summary input")
    diesel = dataframe.loc[dataframe["fuel_type"].eq("Diesel")].copy()
    matching = filter_diesel_zero_tax(dataframe)
    diesel_count = len(diesel)
    return pd.DataFrame(
        [{
            "diesel_count": diesel_count,
            "zero_tax_count": len(matching),
            "zero_tax_percentage_of_diesel": len(matching) / diesel_count * 100 if diesel_count else np.nan,
            "median_price": _numeric_series(matching, "price").median() if len(matching) else np.nan,
            "median_mileage": _numeric_series(matching, "mileage").median() if len(matching) else np.nan,
        }]
    )


def summarize_diesel_zero_tax_by_brand(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Return Diesel zero-tax counts and medians by brand."""

    validate_required_columns(dataframe, ["brand", "price", "mileage"], context="Diesel zero-tax brand input")
    matching = filter_diesel_zero_tax(dataframe).copy()
    if matching.empty:
        return pd.DataFrame(columns=["brand", "car_count", "median_price", "median_mileage"])
    matching["price"] = _numeric_series(matching, "price")
    matching["mileage"] = _numeric_series(matching, "mileage")
    return (
        matching.groupby("brand", dropna=False, observed=False)
        .agg(car_count=("brand", "size"), median_price=("price", "median"), median_mileage=("mileage", "median"))
        .reset_index()
        .sort_values("brand", kind="stable")
        .reset_index(drop=True)
    )


def summarize_brand_price_distribution(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Return box-plot-ready price distribution statistics by brand."""

    validate_required_columns(dataframe, ["brand", "price"], context="brand price distribution input")
    working = dataframe[["brand", "price"]].copy()
    working["price"] = _numeric_series(working, "price")
    result = (
        working.groupby("brand", dropna=False, observed=False)["price"]
        .agg(car_count="count", minimum_price="min", q1_price=lambda values: values.quantile(0.25), median_price="median", q3_price=lambda values: values.quantile(0.75), maximum_price="max")
        .reset_index()
    )
    result["iqr_price"] = result["q3_price"] - result["q1_price"]
    return result.sort_values(["median_price", "brand"], ascending=[True, True], kind="stable").reset_index(drop=True)


def find_top_models(dataframe: pd.DataFrame, n: int = 3) -> pd.DataFrame:
    """Return the top raw model labels by listing count."""

    if n <= 0:
        raise ValueError("n must be positive")
    validate_required_columns(dataframe, ["model"], context="top-model input")
    result = dataframe["model"].value_counts(dropna=True).rename_axis("model").reset_index(name="listing_count")
    return result.sort_values(["listing_count", "model"], ascending=[False, True], kind="stable").head(n).reset_index(drop=True)


def find_top_brand_model_pairs(dataframe: pd.DataFrame, n: int = 3) -> pd.DataFrame:
    """Return top brand-model pairs with deterministic tie-breaking."""

    if n <= 0:
        raise ValueError("n must be positive")
    validate_required_columns(dataframe, ["brand", "model"], context="top brand-model input")
    result = dataframe.groupby(["brand", "model"], dropna=False, observed=False).size().reset_index(name="listing_count")
    return result.sort_values(["listing_count", "brand", "model"], ascending=[False, True, True], kind="stable").head(n).reset_index(drop=True)


def summarize_price_by_vehicle_age(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Return price statistics for every observed vehicle-age group."""

    validate_required_columns(dataframe, ["vehicle_age", "price"], context="vehicle-age price input")
    working = dataframe[["vehicle_age", "price"]].copy()
    working["vehicle_age"] = _numeric_series(working, "vehicle_age")
    working["price"] = _numeric_series(working, "price")
    result = (
        working.groupby("vehicle_age", dropna=False, observed=False)["price"]
        .agg(car_count="count", average_price="mean", median_price="median", minimum_price="min", maximum_price="max")
        .reset_index()
        .sort_values("vehicle_age", kind="stable")
        .reset_index(drop=True)
    )
    return result


def build_guiding_exercise_outputs(dataframe: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Build all Phase 5 analytical tables without rounding values."""

    filtered = filter_diesel_zero_tax(dataframe)
    return {
        "price_by_fuel_type": summarize_price_by_fuel_type(dataframe),
        "price_by_fuel_type_required": required_fuel_type_summary(dataframe),
        "mileage_price_correlation": calculate_mileage_price_correlation(dataframe),
        "mileage_price_correlation_by_brand": calculate_mileage_price_correlation_by_brand(dataframe),
        "transmission_summary": summarize_by_transmission(dataframe),
        "diesel_zero_tax_cars": filtered,
        "diesel_zero_tax_summary": summarize_diesel_zero_tax(dataframe),
        "diesel_zero_tax_by_brand": summarize_diesel_zero_tax_by_brand(dataframe),
        "brand_price_distribution": summarize_brand_price_distribution(dataframe),
        "top_models": find_top_models(dataframe),
        "top_brand_model_pairs": find_top_brand_model_pairs(dataframe),
        "price_by_vehicle_age": summarize_price_by_vehicle_age(dataframe),
    }


def write_guiding_exercise_outputs(outputs: dict[str, pd.DataFrame]) -> dict[str, Path]:
    """Write Phase 5 analytical tables to the reports directory."""

    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for name, table in outputs.items():
        filename = f"{name}.csv"
        path = TABLES_DIR / filename
        table.to_csv(path, index=False)
        paths[name] = path
    return paths
