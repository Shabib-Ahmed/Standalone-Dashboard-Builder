import os
from html.parser import HTMLParser

import pytest

from dashlib.HtmlBuilder import ( 
    HTMLBuilder,
    ViewConfig,
    GraphRow,
    GraphConfig,
    BarOptions,
    LineOptions,
    ScatterOptions,
    DropdownControl,
    RangeInputControl,
)


# ---------------------------------------------------------------------------
# HTML parsing helpers
# ---------------------------------------------------------------------------

class HtmlInspector(HTMLParser):
    """Collect ids, tag names, and text content from rendered HTML."""

    def __init__(self):
        super().__init__()
        self.ids: list[str] = []
        self.tags: list[str] = []
        self._text_chunks: list[str] = []

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        attrs_dict = dict(attrs)
        if "id" in attrs_dict:
            self.ids.append(attrs_dict["id"])

    def handle_data(self, data):
        stripped = data.strip()
        if stripped:
            self._text_chunks.append(stripped)

    @property
    def text(self) -> str:
        return " ".join(self._text_chunks)


def parse_html(html: str) -> HtmlInspector:
    inspector = HtmlInspector()
    inspector.feed(html)
    return inspector


# ---------------------------------------------------------------------------
# Builder factories
# ---------------------------------------------------------------------------

from pathlib import Path

TEMPLATE_PATH = Path(__file__).parent.parent / "template.html"


def make_minimal_builder() -> HTMLBuilder:
    """Smallest valid HTMLBuilder — one section, no views."""
    template_html = TEMPLATE_PATH.read_text(encoding="utf-8")
    b = HTMLBuilder(
        title="Test Dashboard",
        main_tab_label="Overview",
        dropdown_label="Select Ward",
        plotly_version="5.18.0",
        template=template_html,
    )
    section = b.add_section("ward_a", "Ward A")
    section.add_tab("overview_tab", "Overview", "<p>Overview content.</p>")
    return b


def make_full_builder() -> HTMLBuilder:
    """Realistic dashboard with sections, views, controls, and multiple chart types."""
    template_html = TEMPLATE_PATH.read_text(encoding="utf-8")
    b = HTMLBuilder(
        title="Ward Safety Dashboard",
        main_tab_label="Overview",
        dropdown_label="Select Ward",
        plotly_version="5.18.0",
        template=template_html,
    )

    # Sections — tabs must exist before add_button / add_dropdown
    section_a = b.add_section("ward_a", "Ward A", date_range=("2024-01", "2024-12"))
    section_a.add_tab("summary_tab", "Summary", "<p>Placeholder</p>")
    section_b = b.add_section("ward_b", "Ward B")
    section_b.add_tab("metric_tab", "Metrics", "<p>Placeholder</p>")

    # Views
    bar_view = ViewConfig(
        key="falls_bar",
        tab_label="Falls Bar",
        heading="Falls by Month",
        description="Monthly fall counts per ward.",
        rows=[
            GraphRow(graphs=[
                GraphConfig(
                    div_id="falls_bar_chart",
                    options=BarOptions(
                        x_col="Month",
                        y_label="Falls",
                        title="Falls by Month",
                        barmode="group",
                    ),
                    height=450,
                )
            ], layout="stack")
        ],
        controls=[
            DropdownControl(
                control_id="ward_dropdown",
                label="Ward",
                options=["All", "Ward A", "Ward B"],
            )
        ],
    )

    line_view = ViewConfig(
        key="trend_line",
        tab_label="Trend",
        heading="Falls Trend Over Time",
        rows=[
            GraphRow(graphs=[
                GraphConfig(
                    div_id="trend_line_chart",
                    options=LineOptions(
                        x_col="Month",
                        y_label="Falls",
                        title="Trend",
                    ),
                )
            ])
        ],
    )

    scatter_view = ViewConfig(
        key="workload_scatter",
        tab_label="Workload",
        heading="Workload vs Falls",
        rows=[
            GraphRow(graphs=[
                GraphConfig(
                    div_id="scatter_chart",
                    options=ScatterOptions(
                        x_col="Workload",
                        y_col="Falls",
                        title="Correlation",
                        show_regression=True,
                        show_loess=True,
                        show_stats_badge=True,
                    ),
                )
            ])
        ],
        controls=[
            RangeInputControl(
                lo_id="workload_lo",
                hi_id="workload_hi",
                label="Workload Range",
                result_div_id="workload_result",
            )
        ],
    )

    b.add_view(bar_view)
    b.add_view(line_view)
    b.add_view(scatter_view)

    # Inline button content
    b.add_button(
        section_key="ward_a",
        tab_key="summary_tab",
        button_label="Summary",
        content_html="<p>Ward A summary content.</p>",
    )

    # Dropdown within a section tab
    b.add_dropdown(
        section_key="ward_b",
        tab_key="metric_tab",
        dropdown_id="metric_select",
        label="Metric",
        options=["Falls", "Pressure Injuries"],
    )

    return b


# ---------------------------------------------------------------------------
# render() — basic structure
# ---------------------------------------------------------------------------

class TestRenderDebug:
    def test_render_output_repr(self):
        """Temporary: print what render() actually returns to diagnose failures."""
        html = make_minimal_builder().render()
        print(f"\nrender() returned ({len(html)} chars): {repr(html[:200])}")
        assert True  # always passes — just for inspection


class TestRenderBasicStructure:
    def test_render_returns_string(self):
        html = make_minimal_builder().render()
        assert isinstance(html, str)

    def test_render_non_empty(self):
        html = make_minimal_builder().render()
        assert len(html) > 100

    def test_render_is_html_document(self):
        html = make_minimal_builder().render()
        assert "<html" in html.lower() or "<!doctype html" in html.lower()

    def test_render_has_head_and_body(self):
        html = make_minimal_builder().render().lower()
        assert "<head" in html
        assert "<body" in html

    def test_render_title_in_output(self):
        html = make_minimal_builder().render()
        assert "Test Dashboard" in html

    def test_render_plotly_version_referenced(self):
        html = make_minimal_builder().render()
        assert "5.18.0" in html


# ---------------------------------------------------------------------------
# render() — sections and tabs
# ---------------------------------------------------------------------------

class TestRenderSections:
    def test_section_label_present(self):
        html = make_full_builder().render()
        assert "Ward A" in html
        assert "Ward B" in html

    def test_date_range_present(self):
        html = make_full_builder().render()
        assert "2024-01" in html or "2024" in html  # formatted or raw

    def test_button_label_present(self):
        html = make_full_builder().render()
        assert "Summary" in html

    def test_button_content_present(self):
        html = make_full_builder().render()
        assert "Ward A summary content" in html

    def test_dropdown_options_present(self):
        html = make_full_builder().render()
        assert "Falls" in html
        assert "Pressure Injuries" in html


# ---------------------------------------------------------------------------
# render() — views
# ---------------------------------------------------------------------------

class TestRenderViews:
    def test_view_headings_present(self):
        html = make_full_builder().render()
        assert "Falls by Month" in html
        assert "Falls Trend Over Time" in html
        assert "Workload vs Falls" in html

    def test_view_tab_labels_present(self):
        html = make_full_builder().render()
        assert "Falls Bar" in html
        assert "Trend" in html
        assert "Workload" in html

    def test_view_description_present(self):
        html = make_full_builder().render()
        assert "Monthly fall counts per ward" in html

    def test_chart_div_ids_present(self):
        html = make_full_builder().render()
        inspector = parse_html(html)
        assert "falls_bar_chart" in inspector.ids
        assert "trend_line_chart" in inspector.ids
        assert "scatter_chart" in inspector.ids


# ---------------------------------------------------------------------------
# render() — controls
# ---------------------------------------------------------------------------

class TestRenderControls:
    def test_dropdown_control_label_present(self):
        html = make_full_builder().render()
        assert "Ward" in html

    def test_dropdown_control_options_present(self):
        html = make_full_builder().render()
        assert "Ward A" in html
        assert "Ward B" in html

    def test_range_input_label_present(self):
        html = make_full_builder().render()
        assert "Workload Range" in html

    def test_range_input_ids_present(self):
        html = make_full_builder().render()
        inspector = parse_html(html)
        assert "workload_lo" in inspector.ids
        assert "workload_hi" in inspector.ids


# ---------------------------------------------------------------------------
# render() — no broken placeholders
# ---------------------------------------------------------------------------

class TestRenderNoBrokenPlaceholders:
    def test_no_double_braces(self):
        html = make_full_builder().render()
        assert "{{" not in html
        assert "}}" not in html

    def test_no_none_literals(self):
        html = make_full_builder().render()
        # "None" appearing as a literal value (not inside JS/JSON) is a sign
        # of an unfilled template slot.
        assert ">None<" not in html

    def test_no_undefined_literals(self):
        html = make_full_builder().render()
        assert ">undefined<" not in html


# ---------------------------------------------------------------------------
# save()
# ---------------------------------------------------------------------------

class TestSave:
    def test_save_creates_file(self, tmp_path):
        path = tmp_path / "dashboard.html"
        make_full_builder().save(str(path))
        assert path.exists()

    def test_saved_file_is_non_empty(self, tmp_path):
        path = tmp_path / "dashboard.html"
        make_full_builder().save(str(path))
        assert path.stat().st_size > 0

    def test_saved_content_matches_render(self, tmp_path):
        builder = make_full_builder()
        path = tmp_path / "dashboard.html"
        builder.save(str(path))
        rendered = builder.render()
        saved = path.read_text(encoding="utf-8")
        assert saved == rendered

    def test_save_overwrites_existing_file(self, tmp_path):
        path = tmp_path / "dashboard.html"
        path.write_text("old content", encoding="utf-8")
        make_minimal_builder().save(str(path))
        assert "old content" not in path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# add_view — builder fluency
# ---------------------------------------------------------------------------

class TestBuilderApi:
    def test_add_view_returns_builder(self):
        b = make_minimal_builder()
        view = ViewConfig(key="v1", tab_label="V1", heading="View 1")
        result = b.add_view(view)
        assert result is b  # fluent API

    def test_add_button_returns_builder(self):
        b = make_minimal_builder()
        # "overview_tab" is created by make_minimal_builder
        result = b.add_button(
            section_key="ward_a",
            tab_key="overview_tab",
            button_label="Btn",
            content_html="<p>Hi</p>",
        )
        assert result is b

    def test_add_dropdown_returns_builder(self):
        b = make_minimal_builder()
        result = b.add_dropdown(
            section_key="ward_a",
            tab_key="overview_tab",
            dropdown_id="d1",
            label="Label",
            options=["X", "Y"],
        )
        assert result is b

    def test_multiple_sections_all_rendered(self):
        b = HTMLBuilder(
            title="T", main_tab_label="M", dropdown_label="D",
            plotly_version="5.18.0",
            template=TEMPLATE_PATH.read_text(encoding="utf-8"),
        )
        b.add_section("s1", "Section One")
        b.add_section("s2", "Section Two")
        b.add_section("s3", "Section Three")
        html = b.render()
        assert "Section One" in html
        assert "Section Two" in html
        assert "Section Three" in html
