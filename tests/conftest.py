import pandas as pd
import numpy as np
import pytest


@pytest.fixture
def ward_df():
    """Row-level DataFrame: categorical group, time bucket, numeric metric, margin column."""
    return pd.DataFrame({
        "Group":  ["X", "X", "X", "Y", "Y", "Z"],
        "Bucket": ["P1", "P2", "P3", "P1", "P2", "P1"],
        "Metric": [10.0, 20.0, 30.0, 40.0, 50.0, 60.0],
        "Error":  [0.5,  1.0,  1.5,  2.0,  2.5,  3.0],
    })


@pytest.fixture
def summary_df():
    """Pre-aggregated summary DataFrame matching the shape returned by grouped_agg."""
    return pd.DataFrame({
        "Group":   ["X",   "Y",   "Z"],
        "Average": [20.0,  45.0,  60.0],
        "StdDev":  [10.0,   7.07,  0.0],
        "n":       [3,      2,     1],
    })


@pytest.fixture
def two_group_df():
    """Two-group DataFrame with a secondary bucket column, for comparison_data tests."""
    rng = np.random.default_rng(42)
    return pd.DataFrame({
        "Group":    ["X"] * 10 + ["Y"] * 10,
        "Category": (["Alpha", "Beta"] * 5) + (["Alpha", "Beta"] * 5),
        "Metric":   rng.uniform(1, 10, 20).round(2),
    })


@pytest.fixture
def chart_df():
    """Minimal DataFrame covering all column types required by ChartBuilder methods."""
    return pd.DataFrame({
        "Bucket": ["P1", "P2", "P3", "P1", "P2", "P3"],
        "Group":  ["X",  "X",  "X",  "Y",  "Y",  "Y"],
        "Metric": [1.5,  2.5,  3.5,  4.5,  5.5,  6.5],
        "Error":  [0.1,  0.2,  0.3,  0.4,  0.5,  0.6],
        "Size":   [10,   20,   30,   40,   50,   60],
    })
