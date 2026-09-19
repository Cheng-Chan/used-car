import pandas as pd
import pytest

from src.config import CANONICAL_SOURCE_FILES, LEGACY_MODEL_FILES
from src.data_io import (
    iter_source_filenames,
    load_canonical_candidate_frames,
    normalize_for_audit,
)


def test_canonical_source_selection_is_explicit():
    filenames = iter_source_filenames(include_legacy=False)
    assert filenames == tuple(CANONICAL_SOURCE_FILES)
    assert not set(LEGACY_MODEL_FILES).intersection(filenames)


def test_legacy_files_are_not_loaded_as_canonical_sources():
    frames = load_canonical_candidate_frames()
    assert set(frames) == set(CANONICAL_SOURCE_FILES)
    assert "cclass.csv" not in frames
    assert "focus.csv" not in frames


def test_audit_normalization_renames_and_trims_without_mutating_input():
    raw = pd.DataFrame(
        {
            "model": [" A1"],
            "transmission": ["Manual "],
            "fuelType": [" Petrol"],
            "tax(£)": [0],
        }
    )
    normalized = normalize_for_audit(raw)
    assert raw.loc[0, "model"] == " A1"
    assert normalized.loc[0, "model"] == "A1"
    assert normalized.loc[0, "transmission"] == "Manual"
    assert normalized.loc[0, "fuel_type"] == "Petrol"
    assert normalized.loc[0, "tax"] == 0


@pytest.mark.parametrize(
    ("filename", "brand"),
    [("hyundi.csv", "Hyundai"), ("merc.csv", "Mercedes-Benz"), ("vw.csv", "Volkswagen")],
)
def test_explicit_brand_mapping(filename, brand):
    assert CANONICAL_SOURCE_FILES[filename] == brand
