"""Matplotlib visualizations for the Used Car Prices Analytics project."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter

from .config import FIGURES_DIR
from .validation import DataValidationError, validate_required_columns


def _gbp_formatter(value: float, _position: int) -> str:
    return f"£{value:,.0f}"


def _format_gbp_axis(ax: Axes, axis: str = "y") -> None:
    formatter = FuncFormatter(_gbp_formatter)
    if axis == "x":
        ax.xaxis.set_major_formatter(formatter)
    else:
        ax.yaxis.set_major_formatter(formatter)


def _save_figure(figure: Figure, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.tight_layout()
    figure.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(figure)
    return path


def plot_average_price_by_fuel_type(summary: pd.DataFrame) -> tuple[Figure, Axes]:
    """Create the required Petrol/Diesel/Hybrid average-price bar chart."""

    validate_required_columns(summary, ["fuel_type", "average_price", "car_count"], context="fuel price plot input")
    order = ["Petrol", "Diesel", "Hybrid"]
    plot_data = summary.set_index("fuel_type").reindex(order).dropna(subset=["average_price"]).reset_index()
    if plot_data.empty:
        raise DataValidationError("fuel price plot has no required fuel categories with prices")
    figure, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(plot_data["fuel_type"], plot_data["average_price"], color=["#4C78A8", "#F58518", "#54A24B"][: len(plot_data)])
    ax.bar_label(bars, labels=[f"n={int(count):,}" for count in plot_data["car_count"]], padding=3, fontsize=9)
    ax.set_title("Average Used-Car Listing Price by Fuel Type")
    ax.set_xlabel("Fuel type")
    ax.set_ylabel("Average listing price (GBP)")
    _format_gbp_axis(ax)
    return figure, ax


def plot_mileage_vs_price(dataframe: pd.DataFrame, correlation: pd.DataFrame) -> tuple[Figure, Axes]:
    """Create the full-data mileage-price scatter plot."""

    validate_required_columns(dataframe, ["mileage", "price"], context="mileage-price plot input")
    validate_required_columns(correlation, ["pearson_correlation", "spearman_correlation", "observations"], context="correlation plot input")
    valid = dataframe[["mileage", "price"]].dropna(subset=["mileage", "price"])
    result = correlation.iloc[0]
    figure, ax = plt.subplots(figsize=(9, 6))
    ax.scatter(valid["mileage"], valid["price"], s=9, alpha=0.24, color="#4C78A8", rasterized=True)
    ax.set_title(
        f"Mileage vs Listing Price (Pearson r={result['pearson_correlation']:.3f}, n={int(result['observations']):,})"
    )
    ax.set_xlabel("Mileage (miles, source convention)")
    ax.set_ylabel("Listing price (GBP)")
    _format_gbp_axis(ax)
    ax.text(
        0.02,
        0.97,
        f"Spearman ρ={result['spearman_correlation']:.3f}\nAll valid records plotted: {len(valid):,}",
        transform=ax.transAxes,
        va="top",
        bbox={"boxstyle": "round", "facecolor": "white", "alpha": 0.8},
    )
    return figure, ax


def plot_car_count_by_transmission(summary: pd.DataFrame) -> tuple[Figure, Axes]:
    """Create a transmission listing-count bar chart."""

    validate_required_columns(summary, ["transmission", "car_count"], context="transmission count plot input")
    plot_data = summary.sort_values("car_count", ascending=False, kind="stable")
    figure, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(plot_data["transmission"], plot_data["car_count"], color="#72B7B2")
    ax.bar_label(bars, labels=[f"{int(value):,}" for value in plot_data["car_count"]], padding=3, fontsize=9)
    ax.set_title("Listing Count by Transmission")
    ax.set_xlabel("Transmission")
    ax.set_ylabel("Number of listings")
    return figure, ax


def plot_median_price_by_transmission(summary: pd.DataFrame) -> tuple[Figure, Axes]:
    """Create a separate transmission median-price bar chart."""

    validate_required_columns(summary, ["transmission", "median_price"], context="transmission median plot input")
    plot_data = summary.sort_values("median_price", ascending=False, kind="stable")
    figure, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(plot_data["transmission"], plot_data["median_price"], color="#E45756")
    ax.bar_label(bars, labels=[f"£{value:,.0f}" for value in plot_data["median_price"]], padding=3, fontsize=9)
    ax.set_title("Median Listing Price by Transmission")
    ax.set_xlabel("Transmission")
    ax.set_ylabel("Median listing price (GBP)")
    _format_gbp_axis(ax)
    return figure, ax


def plot_price_distribution_by_brand(dataframe: pd.DataFrame) -> tuple[Figure, Axes]:
    """Create a brand price box plot sorted by median price.

    Fliers are hidden only for readability; every source row remains in the
    dataset and in all analytical calculations.
    """

    validate_required_columns(dataframe, ["brand", "price"], context="brand box-plot input")
    medians = dataframe.groupby("brand", observed=False)["price"].median().sort_values()
    labels = medians.index.tolist()
    values = [dataframe.loc[dataframe["brand"].eq(brand), "price"].dropna() for brand in labels]
    figure, ax = plt.subplots(figsize=(11, 6))
    ax.boxplot(values, showfliers=False, patch_artist=True, boxprops={"facecolor": "#B279A2", "alpha": 0.7})
    ax.set_xticks(range(1, len(labels) + 1))
    ax.set_xticklabels(labels)
    ax.set_title("Price Distribution by Brand (outlier points hidden for readability; data retained)")
    ax.set_xlabel("Brand")
    ax.set_ylabel("Listing price (GBP)")
    _format_gbp_axis(ax)
    ax.tick_params(axis="x", rotation=35)
    return figure, ax


def plot_top_three_models(summary: pd.DataFrame) -> tuple[Figure, Axes]:
    """Create a horizontal bar chart for the three most common model labels."""

    validate_required_columns(summary, ["model", "listing_count"], context="top-model plot input")
    plot_data = summary.sort_values("listing_count", ascending=True, kind="stable")
    figure, ax = plt.subplots(figsize=(8, 5))
    bars = ax.barh(plot_data["model"], plot_data["listing_count"], color="#FF9DA6")
    ax.bar_label(bars, labels=[f"{int(value):,}" for value in plot_data["listing_count"]], padding=3, fontsize=9)
    ax.set_title("Three Most Common Model Labels")
    ax.set_xlabel("Number of listings")
    ax.set_ylabel("Model")
    return figure, ax


def plot_average_price_by_vehicle_age(summary: pd.DataFrame) -> tuple[Figure, Axes]:
    """Create an age-sorted average-price line chart."""

    validate_required_columns(summary, ["vehicle_age", "average_price"], context="age price plot input")
    plot_data = summary.sort_values("vehicle_age", kind="stable")
    figure, ax = plt.subplots(figsize=(10, 5))
    ax.plot(plot_data["vehicle_age"], plot_data["average_price"], marker="o", linewidth=1.8, color="#4C78A8")
    ax.set_title("Average Listing Price by Vehicle Age (reference year 2024)")
    ax.set_xlabel("Vehicle age (years as of 2024)")
    ax.set_ylabel("Average listing price (GBP)")
    _format_gbp_axis(ax)
    ax.set_xticks(plot_data["vehicle_age"])
    ax.tick_params(axis="x", rotation=45)
    return figure, ax


def plot_listing_count_by_brand(dataframe: pd.DataFrame) -> tuple[Figure, Axes]:
    """Create a brand listing-count chart to show dataset imbalance."""

    validate_required_columns(dataframe, ["brand"], context="brand count plot input")
    counts = dataframe["brand"].value_counts().sort_values(ascending=True)
    figure, ax = plt.subplots(figsize=(9, 6))
    bars = ax.barh(counts.index, counts.values, color="#59A14F")
    ax.bar_label(bars, labels=[f"{int(value):,}" for value in counts.values], padding=3, fontsize=8)
    ax.set_title("Listing Count by Brand")
    ax.set_xlabel("Number of listings")
    ax.set_ylabel("Brand")
    return figure, ax


def create_required_figures(
    dataframe: pd.DataFrame,
    outputs: dict[str, pd.DataFrame],
    *,
    output_dir: Path = FIGURES_DIR,
) -> dict[str, Path]:
    """Create and save every required Phase 6 figure."""

    output_dir.mkdir(parents=True, exist_ok=True)
    figure_specs: list[tuple[str, Any]] = [
        ("average_price_by_fuel_type.png", lambda: plot_average_price_by_fuel_type(outputs["price_by_fuel_type"])),
        ("mileage_vs_price_scatter.png", lambda: plot_mileage_vs_price(dataframe, outputs["mileage_price_correlation"])),
        ("car_count_by_transmission.png", lambda: plot_car_count_by_transmission(outputs["transmission_summary"])),
        ("median_price_by_transmission.png", lambda: plot_median_price_by_transmission(outputs["transmission_summary"])),
        ("price_distribution_by_brand.png", lambda: plot_price_distribution_by_brand(dataframe)),
        ("top_three_models.png", lambda: plot_top_three_models(outputs["top_models"])),
        ("average_price_by_vehicle_age.png", lambda: plot_average_price_by_vehicle_age(outputs["price_by_vehicle_age"])),
        ("listing_count_by_brand.png", lambda: plot_listing_count_by_brand(dataframe)),
    ]
    paths: dict[str, Path] = {}
    for filename, factory in figure_specs:
        figure, _ = factory()
        path = output_dir / filename
        _save_figure(figure, path)
        paths[filename] = path
    return paths
