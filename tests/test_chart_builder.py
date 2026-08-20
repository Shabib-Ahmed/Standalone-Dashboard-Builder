import pandas as pd
import pytest

from dashlib.ChartBuilder import ChartBuilder 

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def assert_valid_html_fragment(html: str, title: str = "") -> None:
    """Common assertions applied to every ChartBuilder output."""
    assert isinstance(html, str), "Output must be a string"
    assert len(html) > 0, "Output must not be empty"
    assert "<div" in html, "Output must contain at least one <div>"
    if title:
        assert title in html, f"Title '{title}' not found in output"


# ---------------------------------------------------------------------------
# Parametrized smoke tests — one call per chart method
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("method,extra_kwargs", [
    ("bar",         {"x": "Month", "y": "Value", "color": "Ward"}),
    ("grouped_bar", {"x": "Month", "y": "Value", "color": "Ward"}),
    ("single_line", {"x": "Month", "y_default": "Value", "color_col": "Ward"}),
    ("multi_line",  {"x": "Month", "y_default": "Value", "color_col": "Ward"}),
    ("scatter",     {"x": "Value", "y": "CI",    "color": "Ward"}),
    ("box",         {"x": "Ward",  "y": "Value"}),
    ("dual_axis_line", {"x": "Month", "y1": "Value", "y2": "CI"}),
])
def test_chart_returns_valid_html(chart_df, method, extra_kwargs):
    fn = getattr(ChartBuilder, method)
    html = fn(chart_df, **extra_kwargs)
    assert_valid_html_fragment(html)


# ---------------------------------------------------------------------------
# Title injection
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("method,extra_kwargs", [
    ("bar",            {"x": "Month", "y": "Value", "color": "Ward"}),
    ("grouped_bar",    {"x": "Month", "y": "Value", "color": "Ward"}),
    ("single_line",    {"x": "Month", "y_default": "Value", "color_col": "Ward"}),
    ("multi_line",     {"x": "Month", "y_default": "Value", "color_col": "Ward"}),
    ("scatter",        {"x": "Value", "y": "CI"}),
    ("box",            {"x": "Ward",  "y": "Value"}),
    ("dual_axis_line", {"x": "Month", "y1": "Value", "y2": "CI"}),
])
def test_title_appears_in_output(chart_df, method, extra_kwargs):
    fn = getattr(ChartBuilder, method)
    html = fn(chart_df, title="WardMetric", **extra_kwargs)
    assert "WardMetric" in html


# ---------------------------------------------------------------------------
# bar
# ---------------------------------------------------------------------------

class TestBar:
    def test_error_y_accepted(self, chart_df):
        html = ChartBuilder.bar(
            chart_df, x="Month", y="Value", color="Ward", error_y="CI"
        )
        assert_valid_html_fragment(html)

    def test_text_col_accepted(self, chart_df):
        html = ChartBuilder.bar(
            chart_df, x="Month", y="Value", color="Ward", text="Value"
        )
        assert_valid_html_fragment(html)

    def test_axis_labels_appear(self, chart_df):
        html = ChartBuilder.bar(
            chart_df, x="Month", y="Value", color="Ward",
            x_label="X-Axis", y_label="Y-Axis"
        )
        assert "X-Axis" in html
        assert "Y-Axis" in html


# ---------------------------------------------------------------------------
# grouped_bar
# ---------------------------------------------------------------------------

class TestGroupedBar:
    def test_error_y_accepted(self, chart_df):
        html = ChartBuilder.grouped_bar(
            chart_df, x="Month", y="Value", color="Ward", error_y="CI"
        )
        assert_valid_html_fragment(html)

    def test_legend_title_appears(self, chart_df):
        html = ChartBuilder.grouped_bar(
            chart_df, x="Month", y="Value", color="Ward", legend_title="Department"
        )
        assert "Department" in html


# ---------------------------------------------------------------------------
# histogram
# ---------------------------------------------------------------------------

class TestHistogram:
    def test_returns_valid_html(self):
        s = pd.Series(["Ward A", "Ward A", "Ward B", "Ward C", "Ward B"])
        html = ChartBuilder.histogram(s, title="Ward Distribution")
        assert_valid_html_fragment(html, title="Ward Distribution")

    def test_empty_series_does_not_raise(self):
        s = pd.Series([], dtype=str)
        html = ChartBuilder.histogram(s)
        assert isinstance(html, str)

    def test_x_label_appears(self):
        s = pd.Series(["A", "B", "A"])
        html = ChartBuilder.histogram(s, x_label="Category")
        assert "Category" in html


# ---------------------------------------------------------------------------
# table
# ---------------------------------------------------------------------------

class TestTable:
    def test_returns_valid_html(self, chart_df):
        html = ChartBuilder.table(chart_df, title="Summary Table")
        assert_valid_html_fragment(html, title="Summary Table")

    def test_drop_cols_removes_column(self, chart_df):
        html = ChartBuilder.table(chart_df, drop_cols=["CI"])
        # The "CI" header should not appear in the rendered table
        assert "CI" not in html

    def test_all_column_names_present_by_default(self, chart_df):
        html = ChartBuilder.table(chart_df)
        for col in chart_df.columns:
            assert col in html, f"Column '{col}' not found in table output"


# ---------------------------------------------------------------------------
# single_line / multi_line
# ---------------------------------------------------------------------------

class TestLineCharts:
    def test_single_line_y_options_accepted(self, chart_df):
        html = ChartBuilder.single_line(
            chart_df,
            x="Month",
            y_default="Value",
            color_col="Ward",
            y_options=["Value", "CI"],
        )
        assert_valid_html_fragment(html)

    def test_multi_line_y_options_accepted(self, chart_df):
        html = ChartBuilder.multi_line(
            chart_df,
            x="Month",
            y_default="Value",
            color_col="Ward",
            y_options=["Value", "CI"],
        )
        assert_valid_html_fragment(html)


# ---------------------------------------------------------------------------
# scatter
# ---------------------------------------------------------------------------

class TestScatter:
    def test_size_col_accepted(self, chart_df):
        html = ChartBuilder.scatter(
            chart_df, x="Value", y="CI", color="Ward", size="Size"
        )
        assert_valid_html_fragment(html)

    def test_no_color_accepted(self, chart_df):
        html = ChartBuilder.scatter(chart_df, x="Value", y="CI")
        assert_valid_html_fragment(html)


# ---------------------------------------------------------------------------
# dual_axis_line
# ---------------------------------------------------------------------------

class TestDualAxisLine:
    def test_both_axis_labels_appear(self, chart_df):
        html = ChartBuilder.dual_axis_line(
            chart_df,
            x="Month", y1="Value", y2="CI",
            y1_label="Falls", y2_label="Pressure",
        )
        assert "Falls" in html
        assert "Pressure" in html


# ---------------------------------------------------------------------------
# box
# ---------------------------------------------------------------------------

class TestBox:
    def test_color_col_accepted(self, chart_df):
        html = ChartBuilder.box(chart_df, x="Ward", y="Value", color="Ward")
        assert_valid_html_fragment(html)

    def test_axis_labels_appear(self, chart_df):
        html = ChartBuilder.box(
            chart_df, x="Ward", y="Value",
            x_label="Department", y_label="Incidents"
        )
        assert "Department" in html
        assert "Incidents" in html
