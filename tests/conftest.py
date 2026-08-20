import pandas as pd
import numpy as np
import pytest


@pytest.fixture
def ward_df():
    """Minimal ward-level DataFrame used across multiple test modules."""
    return pd.DataFrame({
        "Ward":  ["A", "A", "A", "B", "B", "C"],
        "Month": ["Jan", "Feb", "Mar", "Jan", "Feb", "Jan"],
        "Value": [10.0, 20.0, 30.0, 40.0, 50.0, 60.0],
        "CI":    [0.5,  1.0,  1.5,  2.0,  2.5,  3.0],
    })


@pytest.fixture
def summary_df():
    """Pre-aggregated summary DataFrame (as returned by grouped_agg)."""
    return pd.DataFrame({
        "Ward":    ["A",   "B",   "C"],
        "Average": [20.0,  45.0,  60.0],
        "StdDev":  [10.0,   7.07,  0.0],
        "n":       [3,      2,     1],
    })


@pytest.fixture
def two_group_df():
    """DataFrame with two groups and a bucket column, for comparison_data tests."""
    rng = np.random.default_rng(42)
    return pd.DataFrame({
        "Ward":   ["A"] * 10 + ["B"] * 10,
        "Shift":  (["Day", "Night"] * 5) + (["Day", "Night"] * 5),
        "Value":  rng.uniform(1, 10, 20).round(2),
    })


@pytest.fixture
def chart_df():
    """Small DataFrame suitable for all ChartBuilder methods."""
    return pd.DataFrame({
        "Month":  ["Jan", "Feb", "Mar", "Jan", "Feb", "Mar"],
        "Ward":   ["A",   "A",   "A",   "B",   "B",   "B"],
        "Value":  [1.5,   2.5,   3.5,   4.5,   5.5,   6.5],
        "CI":     [0.1,   0.2,   0.3,   0.4,   0.5,   0.6],
        "Size":   [10,    20,    30,    40,    50,    60],
    })
