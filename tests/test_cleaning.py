import pandas as pd
import pytest

from src.cleaning import clean_source
from src.config import RAW_CANONICAL_COLUMNS
from src.validation import DataValidationError


def valid_raw(**overrides):
    row = {
        "model": " A1",
        "year": "2020",
        "price": "12000",
        "transmission": "Manual ",
        "mileage": "1000",
        "fuelType": " Petrol",
        "tax": "0",
        "mpg": "55.4",
        "engineSize": "1.4",
    }
    row.update(overrides)
    return pd.DataFrame([row])


def test_clean_source_normalizes_strings_and_preserves_zero_tax():
    cleaned, rejected, summary = clean_source(valid_raw(), brand="Audi", source_file="audi.csv")
    assert rejected.empty
    assert cleaned.columns.tolist() == list(RAW_CANONICAL_COLUMNS)
    assert cleaned.loc[0, "brand"] == "Audi"
    assert cleaned.loc[0, "model"] == "A1"
    assert cleaned.loc[0, "transmission"] == "Manual"
    assert cleaned.loc[0, "fuel_type"] == "Petrol"
    assert cleaned.loc[0, "tax"] == 0
    assert summary["reconciliation_status"] == "balanced"


def test_negative_values_and_future_year_are_rejected_with_reasons():
    raw = pd.concat(
        [
            valid_raw(price="-1"),
            valid_raw(mileage="-10"),
            valid_raw(year="2060"),
        ],
        ignore_index=True,
    )
    cleaned, rejected, summary = clean_source(raw, brand="Audi", source_file="audi.csv")
    assert cleaned.empty
    assert len(rejected) == 3
    assert "price must be greater than 0" in rejected.loc[0, "rejection_reason"]
    assert "mileage must be non-negative" in rejected.loc[1, "rejection_reason"]
    assert "year must not exceed reference year 2024" in rejected.loc[2, "rejection_reason"]
    assert summary["rows_before"] - summary["rows_rejected"] == summary["rows_after"]


def test_numeric_conversion_failure_is_tracked():
    _, rejected, summary = clean_source(valid_raw(price="not-a-number"), brand="Audi", source_file="audi.csv")
    assert len(rejected) == 1
    assert "numeric conversion failed: price" in rejected.loc[0, "rejection_reason"]
    assert summary["numeric_conversion_failures"] == 1


def test_missing_required_columns_raise_useful_error():
    raw = valid_raw().drop(columns=["mpg"])
    with pytest.raises(DataValidationError, match="missing required columns"):
        clean_source(raw, brand="Audi", source_file="audi.csv")


def test_model_capitalization_is_not_title_cased():
    cleaned, _, _ = clean_source(valid_raw(model=" i3"), brand="BMW", source_file="bmw.csv")
    assert cleaned.loc[0, "model"] == "i3"
