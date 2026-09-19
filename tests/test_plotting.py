import matplotlib

matplotlib.use("Agg")

import pandas as pd
import matplotlib.pyplot as plt

from src.analysis import build_guiding_exercise_outputs
from src.plotting import create_required_figures


def test_create_required_figures_saves_all_charts_and_closes_figures(tmp_path):
    dataframe = pd.DataFrame(
        {
            "brand": ["Audi", "BMW", "Ford", "Audi", "BMW", "Ford"],
            "model": ["A1", "i3", "Focus", "A1", "i3", "Focus"],
            "year": [2020, 2019, 2018, 2017, 2016, 2015],
            "vehicle_age": [4, 5, 6, 7, 8, 9],
            "price": [10000, 20000, 8000, 9000, 18000, 7000],
            "transmission": ["Manual", "Automatic", "Manual", "Manual", "Automatic", "Manual"],
            "mileage": [1000, 2000, 3000, 4000, 5000, 6000],
            "fuel_type": ["Petrol", "Hybrid", "Diesel", "Petrol", "Hybrid", "Diesel"],
            "tax": [0, 100, 0, 100, 100, 10],
            "mpg": [50, 60, 55, 50, 60, 55],
            "engine_size": [1.0, 0.0, 1.5, 1.0, 0.0, 1.5],
            "source_file": ["audi.csv", "bmw.csv", "ford.csv", "audi.csv", "bmw.csv", "ford.csv"],
        }
    )
    outputs = build_guiding_exercise_outputs(dataframe)
    paths = create_required_figures(dataframe, outputs, output_dir=tmp_path)
    assert len(paths) == 8
    assert all(path.is_file() and path.stat().st_size > 0 for path in paths.values())
    assert plt.get_fignums() == []
