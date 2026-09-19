# Used Car Prices Analytics

This repository is a reproducible Python data-analytics project for UK used-car listing data. It uses Pandas, NumPy, Matplotlib, SciPy, JupyterLab, and Pytest to audit, clean, integrate, analyze, visualize, and report on manufacturer-level source files.

This is an analytics project, not a machine-learning application. It contains no predictive models, database, dashboard, or web application.

## Analytical questions

The project answers these questions:

- What are average and median prices by fuel type, especially Petrol, Diesel, and Hybrid?
- What is the relationship between mileage and price?
- How many listings and what median prices occur within each transmission category?
- How many Diesel listings have annual tax equal to zero?
- How are price distributions different across brands?
- Which three model labels are most common?
- How does average price vary by vehicle age as of the fixed reference year 2024?

## Repository inspection summary

The raw repository contains 11 CSV files and 108,540 listing rows. Nine complete manufacturer-level files contain 99,187 candidate rows. Two model-only legacy files are kept for audit purposes but excluded from the canonical dataset.

The final cleaned dataset contains 99,186 rows. One Ford record with year `2060` was rejected because the assignment validation rule requires `year <= 2024`.

## Data source and canonical file decision

Included canonical sources:

| Raw file | Derived brand |
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

Excluded legacy sources:

- `cclass.csv`: Mercedes C Class only, missing `tax` and `mpg`, overlaps `merc.csv`.
- `focus.csv`: Ford Focus only, missing `tax` and `mpg`, overlaps `ford.csv`.

The raw filename `hyundi.csv` is preserved. Its derived brand is explicitly normalized to Hyundai, and its `tax(£)` column is normalized during loading without editing the raw file.

## Data dictionary

| Column | Meaning and convention |
|---|---|
| `brand` | Manufacturer derived from the explicit source mapping |
| `model` | Vehicle model, trimmed but not title-cased |
| `year` | Source vehicle year |
| `vehicle_age` | `2024 - year`; age as of the fixed reference year 2024 |
| `price` | Listing price, assumed GBP from the dataset context |
| `transmission` | Transmission category |
| `mileage` | Mileage, assumed miles from the dataset context |
| `fuel_type` | Fuel category |
| `tax` | Annual vehicle tax, assumed GBP from the dataset context |
| `mpg` | Miles per gallon |
| `engine_size` | Engine size, assumed litres |
| `source_file` | Original raw filename |

Currency and unit descriptions are source conventions, not independently verified measurements.

## Project structure

```text
used-car/
├── data/
│   ├── raw/          # Immutable source CSV files
│   ├── interim/      # Rejected-row output
│   └── processed/    # Cleaned and enriched datasets
├── notebooks/        # Ordered Jupyter analysis notebooks
├── src/              # Reusable configuration, audit, cleaning, analysis, and plotting code
├── reports/
│   ├── figures/      # PNG charts
│   ├── tables/       # Final analytical tables
│   ├── data_quality_report.md
│   └── final_report.md
├── tests/            # Pytest unit and integration tests
├── main.py           # Reproducible command-line pipeline
├── requirements.txt
├── pytest.ini
└── README.md
```

## Python requirements

The project targets Python 3.12 or a compatible newer Python 3 release. Required packages are listed in `requirements.txt`:

- pandas
- numpy
- matplotlib
- scipy
- jupyterlab
- ipykernel
- pytest
- nbformat
- nbconvert
- tabulate

## Environment setup

### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## JupyterLab kernel setup

After activating the virtual environment:

```bash
python -m ipykernel install \
  --user \
  --name used-car-analysis \
  --display-name "Python (Used Car Analysis)"
```

Launch JupyterLab from the repository root:

```bash
jupyter lab
```

## Notebook execution order

1. `notebooks/01_data_audit.ipynb`
2. `notebooks/02_cleaning_and_integration.ipynb`
3. `notebooks/03_eda_and_feature_engineering.ipynb`
4. `notebooks/04_guiding_exercises.ipynb`
5. `notebooks/05_visualizations.ipynb`
6. `notebooks/06_final_report.ipynb`

Each notebook calls reusable functions from `src/` and should be run from a kernel started at the repository root.

## Pipeline commands

Run these commands from the repository root:

```bash
python main.py audit
python main.py build
python main.py analyze
python main.py plot
python main.py all
```

`python main.py all` regenerates the audit manifest, verifies raw files, builds the cleaned and enriched datasets, creates analytical tables, and generates all required figures. The pipeline is idempotent for unchanged raw data.

## Testing

```bash
pytest -q
```

The current test suite contains 31 passing tests covering source selection, cleaning, validation, vehicle age, analytical calculations, plotting, and pipeline integration.

## Generated outputs

- `data/interim/rejected_rows.csv`: traceable rejected records.
- `data/processed/used_cars_clean.csv`: canonical cleaned data.
- `data/processed/used_cars_enriched.csv`: cleaned data with vehicle age.
- `reports/tables/`: manifests, quality audits, cleaning reconciliation, analytical tables, and summaries.
- `reports/figures/`: eight Matplotlib PNG figures.
- `reports/data_quality_report.md`: raw-data audit narrative.
- `reports/final_report.md`: final analytical report.

## Key findings

- Final cleaned listings: 99,186.
- Brands represented: 9.
- Unique model labels: 195.
- Year range: 1970–2020.
- Vehicle age as of 2024: 4–54 years.
- Mean price: £16,805.45; median price: £14,495.00.
- Petrol average price: £14,775.20.
- Diesel average price: £19,339.49.
- Hybrid average price: £19,289.59.
- Mileage-price Pearson correlation: −0.417946.
- Mileage-price Spearman correlation: −0.511608.
- Diesel zero-tax listings: 2,596, or 6.34% of Diesel listings.
- Most common models: Fiesta, Golf, and Focus.

These are associations and descriptive summaries of listings, not causal or transaction-level conclusions.

## Data-quality decisions

- Raw data remains immutable and is monitored using SHA-256 hashes.
- Source selection is explicit; no blind CSV glob is used for canonical integration.
- Leading/trailing whitespace is trimmed from relevant strings.
- Model capitalization is preserved.
- `tax(£)` is renamed to `tax` only in derived data.
- Zero tax is valid and retained.
- One future-year record is rejected and documented.
- Duplicate-looking rows are reported but not removed because there is no listing identifier and no approved deduplication rule.
- Outliers are summarized with IQR metrics and retained.

## Limitations

- Records are listings, not confirmed sale transactions.
- Price may be influenced by vehicle features not represented in the data.
- Vehicle condition, location, listing date, trim, and optional equipment are unavailable.
- There is no unique listing identifier.
- Brands have unequal sample sizes.
- Cross-brand correlation can be confounded by brand and model mix.
- Pearson correlation is sensitive to outliers.
- `vehicle_age` is fixed as of 2024.
- Currency and unit assumptions come from the dataset context.
- `cclass.csv` and `focus.csv` require special treatment.
- Zero tax is not given a policy explanation without separate evidence.

## Reproducibility notes

- Raw input files are under `data/raw/` and should not be edited.
- The canonical source mapping and all project paths are defined in `src/config.py`.
- The raw manifest records file sizes, SHA-256 hashes, schemas, row counts, and inclusion decisions.
- Numeric calculations retain full precision; rounding is applied only for presentation.
- No random sampling is used in the required scatter plot.
- Repeated `python main.py all` runs produce stable outputs for unchanged raw data.
