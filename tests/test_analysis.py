import numpy as np
import pandas as pd
import pytest

from src.analysis import (
    calculate_mileage_price_correlation,
    filter_diesel_zero_tax,
    find_top_brand_model_pairs,
    find_top_models,
    summarize_by_transmission,
    summarize_price_by_fuel_type,
    summarize_price_by_vehicle_age,
)
from src.validation import DataValidationError


def fixture_dataframe():
    return pd.DataFrame(
        {
            "brand": ["Audi", "Audi", "BMW", "BMW", "BMW", "Ford"],
            "model": ["A1", "A1", "i3", "i3", "A1", "Focus"],
            "vehicle_age": [4, 5, 6, 7, 8, 9],
            "price": [10000, 12000, 20000, 22000, 14000, 8000],
            "transmission": ["Manual", "Manual", "Automatic", "Automatic", "Manual", "Manual"],
            "mileage": [1000, 2000, 3000, 4000, 5000, 6000],
            "fuel_type": ["Petrol", "Petrol", "Hybrid", "Hybrid", "Diesel", "Diesel"],
            "tax": [0, 100, 0, 20, 0, 10],
        }
    )


def test_mean_and_median_price_by_fuel_type():
    result = summarize_price_by_fuel_type(fixture_dataframe()).set_index("fuel_type")
    assert result.loc["Petrol", "car_count"] == 2
    assert result.loc["Petrol", "average_price"] == 11000
    assert result.loc["Petrol", "median_price"] == 11000
    assert result.loc["Hybrid", "median_price"] == 21000


def test_transmission_counts_and_medians():
    result = summarize_by_transmission(fixture_dataframe()).set_index("transmission")
    assert result.loc["Manual", "car_count"] == 4
    assert result.loc["Manual", "median_price"] == 11000
    assert result.loc["Automatic", "median_price"] == 21000


def test_diesel_zero_tax_requires_both_conditions():
    result = filter_diesel_zero_tax(fixture_dataframe())
    assert len(result) == 1
    assert result.iloc[0]["brand"] == "BMW"
    assert filter_diesel_zero_tax(fixture_dataframe().assign(tax=1)).empty


def test_top_models_and_brand_model_tie_breaking():
    dataframe = fixture_dataframe()
    raw_models = find_top_models(dataframe, n=3)
    assert raw_models["model"].tolist() == ["A1", "i3", "Focus"]
    pairs = find_top_brand_model_pairs(dataframe, n=3)
    assert pairs.iloc[0]["listing_count"] == 2
    assert pairs.iloc[0]["brand"] == "Audi"


def test_price_by_vehicle_age_is_sorted_and_aggregated():
    result = summarize_price_by_vehicle_age(fixture_dataframe())
    assert result["vehicle_age"].tolist() == [4, 5, 6, 7, 8, 9]
    assert result.loc[result.vehicle_age == 4, "average_price"].iloc[0] == 10000


def test_known_linear_correlation():
    dataframe = pd.DataFrame({"mileage": [1, 2, 3, 4], "price": [4, 3, 2, 1]})
    result = calculate_mileage_price_correlation(dataframe)
    assert result.loc[0, "observations"] == 4
    assert result.loc[0, "pearson_correlation"] == pytest.approx(-1.0)
    assert result.loc[0, "spearman_correlation"] == pytest.approx(-1.0)


def test_empty_correlation_result_has_predictable_schema():
    dataframe = fixture_dataframe().iloc[0:0]
    result = calculate_mileage_price_correlation(dataframe)
    assert result.columns.tolist() == ["pearson_correlation", "spearman_correlation", "observations"]
    assert result.loc[0, "observations"] == 0
    assert np.isnan(result.loc[0, "pearson_correlation"])


def test_missing_columns_raise_useful_errors():
    with pytest.raises(DataValidationError, match="missing required columns"):
        summarize_by_transmission(fixture_dataframe().drop(columns=["transmission"]))
