# dashboard-builder

A Python library for generating self-contained interactive HTML dashboards with [Plotly](https://plotly.com/python/) charts, summary statistics, and unit-comparison views with confidence intervals.


## What it does

- **ChartBuilder** — static methods that return Plotly HTML fragments: tables, grouped bar charts, histograms, and multi-series line charts with optional metric-switcher dropdowns.
- **StatsHelper** — grouped aggregations (mean, median, std, IQR, percentiles, …) and comparison data with 95% confidence intervals via Welch's t-test.
- **DashboardBuilder** — collects sections and tabs, wires up a comparison view, and renders everything into a single HTML file from a template.

## Quick start

```bash
git clone https://github.com/Shabib-Ahmed/dashboard-builder.git
cd dashboard-builder
pip install -r requirements.txt
```

## Usage

```python
from dashboard import DashboardBuilder, ChartBuilder, StatsHelper

db = DashboardBuilder("My Dashboard")

sec = db.add_section("unit_a", "Unit A", date_range=("Jan 01", "Dec 31"))
sec.add_tab("overview", "Overview", ChartBuilder.table(df))
sec.add_tab("trend",    "Trend",    ChartBuilder.grouped_bar(
    trend_df, x="Month", y="Average", color="Shift",
    title="Average Workload by Shift",
))

# Optional: add a comparison view with CI tables
comp = StatsHelper.comparison_data(
    df, group_col="Unit", value_col="Workload",
    groups=["Unit A", "Unit B"], bucket_col="Month",
)
db.set_comparison(comp, groups=["Unit A", "Unit B"],
                  filter_keys=["Day", "Night"], filter_label="Shift")

db.save("output.html")
```

## Project structure

```
├── dashboard.py        # Core library — ChartBuilder, StatsHelper, DashboardBuilder
├── template.html       # HTML template rendered by DashboardBuilder
├── requirements.txt    # Python dependencies
└── Example/
    └── demo_dashboard.py   # Generates a sample dashboard from synthetic data
```

## Dependencies

- Python 3.8+
- pandas
- plotly
- scipy
