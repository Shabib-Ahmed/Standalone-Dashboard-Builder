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
from pathlib import Path


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

SECTION_LABEL = "Test Section"
SECTION_KEY = "test_section"
TAB_KEY = "test_tab"
TAB_LABEL = "Test Tab"
TAB_CONTENT = "<p>Test tab content.</p>"
DASHBOARD_TITLE = "Test Dashboard"
PLOTLY_VERSION = "5.18.0"
VIEW_KEY = "test_view"
VIEW_HEADING = "Test View Heading"
VIEW_TAB_LABEL = "Test View Tab"
VIEW_DESCRIPTION = "A description for the test view."
CHART_DIV_ID = "test_chart_div"
DROPDOWN_ID = "test_dropdown"
DROPDOWN_LABEL = "Test Dropdown"
DROPDOWN_OPTIONS = ["Option A", "Option B", "Option C"]
RANGE_LO_ID = "test_lo"
RANGE_HI_ID = "test_hi"
RANGE_LABEL = "Test Range"
RANGE_RESULT_ID = "test_range_result"
BUTTON_LABEL = "Test Button"
BUTTON_CONTENT = "<p>Test button content.</p>"
TEMPLATE_PATH = Path(__file__).parent.parent / "template.html"

def make_minimal_builder() -> HTMLBuilder:
    """Smallest valid HTMLBuilder — one section with one tab, no views."""
    template_html = TEMPLATE_PATH.read_text(encoding="utf-8")
    b = HTMLBuilder(
        title=DASHBOARD_TITLE,
        main_tab_label="Overview",
        dropdown_label="Select Section",
        plotly_version=PLOTLY_VERSION,
        template=template_html,
    )
    section = b.add_section(SECTION_KEY, SECTION_LABEL)
    section.add_tab(TAB_KEY, TAB_LABEL, TAB_CONTENT)
    return b


def make_full_builder() -> HTMLBuilder:
    """Builder with sections, views, controls, buttons, and dropdowns."""
    template_html = TEMPLATE_PATH.read_text(encoding="utf-8")
    b = HTMLBuilder(
        title=DASHBOARD_TITLE,
        main_tab_label="Overview",
        dropdown_label="Select Section",
        plotly_version=PLOTLY_VERSION,
        template=template_html,
    )

    # Sections — tabs must exist before add_button / add_dropdown
    section_a = b.add_section(SECTION_KEY, SECTION_LABEL, date_range=("2024-01", "2024-12"))
    section_a.add_tab(TAB_KEY, TAB_LABEL, TAB_CONTENT)
    section_b = b.add_section("second_section", "Second Section")
    section_b.add_tab("second_tab", "Second Tab", "<p>Second tab content.</p>")

    # Views
    bar_view = ViewConfig(
        key=VIEW_KEY,
        tab_label=VIEW_TAB_LABEL,
        heading=VIEW_HEADING,
        description=VIEW_DESCRIPTION,
        rows=[
            GraphRow(graphs=[
                GraphConfig(
                    div_id=CHART_DIV_ID,
                    options=BarOptions(
                        x_col="Month",
                        y_label="Value",
                        title="Test Chart",
                        barmode="group",
                    ),
                    height=450,
                )
            ], layout="stack")
        ],
        controls=[
            DropdownControl(
                control_id=DROPDOWN_ID,
                label=DROPDOWN_LABEL,
                options=DROPDOWN_OPTIONS,
            )
        ],
    )

    line_view = ViewConfig(
        key="second_view",
        tab_label="Second View Tab",
        heading="Second View Heading",
        rows=[
            GraphRow(graphs=[
                GraphConfig(
                    div_id="second_chart_div",
                    options=LineOptions(
                        x_col="Month",
                        y_label="Value",
                        title="Second Chart",
                    ),
                )
            ])
        ],
    )

    scatter_view = ViewConfig(
        key="third_view",
        tab_label="Third View Tab",
        heading="Third View Heading",
        rows=[
            GraphRow(graphs=[
                GraphConfig(
                    div_id="third_chart_div",
                    options=ScatterOptions(
                        x_col="X",
                        y_col="Y",
                        title="Third Chart",
                        show_regression=True,
                        show_loess=True,
                        show_stats_badge=True,
                    ),
                )
            ])
        ],
        controls=[
            RangeInputControl(
                lo_id=RANGE_LO_ID,
                hi_id=RANGE_HI_ID,
                label=RANGE_LABEL,
                result_div_id=RANGE_RESULT_ID,
            )
        ],
    )

    b.add_view(bar_view)
    b.add_view(line_view)
    b.add_view(scatter_view)

    # Inline button and dropdown
    b.add_button(
        section_key=SECTION_KEY,
        tab_key=TAB_KEY,
        button_label=BUTTON_LABEL,
        content_html=BUTTON_CONTENT,
    )

    b.add_dropdown(
        section_key="second_section",
        tab_key="second_tab",
        dropdown_id=DROPDOWN_ID,
        label=DROPDOWN_LABEL,
        options=DROPDOWN_OPTIONS,
    )

    return b


# ---------------------------------------------------------------------------
# render() — basic structure
# ---------------------------------------------------------------------------

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
        assert DASHBOARD_TITLE in html

    def test_render_plotly_version_referenced(self):
        html = make_minimal_builder().render()
        assert PLOTLY_VERSION in html


# ---------------------------------------------------------------------------
# render() — sections and tabs
# ---------------------------------------------------------------------------

class TestRenderSections:
    def test_section_label_present(self):
        html = make_full_builder().render()
        assert SECTION_LABEL in html

    def test_date_range_present(self):
        html = make_full_builder().render()
        assert "2024-01" in html or "2024" in html

    def test_button_label_present(self):
        html = make_full_builder().render()
        assert BUTTON_LABEL in html

    def test_button_content_present(self):
        html = make_full_builder().render()
        assert "Test button content" in html

    def test_dropdown_options_present(self):
        html = make_full_builder().render()
        assert DROPDOWN_OPTIONS[0] in html


# ---------------------------------------------------------------------------
# render() — views
# ---------------------------------------------------------------------------

class TestRenderViews:
    def test_view_headings_present(self):
        html = make_full_builder().render()
        assert VIEW_HEADING in html

    def test_view_tab_labels_present(self):
        html = make_full_builder().render()
        assert VIEW_TAB_LABEL in html

    def test_view_description_present(self):
        html = make_full_builder().render()
        assert VIEW_DESCRIPTION in html

    def test_chart_div_ids_present(self):
        html = make_full_builder().render()
        inspector = parse_html(html)
        assert CHART_DIV_ID in inspector.ids


# ---------------------------------------------------------------------------
# render() — controls
# ---------------------------------------------------------------------------

class TestRenderControls:
    def test_dropdown_control_label_present(self):
        html = make_full_builder().render()
        assert DROPDOWN_LABEL in html

    def test_dropdown_control_options_present(self):
        html = make_full_builder().render()
        for option in DROPDOWN_OPTIONS:
            assert option in html

    def test_range_input_label_present(self):
        html = make_full_builder().render()
        assert RANGE_LABEL in html

    def test_range_input_ids_present(self):
        html = make_full_builder().render()
        inspector = parse_html(html)
        assert RANGE_LO_ID in inspector.ids
        assert RANGE_HI_ID in inspector.ids


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
        result = b.add_button(
            section_key=SECTION_KEY,
            tab_key=TAB_KEY,
            button_label="Btn",
            content_html="<p>Hi</p>",
        )
        assert result is b

    def test_add_dropdown_returns_builder(self):
        b = make_minimal_builder()
        result = b.add_dropdown(
            section_key=SECTION_KEY,
            tab_key=TAB_KEY,
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
