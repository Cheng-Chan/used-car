"""Command-line entry point for the reproducible used-car analysis pipeline."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Sequence

import pandas as pd

from src.analysis import build_guiding_exercise_outputs, write_guiding_exercise_outputs
from src.audit import build_raw_manifest, run_audit
from src.cleaning import build_clean_dataset, write_clean_outputs
from src.config import (
    CANONICAL_SOURCE_FILES,
    FIGURES_DIR,
    INTERIM_DATA_DIR,
    PROCESSED_DATA_DIR,
    RAW_DATA_DIR,
    TABLES_DIR,
)
from src.features import add_vehicle_age, build_eda_tables, write_eda_outputs
from src.plotting import create_required_figures
from src.validation import DataValidationError, validate_clean_dataframe

LOGGER = logging.getLogger("used_car_pipeline")
MANIFEST_PATH = TABLES_DIR / "raw_data_manifest.csv"


def configure_logging() -> None:
    """Configure concise, user-facing pipeline logs."""

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def verify_raw_sources_and_manifest() -> pd.DataFrame:
    """Verify canonical raw files and their hashes against the saved manifest."""

    missing = [filename for filename in CANONICAL_SOURCE_FILES if not (RAW_DATA_DIR / filename).is_file()]
    if missing:
        raise DataValidationError(f"Missing expected canonical raw source files: {missing}")
    if not MANIFEST_PATH.is_file():
        raise DataValidationError(
            f"Raw manifest not found at {MANIFEST_PATH}. Run `python main.py audit` to generate it explicitly."
        )

    saved = pd.read_csv(MANIFEST_PATH).set_index("filename")
    current = build_raw_manifest().set_index("filename")
    mismatches: list[str] = []
    for filename in CANONICAL_SOURCE_FILES:
        if filename not in saved.index or filename not in current.index:
            mismatches.append(f"{filename}: missing from manifest")
            continue
        for field in ("sha256", "file_size_bytes", "row_count", "column_count"):
            if str(saved.loc[filename, field]) != str(current.loc[filename, field]):
                mismatches.append(f"{filename}: {field} changed")
    if mismatches:
        raise DataValidationError(
            "Raw-data manifest verification failed. Review the raw files and run `python main.py audit` explicitly. "
            + "; ".join(mismatches)
        )
    LOGGER.info("Verified %d canonical raw sources against the saved manifest.", len(CANONICAL_SOURCE_FILES))
    return current.reset_index()


def run_build_stage() -> dict[str, Path]:
    """Clean, integrate, enrich, and summarize the approved source set."""

    verify_raw_sources_and_manifest()
    clean, rejected, cleaning_summary = build_clean_dataset()
    clean_paths = write_clean_outputs(clean, rejected, cleaning_summary)
    enriched = add_vehicle_age(clean)
    eda_tables = build_eda_tables(enriched)
    eda_paths = write_eda_outputs(enriched, eda_tables)
    LOGGER.info("Build complete: %d cleaned rows, %d rejected rows.", len(clean), len(rejected))
    return {**clean_paths, **eda_paths}


def _load_enriched() -> pd.DataFrame:
    path = PROCESSED_DATA_DIR / "used_cars_enriched.csv"
    if not path.is_file():
        raise DataValidationError("Enriched dataset is missing. Run `python main.py build` first.")
    dataframe = pd.read_csv(path)
    validate_clean_dataframe(dataframe.drop(columns=["vehicle_age"]))
    return dataframe


def run_analyze_stage() -> dict[str, Path]:
    """Generate all guiding-exercise analytical tables."""

    verify_raw_sources_and_manifest()
    dataframe = _load_enriched()
    outputs = build_guiding_exercise_outputs(dataframe)
    paths = write_guiding_exercise_outputs(outputs)
    LOGGER.info("Analysis complete: generated %d analytical tables.", len(paths))
    return paths


def run_plot_stage() -> dict[str, Path]:
    """Generate all required Matplotlib figures."""

    verify_raw_sources_and_manifest()
    dataframe = _load_enriched()
    outputs = build_guiding_exercise_outputs(dataframe)
    write_guiding_exercise_outputs(outputs)
    paths = create_required_figures(dataframe, outputs, output_dir=FIGURES_DIR)
    LOGGER.info("Plot stage complete: generated %d figures.", len(paths))
    return paths


def run_all_stages() -> None:
    """Run audit, build, analysis, and plotting in deterministic order."""

    run_audit()
    run_build_stage()
    run_analyze_stage()
    run_plot_stage()
    clean = pd.read_csv(PROCESSED_DATA_DIR / "used_cars_clean.csv")
    rejected = pd.read_csv(INTERIM_DATA_DIR / "rejected_rows.csv")
    LOGGER.info(
        "Pipeline complete: %d cleaned rows, %d rejected rows, outputs in reports/.",
        len(clean),
        len(rejected),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the used-car prices analytics pipeline.")
    parser.add_argument(
        "command",
        choices=("audit", "build", "analyze", "plot", "all"),
        help="Pipeline stage to run. Use 'all' for the complete reproducible pipeline.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Parse a command, execute it, and return a shell-compatible status code."""

    configure_logging()
    args = build_parser().parse_args(argv)
    try:
        if args.command == "audit":
            run_audit()
            LOGGER.info("Audit complete: manifest, schema, quality tables, and report generated.")
        elif args.command == "build":
            run_build_stage()
        elif args.command == "analyze":
            run_analyze_stage()
        elif args.command == "plot":
            run_plot_stage()
        elif args.command == "all":
            run_all_stages()
        return 0
    except Exception as error:  # CLI boundary: convert validation failures to nonzero status.
        LOGGER.error("Pipeline failed: %s", error)
        LOGGER.debug("Pipeline exception details", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
