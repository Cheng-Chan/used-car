"""Read-only helpers for loading explicitly selected raw source files."""

from pathlib import Path

import pandas as pd

from .config import (
    CANONICAL_SOURCE_FILES,
    COLUMN_RENAME_MAP,
    LEGACY_MODEL_FILES,
    RAW_DATA_DIR,
)


def source_path(filename: str) -> Path:
    """Return the path for a known raw filename and reject unknown sources."""

    known_files = set(CANONICAL_SOURCE_FILES) | set(LEGACY_MODEL_FILES)
    if filename not in known_files:
        raise ValueError(f"Unknown source file {filename!r}; use the explicit source mapping.")
    path = RAW_DATA_DIR / filename
    if not path.is_file():
        raise FileNotFoundError(f"Expected raw source file does not exist: {path}")
    return path


def load_raw_source(path: Path) -> pd.DataFrame:
    """Load one raw CSV without changing its columns or values."""

    if not path.is_file():
        raise FileNotFoundError(f"Raw source file does not exist: {path}")
    return pd.read_csv(path)


def load_named_source(filename: str) -> pd.DataFrame:
    """Load one explicitly named raw source file."""

    return load_raw_source(source_path(filename))


def normalize_for_audit(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Return an audit copy with canonical names and trimmed comparison strings.

    This is not the cleaning pipeline. It is a non-destructive view used for
    schema-independent comparisons and quality calculations.
    """

    result = dataframe.rename(columns=COLUMN_RENAME_MAP).copy()
    for column in ("model", "transmission", "fuel_type"):
        if column in result.columns:
            result[column] = result[column].astype("string").str.strip()
    return result


def iter_source_filenames(*, include_legacy: bool = True) -> tuple[str, ...]:
    """Return source filenames in deterministic explicit-mapping order."""

    names = list(CANONICAL_SOURCE_FILES)
    if include_legacy:
        names.extend(LEGACY_MODEL_FILES)
    return tuple(names)


def load_source_frames(*, include_legacy: bool = True) -> dict[str, pd.DataFrame]:
    """Load all explicitly mapped source files for audit purposes."""

    return {filename: load_named_source(filename) for filename in iter_source_filenames(include_legacy=include_legacy)}


def load_canonical_candidate_frames() -> dict[str, pd.DataFrame]:
    """Load only the approved candidate source files, still without cleaning."""

    return {filename: load_named_source(filename) for filename in CANONICAL_SOURCE_FILES}
