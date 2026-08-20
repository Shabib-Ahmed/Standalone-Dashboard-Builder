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
    ("bar",         {"x": "Bucket", "y": "Metric", "color": "Group"}),
    ("grouped_bar", {"x": "Bucket", "y": "Metric", "color": "Group"}),
    ("single_line", {"x": "Bucket", "y_default": "Metric", "color_col": "Group"}),
    ("multi_line",  {"x": "Bucket", "y_default": "Metric", "color_col": "Group"}),
    ("scatter",     {"x": "Metric", "y": "Error",    "color": "Group"}),
    ("box",         {"x": "Group",  "y": "Metric"}),
    ("dual_axis_line", {"x": "Bucket", "y1": "Metric", "y2": "Error"}),
])
def test_chart_returns_valid_html(chart_df, method, extra_kwargs):
    fn = getattr(ChartBuilder, method)
    html = fn(chart_df, **extra_kwargs)
    assert_valid_html_fragment(html)


# ---------------------------------------------------------------------------
# Title injection
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("method,extra_kwargs", [
    ("bar",            {"x": "Bucket", "y": "Metric", "color": "Group"}),
    ("grouped_bar",    {"x": "Bucket", "y": "Metric", "color": "Group"}),
    ("single_line",    {"x": "Bucket", "y_default": "Metric", "color_col": "Group"}),
    ("multi_line",     {"x": "Bucket", "y_default": "Metric", "color_col": "Group"}),
    ("scatter",        {"x": "Metric", "y": "Error"}),
    ("box",            {"x": "Group",  "y": "Metric"}),
    ("dual_axis_line", {"x": "Bucket", "y1": "Metric", "y2": "Error"}),
])
def test_title_appears_in_output(chart_df, method, extra_kwargs):
    fn = getattr(ChartBuilder, method)
    html = fn(chart_df, title="TestTitle", **extra_kwargs)
    assert "TestTitle" in html


# ---------------------------------------------------------------------------
# bar
# ---------------------------------------------------------------------------

class TestBar:
    def test_error_y_accepted(self, chart_df):
        html = ChartBuilder.bar(
            chart_df, x="Bucket", y="Metric", color="Group", error_y="Error"
        )
        assert_valid_html_fragment(html)

    def test_text_col_accepted(self, chart_df):
        html = ChartBuilder.bar(
            chart_df, x="Bucket", y="Metric", color="Group", text="Metric"
        )
        assert_valid_html_fragment(html)

    def test_axis_labels_appear(self, chart_df):
        html = ChartBuilder.bar(
            chart_df, x="Bucket", y="Metric", color="Group",
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
            chart_df, x="Bucket", y="Metric", color="Group", error_y="Error"
        )
        assert_valid_html_fragment(html)

    def test_legend_title_appears(self, chart_df):
        html = ChartBuilder.grouped_bar(
            chart_df, x="Bucket", y="Metric", color="Group", legend_title="Series"
        )
        assert "Series" in html


# ---------------------------------------------------------------------------
# histogram
# ---------------------------------------------------------------------------

class TestHistogram:
    def test_returns_valid_html(self):
        s = pd.Series(["Group X", "Group X", "Group Y", "Group Z", "Group Y"])
        html = ChartBuilder.histogram(s, title="Group Distribution")
        assert_valid_html_fragment(html, title="Group Distribution")

    def test_empty_series_does_not_raise(self):
        s = pd.Series([], dtype=str)
        html = ChartBuilder.histogram(s)
        assert isinstance(html, str)

    def test_x_label_appears(self):
        s = pd.Series(["X", "Y", "A"])
        html = ChartBuilder.histogram(s, x_label="Label")
        assert "Label" in html


# ---------------------------------------------------------------------------
# table
# ---------------------------------------------------------------------------

class TestTable:
    def test_returns_valid_html(self, chart_df):
        html = ChartBuilder.table(chart_df, title="Summary Table")
        assert_valid_html_fragment(html, title="Summary Table")

    def test_drop_cols_removes_column(self, chart_df):
        html = ChartBuilder.table(chart_df, drop_cols=["Error"])
        # The "Error" header should not appear in the rendered table
        assert "Error" not in html

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
            x="Bucket",
            y_default="Metric",
            color_col="Group",
            y_options=["Metric", "Error"],
        )
        assert_valid_html_fragment(html)

    def test_multi_line_y_options_accepted(self, chart_df):
        html = ChartBuilder.multi_line(
            chart_df,
            x="Bucket",
            y_default="Metric",
            color_col="Group",
            y_options=["Metric", "Error"],
        )
        assert_valid_html_fragment(html)


# ---------------------------------------------------------------------------
# scatter
# ---------------------------------------------------------------------------

class TestScatter:
    def test_size_col_accepted(self, chart_df):
        html = ChartBuilder.scatter(
            chart_df, x="Metric", y="Error", color="Group", size="Size"
        )
        assert_valid_html_fragment(html)

    def test_no_color_accepted(self, chart_df):
        html = ChartBuilder.scatter(chart_df, x="Metric", y="Error")
        assert_valid_html_fragment(html)


# ---------------------------------------------------------------------------
# dual_axis_line
# ---------------------------------------------------------------------------

class TestDualAxisLine:
    def test_both_axis_labels_appear(self, chart_df):
        html = ChartBuilder.dual_axis_line(
            chart_df,
            x="Bucket", y1="Metric", y2="Error",
            y1_label="yvalue1", y2_label="yvalue2",
        )
        assert "yvalue1" in html
        assert "yvalue2" in html


# ---------------------------------------------------------------------------
# box
# ---------------------------------------------------------------------------

class TestBox:
    def test_color_col_accepted(self, chart_df):
        html = ChartBuilder.box(chart_df, x="Group", y="Metric", color="Group")
        assert_valid_html_fragment(html)

    def test_axis_labels_appear(self, chart_df):
        html = ChartBuilder.box(
            chart_df, x="Group", y="Metric",
            x_label="Series", y_label="Count"
        )
        assert "Series" in html
        assert "Count" in html
