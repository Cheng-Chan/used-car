"""Reproducible, non-destructive raw-data audit and report generation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd
from tabulate import tabulate

from .config import (
    CANONICAL_SOURCE_FILES,
    CATEGORY_COLUMNS,
    COLUMN_RENAME_MAP,
    EXPECTED_COMPLETE_SOURCE_COLUMNS,
    EXPECTED_LEGACY_SOURCE_COLUMNS,
    INTERIM_DATA_DIR,
    LEGACY_MODEL_FILES,
    NUMERIC_COLUMNS,
    REFERENCE_YEAR,
    RAW_DATA_DIR,
    REPORTS_DIR,
    SHARED_ANALYTICAL_COLUMNS,
    TABLES_DIR,
)
from .data_io import (
    load_canonical_candidate_frames,
    load_named_source,
    load_source_frames,
    normalize_for_audit,
    source_path,
)


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest of a file in binary chunks."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _source_metadata(filename: str) -> dict[str, Any]:
    if filename in CANONICAL_SOURCE_FILES:
        return {
            "assigned_brand": CANONICAL_SOURCE_FILES[filename],
            "source_type": "canonical_manufacturer",
            "included_in_canonical": "yes",
            "exclusion_reason": "",
        }
    legacy = LEGACY_MODEL_FILES[filename]
    return {
        "assigned_brand": legacy["brand"],
        "source_type": "legacy_model_file",
        "included_in_canonical": "no",
        "exclusion_reason": legacy["reason"],
    }


def _json_columns(columns: list[str]) -> str:
    return json.dumps(columns, ensure_ascii=False)


def build_raw_manifest() -> pd.DataFrame:
    """Build a manifest identifying each raw input and its current hash."""

    records: list[dict[str, Any]] = []
    for filename in list(CANONICAL_SOURCE_FILES) + list(LEGACY_MODEL_FILES):
        path = source_path(filename)
        dataframe = load_named_source(filename)
        metadata = _source_metadata(filename)
        records.append(
            {
                "relative_path": str(path.relative_to(REPORTS_DIR.parent)),
                "filename": filename,
                "file_size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "row_count": len(dataframe),
                "column_count": len(dataframe.columns),
                "exact_columns": _json_columns(dataframe.columns.tolist()),
                **metadata,
            }
        )
    return pd.DataFrame(records)


def build_schema_comparison() -> pd.DataFrame:
    """Compare each raw schema with the expected complete source schema."""

    records: list[dict[str, Any]] = []
    for filename in list(CANONICAL_SOURCE_FILES) + list(LEGACY_MODEL_FILES):
        dataframe = load_named_source(filename)
        actual = list(dataframe.columns)
        missing_complete = [column for column in EXPECTED_COMPLETE_SOURCE_COLUMNS if column not in actual]
        unexpected = [column for column in actual if column not in EXPECTED_COMPLETE_SOURCE_COLUMNS]
        tax_column = "tax" if "tax" in actual else "tax(£)" if "tax(£)" in actual else "missing"
        expected_order = list(EXPECTED_COMPLETE_SOURCE_COLUMNS)
        order_matches = actual == expected_order
        dtype_map = {column: str(dtype) for column, dtype in dataframe.dtypes.items()}
        issue_parts = []
        if tax_column == "tax(£)":
            issue_parts.append("tax uses tax(£)")
        if "tax" not in actual and "tax(£)" not in actual:
            issue_parts.append("missing tax")
        if "mpg" not in actual:
            issue_parts.append("missing mpg")
        if unexpected:
            issue_parts.append("unexpected columns")
        if not order_matches:
            issue_parts.append("column order differs")
        records.append(
            {
                "filename": filename,
                "source_type": _source_metadata(filename)["source_type"],
                "actual_columns": _json_columns(actual),
                "expected_complete_columns": _json_columns(expected_order),
                "missing_complete_columns": _json_columns(missing_complete),
                "unexpected_columns": _json_columns(unexpected),
                "tax_column": tax_column,
                "mpg_available": "yes" if "mpg" in actual else "no",
                "column_order_matches_complete": "yes" if order_matches else "no",
                "inferred_dtypes": json.dumps(dtype_map, ensure_ascii=False),
                "schema_issues": "; ".join(issue_parts) if issue_parts else "none",
            }
        )
    return pd.DataFrame(records)


def _canonical_audit_frame(filename: str, dataframe: pd.DataFrame) -> pd.DataFrame:
    result = normalize_for_audit(dataframe)
    result["source_file"] = filename
    return result


def _combined_candidate_frame() -> pd.DataFrame:
    frames = [_canonical_audit_frame(filename, dataframe) for filename, dataframe in load_canonical_candidate_frames().items()]
    return pd.concat(frames, ignore_index=True, sort=False)


def _duplicate_counts(dataframe: pd.DataFrame) -> tuple[int, int]:
    duplicate_mask = dataframe.duplicated(keep=False)
    return int(dataframe.duplicated().sum()), int(duplicate_mask.sum())


def _numeric_summary(dataframe: pd.DataFrame, column: str) -> dict[str, Any]:
    if column not in dataframe.columns:
        return {
            "available": "no",
            "missing_count": len(dataframe),
            "missing_pct": 100.0 if len(dataframe) else 0.0,
            "conversion_failures": 0,
            "minimum": None,
            "maximum": None,
            "zero_count": 0,
            "negative_count": 0,
            "future_year_count": 0,
            "q1": None,
            "q3": None,
            "iqr": None,
            "below_iqr_count": 0,
            "above_iqr_count": 0,
        }
    raw = dataframe[column]
    numeric = pd.to_numeric(raw, errors="coerce")
    conversion_failures = int(numeric.isna().sum() - raw.isna().sum())
    non_missing = numeric.dropna()
    q1 = non_missing.quantile(0.25) if not non_missing.empty else None
    q3 = non_missing.quantile(0.75) if not non_missing.empty else None
    iqr = q3 - q1 if q1 is not None and q3 is not None else None
    lower = q1 - 1.5 * iqr if iqr is not None else None
    upper = q3 + 1.5 * iqr if iqr is not None else None
    return {
        "available": "yes",
        "missing_count": int(numeric.isna().sum()),
        "missing_pct": round(float(numeric.isna().mean() * 100), 4) if len(numeric) else 0.0,
        "conversion_failures": conversion_failures,
        "minimum": non_missing.min() if not non_missing.empty else None,
        "maximum": non_missing.max() if not non_missing.empty else None,
        "zero_count": int(non_missing.eq(0).sum()),
        "negative_count": int(non_missing.lt(0).sum()),
        "future_year_count": int(non_missing.gt(REFERENCE_YEAR).sum()) if column == "year" else 0,
        "q1": q1,
        "q3": q3,
        "iqr": iqr,
        "below_iqr_count": int(non_missing.lt(lower).sum()) if lower is not None else 0,
        "above_iqr_count": int(non_missing.gt(upper).sum()) if upper is not None else 0,
    }


def build_missing_values() -> pd.DataFrame:
    """Return missing-value counts for every raw source column."""

    records: list[dict[str, Any]] = []
    for filename, dataframe in load_source_frames(include_legacy=True).items():
        for column in dataframe.columns:
            missing_count = int(dataframe[column].isna().sum())
            records.append(
                {
                    "source": filename,
                    "column": column,
                    "row_count": len(dataframe),
                    "missing_count": missing_count,
                    "missing_pct": round(missing_count / len(dataframe) * 100, 4) if len(dataframe) else 0.0,
                }
            )
    candidate = _combined_candidate_frame()
    for column in candidate.columns:
        missing_count = int(candidate[column].isna().sum())
        records.append(
            {
                "source": "canonical_candidate_combined",
                "column": column,
                "row_count": len(candidate),
                "missing_count": missing_count,
                "missing_pct": round(missing_count / len(candidate) * 100, 4) if len(candidate) else 0.0,
            }
        )
    return pd.DataFrame(records)


def build_numeric_quality() -> pd.DataFrame:
    """Return range, missingness, zero, validity, and IQR review metrics."""

    records: list[dict[str, Any]] = []
    source_frames = load_source_frames(include_legacy=True)
    source_frames["canonical_candidate_combined"] = _combined_candidate_frame()
    for source, dataframe in source_frames.items():
        normalized = normalize_for_audit(dataframe)
        for column in NUMERIC_COLUMNS:
            records.append({"source": source, "column": column, "row_count": len(normalized), **_numeric_summary(normalized, column)})
    return pd.DataFrame(records)


def build_quality_summary() -> pd.DataFrame:
    """Return one focused quality summary row per source and candidate set."""

    source_frames = load_source_frames(include_legacy=True)
    source_frames["canonical_candidate_combined"] = _combined_candidate_frame()
    records: list[dict[str, Any]] = []
    for source, dataframe in source_frames.items():
        normalized = normalize_for_audit(dataframe)
        duplicate_rows, duplicate_group_rows = _duplicate_counts(dataframe)
        shared_columns = [column for column in SHARED_ANALYTICAL_COLUMNS if column in normalized.columns]
        whitespace_counts = {
            column: int(dataframe[column].astype("string").ne(dataframe[column].astype("string").str.strip()).sum())
            for column in ("model", "transmission")
            if column in dataframe.columns
        }
        fuel_column = "fuelType" if "fuelType" in dataframe.columns else "fuel_type" if "fuel_type" in dataframe.columns else None
        if fuel_column is not None:
            whitespace_counts[fuel_column] = int(dataframe[fuel_column].astype("string").ne(dataframe[fuel_column].astype("string").str.strip()).sum())
        values = {column: _numeric_summary(normalized, column) for column in NUMERIC_COLUMNS}
        records.append(
            {
                "source": source,
                "row_count": len(dataframe),
                "column_count": len(dataframe.columns),
                "missing_cell_count": int(dataframe.isna().sum().sum()),
                "exact_duplicate_rows": duplicate_rows,
                "exact_duplicate_group_rows": duplicate_group_rows,
                "duplicate_shared_analytical_rows": int(normalized.duplicated(subset=shared_columns).sum()) if shared_columns else 0,
                "unique_models": int(normalized["model"].nunique(dropna=True)) if "model" in normalized else 0,
                "unique_fuel_types": int(normalized["fuel_type"].nunique(dropna=True)) if "fuel_type" in normalized else 0,
                "unique_transmissions": int(normalized["transmission"].nunique(dropna=True)) if "transmission" in normalized else 0,
                "whitespace_issues": json.dumps(whitespace_counts),
                "year_min": values["year"]["minimum"],
                "year_max": values["year"]["maximum"],
                "price_min": values["price"]["minimum"],
                "price_max": values["price"]["maximum"],
                "mileage_min": values["mileage"]["minimum"],
                "mileage_max": values["mileage"]["maximum"],
                "tax_min": values["tax"]["minimum"],
                "tax_max": values["tax"]["maximum"],
                "mpg_min": values["mpg"]["minimum"],
                "mpg_max": values["mpg"]["maximum"],
                "engine_size_min": values["engine_size"]["minimum"],
                "engine_size_max": values["engine_size"]["maximum"],
                "zero_tax_count": values["tax"]["zero_count"],
                "zero_mpg_count": values["mpg"]["zero_count"],
                "zero_engine_size_count": values["engine_size"]["zero_count"],
                "negative_numeric_count": sum(values[column]["negative_count"] for column in NUMERIC_COLUMNS),
                "future_year_count": values["year"]["future_year_count"],
                "review_flag_count": _review_flag_count(normalized),
            }
        )
    return pd.DataFrame(records)


def _review_flag_count(dataframe: pd.DataFrame) -> int:
    """Count values outside broad review thresholds; this does not reject data."""

    year = pd.to_numeric(dataframe.get("year", pd.Series(dtype=float)), errors="coerce")
    mpg = pd.to_numeric(dataframe.get("mpg", pd.Series(dtype=float)), errors="coerce")
    engine_size = pd.to_numeric(dataframe.get("engine_size", pd.Series(dtype=float)), errors="coerce")
    price = pd.to_numeric(dataframe.get("price", pd.Series(dtype=float)), errors="coerce")
    return int(year.gt(REFERENCE_YEAR).sum() + mpg.lt(10).sum() + mpg.gt(250).sum() + engine_size.gt(8).sum() + price.gt(100000).sum())


def build_category_summary() -> pd.DataFrame:
    """Return observed fuel and transmission categories by source."""

    records: list[dict[str, Any]] = []
    source_frames = load_source_frames(include_legacy=True)
    source_frames["canonical_candidate_combined"] = _combined_candidate_frame()
    for source, dataframe in source_frames.items():
        normalized = normalize_for_audit(dataframe)
        for column in CATEGORY_COLUMNS:
            if column not in normalized:
                continue
            counts = normalized[column].value_counts(dropna=False)
            for value, count in counts.items():
                records.append({"source": source, "category_column": column, "category_value": "<missing>" if pd.isna(value) else value, "count": int(count)})
    return pd.DataFrame(records)


def _overlap_record(legacy_filename: str, manufacturer_filename: str) -> dict[str, Any]:
    legacy = normalize_for_audit(load_named_source(legacy_filename))
    manufacturer = normalize_for_audit(load_named_source(manufacturer_filename))
    scope = LEGACY_MODEL_FILES[legacy_filename]["model_scope"]
    manufacturer_scope = manufacturer[manufacturer["model"] == scope]
    comparison_columns = list(SHARED_ANALYTICAL_COLUMNS)
    legacy_counts = legacy[comparison_columns].value_counts(dropna=False)
    manufacturer_counts = manufacturer_scope[comparison_columns].value_counts(dropna=False)
    matching_instances = sum(min(int(count), int(manufacturer_counts.get(key, 0))) for key, count in legacy_counts.items())
    matching_groups = len(legacy_counts.index.intersection(manufacturer_counts.index))
    return {
        "legacy_file": legacy_filename,
        "manufacturer_file": manufacturer_filename,
        "model_scope": scope,
        "legacy_row_count": len(legacy),
        "manufacturer_scope_row_count": len(manufacturer_scope),
        "legacy_unique_shared_rows": len(legacy_counts),
        "manufacturer_scope_unique_shared_rows": len(manufacturer_counts),
        "exact_matching_instances": matching_instances,
        "exact_matching_groups": matching_groups,
        "legacy_unmatched_instances": len(legacy) - matching_instances,
        "manufacturer_scope_unmatched_instances": len(manufacturer_scope) - matching_instances,
        "legacy_year_min": pd.to_numeric(legacy["year"]).min(),
        "legacy_year_max": pd.to_numeric(legacy["year"]).max(),
        "manufacturer_scope_year_min": pd.to_numeric(manufacturer_scope["year"]).min(),
        "manufacturer_scope_year_max": pd.to_numeric(manufacturer_scope["year"]).max(),
        "missing_fields_in_legacy": "tax, mpg",
        "recommendation": "exclude from canonical dataset",
    }


def build_legacy_overlap() -> pd.DataFrame:
    """Compare legacy model-only files to their manufacturer-file scopes."""

    return pd.DataFrame(
        [
            _overlap_record("cclass.csv", "merc.csv"),
            _overlap_record("focus.csv", "ford.csv"),
        ]
    )


def _markdown_table(dataframe: pd.DataFrame, columns: list[str] | None = None) -> str:
    selected = dataframe if columns is None else dataframe[columns]
    return tabulate(selected, headers="keys", tablefmt="github", showindex=False)


def write_data_quality_report(
    manifest: pd.DataFrame,
    schema: pd.DataFrame,
    quality: pd.DataFrame,
    numeric: pd.DataFrame,
    categories: pd.DataFrame,
    legacy: pd.DataFrame,
) -> Path:
    """Write the narrative raw-data quality report from generated audit tables."""

    candidate = quality.loc[quality["source"] == "canonical_candidate_combined"].iloc[0]
    complete_sources = manifest.loc[manifest["included_in_canonical"] == "yes"]
    schema_issues = schema.loc[schema["schema_issues"] != "none", ["filename", "schema_issues"]]
    missing_nonzero = numeric.loc[numeric["missing_count"] > 0, ["source", "column", "missing_count", "missing_pct"]]
    report = f"""# Raw Data Quality Report

## Executive summary

The repository contains {int(manifest['row_count'].sum()):,} raw listing rows across {len(manifest)} CSV files. The recommended canonical candidate uses {len(complete_sources)} complete manufacturer-level files and contains {int(candidate['row_count']):,} rows before cleaning. The two legacy model-only files are excluded because they overlap the complete Ford and Mercedes-Benz sources and omit `tax` and `mpg`.

This report is an audit, not a cleaning result. Raw files remain immutable. SHA-256 hashes in `raw_data_manifest.csv` identify the exact input bytes used for this audit.

## Source inventory

{_markdown_table(manifest, ['filename', 'row_count', 'column_count', 'assigned_brand', 'source_type', 'included_in_canonical'])}

## Schema findings

{_markdown_table(schema, ['filename', 'tax_column', 'mpg_available', 'column_order_matches_complete', 'schema_issues'])}

The complete sources share the same nine fields except that `hyundi.csv` uses `tax(£)` instead of `tax`. The audit records this as a source-level difference to normalize later. `cclass.csv` and `focus.csv` omit both `tax` and `mpg`.

## Missing-data findings

The raw source files contain no blank cells in their existing columns. The legacy files still have analytical fields unavailable by schema: `tax` and `mpg`. These are structural omissions, not evidence that the values are zero.

{_markdown_table(missing_nonzero) if not missing_nonzero.empty else 'No missing cells were found in columns present in the raw files.'}

## Duplicate findings

Exact duplicate rows occur within several source files. The canonical candidate has {int(candidate['exact_duplicate_rows']):,} duplicate rows under the raw normalized candidate view. There is no listing identifier, so duplicate-looking rows are not removed during the audit. A duplicate policy must be approved during cleaning.

## Category findings

Observed fuel types and transmission values are preserved, including `Other` and `Electric` where present. Unknown categories must be reported rather than silently recoded.

{_markdown_table(categories.loc[categories['source'] == 'canonical_candidate_combined'].groupby(['category_column', 'category_value'], as_index=False)['count'].sum(), ['category_column', 'category_value', 'count'])}

## Range and validity findings

The candidate source set has year range {candidate['year_min']}–{candidate['year_max']}, price range £{candidate['price_min']:,.2f}–£{candidate['price_max']:,.2f}, and mileage range {candidate['mileage_min']:,.0f}–{candidate['mileage_max']:,.0f}. Zero annual tax is observed and remains valid for the required exercise. Zero engine sizes require investigation and must not be silently changed.

The audit found {int(candidate['future_year_count'])} year value after the fixed reference year {REFERENCE_YEAR}. Broad review flags are diagnostic only and do not automatically invalidate records. Outliers should be described with IQR or percentile analysis rather than deleted merely for being extreme.

{_markdown_table(quality, ['source', 'row_count', 'exact_duplicate_rows', 'zero_tax_count', 'zero_engine_size_count', 'future_year_count', 'review_flag_count'])}

## Legacy-file assessment

{_markdown_table(legacy, ['legacy_file', 'manufacturer_file', 'legacy_row_count', 'manufacturer_scope_row_count', 'exact_matching_instances', 'legacy_unmatched_instances', 'manufacturer_scope_unmatched_instances', 'recommendation'])}

The legacy files are not exact duplicates, but their overlap with broader manufacturer files could overrepresent Ford Focus and Mercedes-Benz C Class listings. They remain excluded from the canonical dataset.

## Recommended cleaning rules

1. Load only the explicit nine-file canonical mapping.
2. Preserve raw filenames and derive brands from the explicit mapping.
3. Rename `fuelType`, `engineSize`, and `tax(£)` explicitly.
4. Trim `model`, `transmission`, and fuel-type strings without title-casing model names.
5. Validate numeric conversion with diagnostics before accepting or rejecting rows.
6. Keep `tax == 0` as valid.
7. Investigate the year-2060 Ford record before applying the documented year rule.
8. Do not remove outliers or duplicates without an approved, traceable policy.

## Risks and limitations

- The files contain listings rather than confirmed sale transactions.
- Units such as GBP, miles, MPG, and litres are dataset-context assumptions.
- There is no unique listing identifier, so duplicate-looking rows may be legitimate.
- Vehicle condition, location, listing date, trim, and optional equipment are unavailable.
- Source files have unequal sample sizes.
- `cclass.csv` and `focus.csv` require special treatment because of their scope and schemas.
- A zero tax value must not be given a policy explanation without separate evidence.

## Final recommended canonical source list

{', '.join(complete_sources['filename'])}

Excluded legacy sources: `cclass.csv` and `focus.csv`.
"""
    report_path = REPORTS_DIR / "data_quality_report.md"
    report_path.write_text(report, encoding="utf-8")
    return report_path


def run_audit() -> dict[str, pd.DataFrame | Path]:
    """Generate all Phase 2 audit outputs and return them for notebook use."""

    for directory in (INTERIM_DATA_DIR, TABLES_DIR, REPORTS_DIR):
        directory.mkdir(parents=True, exist_ok=True)

    manifest = build_raw_manifest()
    schema = build_schema_comparison()
    quality = build_quality_summary()
    missing = build_missing_values()
    numeric = build_numeric_quality()
    categories = build_category_summary()
    legacy = build_legacy_overlap()

    outputs: dict[str, pd.DataFrame | Path] = {
        "manifest": manifest,
        "schema": schema,
        "quality": quality,
        "missing": missing,
        "numeric": numeric,
        "categories": categories,
        "legacy": legacy,
    }
    manifest.to_csv(TABLES_DIR / "raw_data_manifest.csv", index=False)
    schema.to_csv(TABLES_DIR / "raw_schema_comparison.csv", index=False)
    quality.to_csv(TABLES_DIR / "source_quality_summary.csv", index=False)
    missing.to_csv(TABLES_DIR / "missing_values_by_source.csv", index=False)
    numeric.to_csv(TABLES_DIR / "numeric_quality_summary.csv", index=False)
    categories.to_csv(TABLES_DIR / "category_summary.csv", index=False)
    legacy.to_csv(TABLES_DIR / "legacy_file_overlap.csv", index=False)
    outputs["report"] = write_data_quality_report(manifest, schema, quality, numeric, categories, legacy)
    return outputs
