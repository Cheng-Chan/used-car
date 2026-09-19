import pandas as pd
import pytest

from src.features import add_vehicle_age, build_eda_tables
from src.validation import DataValidationError


def test_vehicle_age_uses_fixed_reference_year_and_integer_type():
    raw = pd.DataFrame({"brand": ["Audi", "BMW"], "year": [2020, 2010], "price": [1, 2]})
    enriched = add_vehicle_age(raw)
    assert enriched["vehicle_age"].tolist() == [4, 14]
    assert str(enriched["vehicle_age"].dtype) == "int64"
    assert enriched.columns.tolist() == ["brand", "year", "vehicle_age", "price"]


def test_vehicle_age_does_not_use_current_year():
    raw = pd.DataFrame({"year": [2024]})
    assert add_vehicle_age(raw, reference_year=2024).loc[0, "vehicle_age"] == 0
    assert add_vehicle_age(raw, reference_year=2030).loc[0, "vehicle_age"] == 6


def test_negative_vehicle_age_is_rejected():
    with pytest.raises(DataValidationError, match="negative age"):
        add_vehicle_age(pd.DataFrame({"year": [2025]}))


def test_vehicle_age_does_not_mutate_input():
    raw = pd.DataFrame({"year": [2020]})
    original = raw.copy(deep=True)
    result = add_vehicle_age(raw)
    pd.testing.assert_frame_equal(raw, original)
    assert "vehicle_age" not in raw.columns
    assert "vehicle_age" in result.columns


def test_vehicle_age_rejects_missing_or_non_integer_years():
    with pytest.raises(DataValidationError, match="non-numeric"):
        add_vehicle_age(pd.DataFrame({"year": ["unknown"]}))
    with pytest.raises(DataValidationError, match="non-integer"):
        add_vehicle_age(pd.DataFrame({"year": [2020.5]}))


def test_eda_tables_include_required_distributions_and_summaries():
    dataframe = pd.DataFrame(
        {
            "brand": ["Audi", "BMW"],
            "model": ["A1", "i3"],
            "year": [2020, 2010],
            "vehicle_age": [4, 14],
            "price": [10000, 20000],
            "transmission": ["Manual", "Automatic"],
            "mileage": [1000, 2000],
            "fuel_type": ["Petrol", "Electric"],
            "tax": [0, 100],
            "mpg": [50.0, 100.0],
            "engine_size": [1.0, 0.0],
            "source_file": ["audi.csv", "bmw.csv"],
        }
    )
    tables = build_eda_tables(dataframe)
    assert tables["dataset_overview"].loc[0, "listing_count"] == 2
    assert "median" in tables["numeric_distribution_summary"].columns
    assert set(tables["price_summary_by_brand"]["brand"]) == {"Audi", "BMW"}
