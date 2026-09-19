from pathlib import Path

import pandas as pd

from main import verify_raw_sources_and_manifest
from src.config import CANONICAL_SOURCE_FILES, CANONICAL_COLUMNS, PROCESSED_DATA_DIR, TABLES_DIR
from src.data_io import iter_source_filenames, load_canonical_candidate_frames


def test_all_expected_raw_sources_exist_and_selection_is_explicit():
    assert set(iter_source_filenames(include_legacy=False)) == set(CANONICAL_SOURCE_FILES)
    assert {path.name for path in Path("data/raw").glob("*.csv")} == set(CANONICAL_SOURCE_FILES) | {"cclass.csv", "focus.csv"}
    assert "cclass.csv" not in load_canonical_candidate_frames()
    assert "focus.csv" not in load_canonical_candidate_frames()


def test_saved_raw_manifest_verifies_current_sources():
    manifest = verify_raw_sources_and_manifest()
    assert len(manifest) == 11
    assert set(manifest.loc[manifest["included_in_canonical"] == "yes", "assigned_brand"]) == {
        "Audi", "BMW", "Ford", "Hyundai", "Mercedes-Benz", "Skoda", "Toyota", "Vauxhall", "Volkswagen"
    }


def test_processed_dataset_has_required_columns_and_tax_zero_records():
    dataframe = pd.read_csv(PROCESSED_DATA_DIR / "used_cars_enriched.csv")
    assert dataframe.columns.tolist() == list(CANONICAL_COLUMNS)
    assert dataframe["tax"].eq(0).any()
    assert dataframe["vehicle_age"].eq(2024 - dataframe["year"]).all()
    assert dataframe["brand"].nunique() == 9


def test_required_analysis_outputs_exist_with_expected_schemas():
    expected = {
        "price_by_fuel_type.csv": {"fuel_type", "average_price"},
        "mileage_price_correlation.csv": {"pearson_correlation", "spearman_correlation", "observations"},
        "transmission_summary.csv": {"transmission", "car_count", "median_price"},
        "diesel_zero_tax_cars.csv": {"fuel_type", "tax"},
        "brand_price_distribution.csv": {"brand", "q1_price", "median_price", "q3_price"},
        "top_models.csv": {"model", "listing_count"},
        "price_by_vehicle_age.csv": {"vehicle_age", "average_price"},
    }
    for filename, columns in expected.items():
        path = TABLES_DIR / filename
        assert path.is_file(), filename
        assert columns.issubset(pd.read_csv(path, nrows=0).columns), filename


def test_pipeline_output_directories_exist():
    assert PROCESSED_DATA_DIR.is_dir()
    assert TABLES_DIR.is_dir()
    assert Path("reports/figures").is_dir()
