# Raw Data Quality Report

## Executive summary

The repository contains 108,540 raw listing rows across 11 CSV files. The recommended canonical candidate uses 9 complete manufacturer-level files and contains 99,187 rows before cleaning. The two legacy model-only files are excluded because they overlap the complete Ford and Mercedes-Benz sources and omit `tax` and `mpg`.

This report is an audit, not a cleaning result. Raw files remain immutable. SHA-256 hashes in `raw_data_manifest.csv` identify the exact input bytes used for this audit.

## Source inventory

| filename     |   row_count |   column_count | assigned_brand   | source_type            | included_in_canonical   |
|--------------|-------------|----------------|------------------|------------------------|-------------------------|
| audi.csv     |       10668 |              9 | Audi             | canonical_manufacturer | yes                     |
| bmw.csv      |       10781 |              9 | BMW              | canonical_manufacturer | yes                     |
| ford.csv     |       17965 |              9 | Ford             | canonical_manufacturer | yes                     |
| hyundi.csv   |        4860 |              9 | Hyundai          | canonical_manufacturer | yes                     |
| merc.csv     |       13119 |              9 | Mercedes-Benz    | canonical_manufacturer | yes                     |
| skoda.csv    |        6267 |              9 | Skoda            | canonical_manufacturer | yes                     |
| toyota.csv   |        6738 |              9 | Toyota           | canonical_manufacturer | yes                     |
| vauxhall.csv |       13632 |              9 | Vauxhall         | canonical_manufacturer | yes                     |
| vw.csv       |       15157 |              9 | Volkswagen       | canonical_manufacturer | yes                     |
| cclass.csv   |        3899 |              7 | Mercedes-Benz    | legacy_model_file      | no                      |
| focus.csv    |        5454 |              7 | Ford             | legacy_model_file      | no                      |

## Schema findings

| filename     | tax_column   | mpg_available   | column_order_matches_complete   | schema_issues                                             |
|--------------|--------------|-----------------|---------------------------------|-----------------------------------------------------------|
| audi.csv     | tax          | yes             | yes                             | none                                                      |
| bmw.csv      | tax          | yes             | yes                             | none                                                      |
| ford.csv     | tax          | yes             | yes                             | none                                                      |
| hyundi.csv   | tax(£)       | yes             | no                              | tax uses tax(£); unexpected columns; column order differs |
| merc.csv     | tax          | yes             | yes                             | none                                                      |
| skoda.csv    | tax          | yes             | yes                             | none                                                      |
| toyota.csv   | tax          | yes             | yes                             | none                                                      |
| vauxhall.csv | tax          | yes             | yes                             | none                                                      |
| vw.csv       | tax          | yes             | yes                             | none                                                      |
| cclass.csv   | missing      | no              | no                              | missing tax; missing mpg; column order differs            |
| focus.csv    | missing      | no              | no                              | missing tax; missing mpg; column order differs            |

The complete sources share the same nine fields except that `hyundi.csv` uses `tax(£)` instead of `tax`. The audit records this as a source-level difference to normalize later. `cclass.csv` and `focus.csv` omit both `tax` and `mpg`.

## Missing-data findings

The raw source files contain no blank cells in their existing columns. The legacy files still have analytical fields unavailable by schema: `tax` and `mpg`. These are structural omissions, not evidence that the values are zero.

| source     | column   |   missing_count |   missing_pct |
|------------|----------|-----------------|---------------|
| cclass.csv | tax      |            3899 |           100 |
| cclass.csv | mpg      |            3899 |           100 |
| focus.csv  | tax      |            5454 |           100 |
| focus.csv  | mpg      |            5454 |           100 |

## Duplicate findings

Exact duplicate rows occur within several source files. The canonical candidate has 1,475 duplicate rows under the raw normalized candidate view. There is no listing identifier, so duplicate-looking rows are not removed during the audit. A duplicate policy must be approved during cleaning.

## Category findings

Observed fuel types and transmission values are preserved, including `Other` and `Electric` where present. Unknown categories must be reported rather than silently recoded.

| category_column   | category_value   |   count |
|-------------------|------------------|---------|
| fuel_type         | Diesel           |   40928 |
| fuel_type         | Electric         |       6 |
| fuel_type         | Hybrid           |    3078 |
| fuel_type         | Other            |     247 |
| fuel_type         | Petrol           |   54928 |
| transmission      | Automatic        |   20056 |
| transmission      | Manual           |   56445 |
| transmission      | Other            |       9 |
| transmission      | Semi-Auto        |   22677 |

## Range and validity findings

The candidate source set has year range 1970–2060, price range £450.00–£159,999.00, and mileage range 1–323,000. Zero annual tax is observed and remains valid for the required exercise. Zero engine sizes require investigation and must not be silently changed.

The audit found 1 year value after the fixed reference year 2024. Broad review flags are diagnostic only and do not automatically invalidate records. Outliers should be described with IQR or percentile analysis rather than deleted merely for being extreme.

| source                       |   row_count |   exact_duplicate_rows |   zero_tax_count |   zero_engine_size_count |   future_year_count |   review_flag_count |
|------------------------------|-------------|------------------------|------------------|--------------------------|---------------------|---------------------|
| audi.csv                     |       10668 |                    103 |              536 |                       57 |                   0 |                  18 |
| bmw.csv                      |       10781 |                    117 |              340 |                       47 |                   0 |                  58 |
| ford.csv                     |       17965 |                    154 |             2153 |                       51 |                   1 |                   1 |
| hyundi.csv                   |        4860 |                     86 |              136 |                       47 |                   0 |                   7 |
| merc.csv                     |       13119 |                    259 |              172 |                       12 |                   0 |                  33 |
| skoda.csv                    |        6267 |                     79 |              217 |                        5 |                   0 |                   0 |
| toyota.csv                   |        6738 |                     39 |             1790 |                        6 |                   0 |                  11 |
| vauxhall.csv                 |       13632 |                    374 |              360 |                       33 |                   0 |                   0 |
| vw.csv                       |       15157 |                    264 |              590 |                       15 |                   0 |                   1 |
| cclass.csv                   |        3899 |                    102 |                0 |                        1 |                   0 |                   0 |
| focus.csv                    |        5454 |                    696 |                0 |                       12 |                   0 |                   0 |
| canonical_candidate_combined |       99187 |                   1475 |             6294 |                      273 |                   1 |                 129 |

## Legacy-file assessment

| legacy_file   | manufacturer_file   |   legacy_row_count |   manufacturer_scope_row_count |   exact_matching_instances |   legacy_unmatched_instances |   manufacturer_scope_unmatched_instances | recommendation                 |
|---------------|---------------------|--------------------|--------------------------------|----------------------------|------------------------------|------------------------------------------|--------------------------------|
| cclass.csv    | merc.csv            |               3899 |                           3747 |                       3594 |                          305 |                                      153 | exclude from canonical dataset |
| focus.csv     | ford.csv            |               5454 |                           4588 |                       4361 |                         1093 |                                      227 | exclude from canonical dataset |

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

audi.csv, bmw.csv, ford.csv, hyundi.csv, merc.csv, skoda.csv, toyota.csv, vauxhall.csv, vw.csv

Excluded legacy sources: `cclass.csv` and `focus.csv`.
