"""Central configuration for the Used Car Prices Analytics project."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
INTERIM_DATA_DIR = PROJECT_ROOT / "data" / "interim"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
REPORTS_DIR = PROJECT_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"
TABLES_DIR = REPORTS_DIR / "tables"

# The assignment requires vehicle age to be calculated as of this fixed year.
REFERENCE_YEAR = 2024

# The source mapping is deliberately explicit. Legacy model-only files are not
# loaded into the canonical candidate dataset because they overlap the complete
# manufacturer files and omit tax and MPG.
CANONICAL_SOURCE_FILES = {
    "audi.csv": "Audi",
    "bmw.csv": "BMW",
    "ford.csv": "Ford",
    "hyundi.csv": "Hyundai",
    "merc.csv": "Mercedes-Benz",
    "skoda.csv": "Skoda",
    "toyota.csv": "Toyota",
    "vauxhall.csv": "Vauxhall",
    "vw.csv": "Volkswagen",
}

LEGACY_MODEL_FILES = {
    "cclass.csv": {
        "brand": "Mercedes-Benz",
        "model_scope": "C Class",
        "reason": "Model-only file overlaps merc.csv and omits tax and mpg.",
    },
    "focus.csv": {
        "brand": "Ford",
        "model_scope": "Focus",
        "reason": "Model-only file overlaps ford.csv and omits tax and mpg.",
    },
}

EXPECTED_COMPLETE_SOURCE_COLUMNS = (
    "model",
    "year",
    "price",
    "transmission",
    "mileage",
    "fuelType",
    "tax",
    "mpg",
    "engineSize",
)

EXPECTED_LEGACY_SOURCE_COLUMNS = (
    "model",
    "year",
    "price",
    "transmission",
    "mileage",
    "fuelType",
    "engineSize",
)

COLUMN_RENAME_MAP = {
    "fuelType": "fuel_type",
    "engineSize": "engine_size",
    "tax(£)": "tax",
}

SHARED_ANALYTICAL_COLUMNS = (
    "model",
    "year",
    "price",
    "transmission",
    "mileage",
    "fuel_type",
    "engine_size",
)

RAW_CANONICAL_COLUMNS = (
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
    "source_file",
)

CANONICAL_COLUMNS = (
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

NUMERIC_COLUMNS = ("year", "price", "mileage", "tax", "mpg", "engine_size")
CATEGORY_COLUMNS = ("fuel_type", "transmission")
