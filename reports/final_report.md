# Used Car Prices Analysis

## 1. Executive Summary

The final canonical dataset contains 99,186 cleaned UK used-car listings from nine manufacturer-level source files. One invalid Ford record with year `2060` was rejected. The dataset contains nine brands and 195 unique model labels.

Average prices were £14,775.20 for Petrol, £19,339.49 for Diesel, and £19,289.59 for Hybrid. Mileage and price had a Pearson correlation of −0.417946 and a Spearman correlation of −0.511608. These results indicate a negative association, but correlation does not prove that mileage alone causes price changes.

There were 2,596 Diesel listings with zero annual tax, equal to 6.34% of all Diesel listings. The three most common model labels were Fiesta, Golf, and Focus.

## 2. Project Objectives

This project was designed to audit, clean, integrate, analyze, and visualize used-car listing data using Python, Pandas, NumPy, SciPy, Matplotlib, JupyterLab, reusable modules, Pytest, and Markdown reporting.

The required analytical questions were:

- Average price by fuel type.
- Mileage-price correlation.
- Listing counts and median prices by transmission.
- Diesel listings with zero annual tax.
- Price distributions across brands.
- Three most common models.
- Vehicle age using the fixed formula `vehicle_age = 2024 - year`.
- Average price by vehicle age.

## 3. Dataset Overview

The repository contained 11 raw CSV files and 108,540 rows. The canonical candidate used nine complete manufacturer-level files and contained 99,187 rows before cleaning. The final cleaned dataset contains 99,186 rows.

The final data covers years 1970–2020. Vehicle age ranges from 4 to 54 years as of the fixed reference year 2024. There are nine brands and 195 unique model labels.

Detailed summaries are available in [`dataset_overview.csv`](tables/dataset_overview.csv), [`raw_data_manifest.csv`](tables/raw_data_manifest.csv), and [`numeric_distribution_summary.csv`](tables/numeric_distribution_summary.csv).

## 4. Data Integration Decisions

The canonical source mapping is explicit:

| Source | Brand |
|---|---|
| `audi.csv` | Audi |
| `bmw.csv` | BMW |
| `ford.csv` | Ford |
| `hyundi.csv` | Hyundai |
| `merc.csv` | Mercedes-Benz |
| `skoda.csv` | Skoda |
| `toyota.csv` | Toyota |
| `vauxhall.csv` | Vauxhall |
| `vw.csv` | Volkswagen |

`hyundi.csv` retains its original raw filename. Its brand is normalized explicitly to Hyundai, and its `tax(£)` column is renamed to `tax` only in derived data.

`cclass.csv` and `focus.csv` were excluded. They are model-only files that omit `tax` and `mpg`, overlap their broader manufacturer files, and could overrepresent Mercedes-Benz C Class and Ford Focus listings. The overlap audit found 3,594 exact matching C Class instances and 4,361 exact matching Focus instances.

## 5. Data Quality and Cleaning

Raw files were preserved byte-for-byte. SHA-256 comparisons against the original Git contents passed for all 11 files.

The raw audit found no blank cells in fields present in the source files. It identified leading model whitespace, source schema differences, within-file duplicates, zero engine-size values, and one future-year record.

Cleaning decisions were:

- Trim `model`, `transmission`, and fuel-type strings.
- Preserve model capitalization.
- Convert numeric fields with conversion diagnostics.
- Retain `tax == 0`.
- Reject the Ford record with year `2060` because the fixed validity rule requires year no greater than 2024.
- Do not remove duplicate-looking rows because no unique listing identifier exists.
- Do not remove statistical outliers.

The reconciliation was:

```text
99,187 raw canonical rows
-      1 rejected row
-      0 duplicate removals
= 99,186 final cleaned rows
```

See [`data_quality_report.md`](data_quality_report.md), [`cleaning_summary.csv`](tables/cleaning_summary.csv), and [`rejected_rows.csv`](../data/interim/rejected_rows.csv).

## 6. Average Price by Fuel Type

| Fuel type | Listings | Average price | Median price |
|---|---:|---:|---:|
| Petrol | 54,927 | £14,775.20 | £12,000.00 |
| Diesel | 40,928 | £19,339.49 | £17,097.00 |
| Hybrid | 3,078 | £19,289.59 | £18,298.00 |

Diesel and Hybrid have higher average and median listing prices than Petrol in this dataset. This is descriptive and may reflect differences in brand, model, age, equipment, and sample composition.

See [`price_by_fuel_type.csv`](tables/price_by_fuel_type.csv), [`price_by_fuel_type_required.csv`](tables/price_by_fuel_type_required.csv), and [`average_price_by_fuel_type.png`](figures/average_price_by_fuel_type.png).

## 7. Mileage and Price Correlation

| Measure | Value | Observations |
|---|---:|---:|
| Pearson correlation | −0.417946 | 99,186 |
| Spearman correlation | −0.511608 | 99,186 |

Both coefficients are negative. Higher mileage tends to be associated with lower listing price. Pearson measures linear association, while Spearman measures monotonic rank association. The stronger negative Spearman value suggests that the rank relationship is more consistent than a strictly linear relationship.

Outliers can affect Pearson correlation. Neither coefficient proves causation, and mileage is not the only factor related to price.

See [`mileage_price_correlation.csv`](tables/mileage_price_correlation.csv), [`mileage_price_correlation_by_brand.csv`](tables/mileage_price_correlation_by_brand.csv), and [`mileage_vs_price_scatter.png`](figures/mileage_vs_price_scatter.png).

## 8. Transmission Analysis

| Transmission | Listings | Median price | Average price |
|---|---:|---:|---:|
| Automatic | 20,055 | £19,297.00 | £21,558.97 |
| Manual | 56,445 | £11,000.00 | £12,112.06 |
| Other | 9 | £15,999.00 | £16,219.11 |
| Semi-Auto | 22,677 | £22,383.00 | £24,284.03 |

Manual listings are the most common. Semi-Auto listings have the highest median price among the observed transmission categories. Category size and brand/model composition should be considered before interpreting these differences.

See [`transmission_summary.csv`](tables/transmission_summary.csv), [`car_count_by_transmission.png`](figures/car_count_by_transmission.png), and [`median_price_by_transmission.png`](figures/median_price_by_transmission.png).

## 9. Diesel Cars with Zero Tax

There are 2,596 Diesel listings with annual tax equal to zero. This is 6.342846% of the 40,928 Diesel listings. Their median price is £9,063.50 and median mileage is 41,066.5.

The zero-tax value is retained as a valid analytical value. This report does not infer a tax-policy explanation from the dataset alone.

See [`diesel_zero_tax_summary.csv`](tables/diesel_zero_tax_summary.csv), [`diesel_zero_tax_by_brand.csv`](tables/diesel_zero_tax_by_brand.csv), and [`diesel_zero_tax_cars.csv`](tables/diesel_zero_tax_cars.csv).

## 10. Price Distribution Across Brands

Brand medians range from £9,999 for Vauxhall to £22,480 for Mercedes-Benz. BMW and Audi also have relatively high medians at £20,462 and £20,200 respectively.

The box plot sorts brands by median price and hides outlier points only for readability. No observations were removed from the dataset or analytical calculations.

See [`brand_price_distribution.csv`](tables/brand_price_distribution.csv) and [`price_distribution_by_brand.png`](figures/price_distribution_by_brand.png).

## 11. Most Common Models

The three most common raw model labels are:

| Rank | Model | Listings |
|---:|---|---:|
| 1 | Fiesta | 6,556 |
| 2 | Golf | 4,863 |
| 3 | Focus | 4,588 |

The matching top brand-model pairs are Ford Fiesta, Volkswagen Golf, and Ford Focus. Both raw-label and brand-model tables are provided because model names can theoretically occur across brands.

See [`top_models.csv`](tables/top_models.csv), [`top_brand_model_pairs.csv`](tables/top_brand_model_pairs.csv), and [`top_three_models.png`](figures/top_three_models.png).

## 12. Vehicle Age and Average Price

Vehicle age was calculated exactly as:

```python
vehicle_age = 2024 - year
```

The enriched data contains 26 observed age groups from 4 to 54 years. The complete age table retains every observed group, including small groups, and is sorted by age.

See [`price_by_vehicle_age.csv`](tables/price_by_vehicle_age.csv) and [`average_price_by_vehicle_age.png`](figures/average_price_by_vehicle_age.png).

Age groups with few listings should not be treated as equally reliable. Vehicle age is fixed as of 2024 and is not current age.

## 13. Additional Findings

The largest brand groups are Ford with 17,964 listings, Volkswagen with 15,157, and Vauxhall with 13,632. Hyundai is the smallest canonical group with 4,860 listings. This imbalance matters for cross-brand comparisons and correlations.

The overall mean price of £16,805.45 exceeds the median of £14,495.00, supporting the conclusion that prices are right-skewed. Median values can therefore describe a typical listing more robustly than means in some comparisons.

See [`listing_count_by_brand.csv`](tables/listing_count_by_brand.csv), [`price_summary_by_brand.csv`](tables/price_summary_by_brand.csv), and [`mileage_summary_by_brand.csv`](tables/mileage_summary_by_brand.csv).

## 14. Limitations

- The records are listings, not confirmed sale transactions.
- Price may be influenced by features not present in the dataset.
- Vehicle condition is unavailable.
- Location is unavailable.
- Listing date is unavailable.
- Trim and optional equipment may not be fully represented.
- There is no unique listing identifier.
- Dataset brands have unequal sample sizes.
- Cross-brand correlation can be confounded by brand and model mix.
- Pearson correlation is sensitive to outliers.
- `vehicle_age` is fixed as of 2024.
- Currency and unit assumptions come from the dataset context.
- `cclass.csv` and `focus.csv` require special treatment.
- Zero tax should not be given a policy explanation without separate evidence.

## 15. Recommendations

1. Use median prices alongside means when comparing categories with skewed distributions.
2. Report listing counts with every category-level price comparison.
3. Treat mileage-price correlation as descriptive and consider brand/model mix in any further analysis.
4. Review low-count age and transmission categories cautiously.
5. Preserve the raw-data hash manifest when reproducing the analysis.
6. Obtain transaction, condition, location, and listing-date data before making market or pricing claims.

## 16. Conclusion

The project delivers a reproducible used-car analytics workflow from immutable raw files through audit, cleaning, feature engineering, analytical tables, visualizations, automated tests, and final reporting. The canonical dataset and outputs answer all guiding exercises while documenting the major data-quality decisions and limitations.
