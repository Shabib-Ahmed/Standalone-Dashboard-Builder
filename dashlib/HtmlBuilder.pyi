from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field


# =====================================================================
# Data-model dataclasses
# =====================================================================

class Tab:
    key: str
    label: str
    content_html: str
    def __init__(self, key: str, label: str, content_html: str) -> None: ...


class Section:
    key: str
    label: str
    date_range: Optional[Tuple[str, str]]
    tabs: List[Tab]
    def __init__(
        self,
        key: str,
        label: str,
        date_range: Optional[Tuple[str, str]] = ...,
        tabs: List[Tab] = ...,
    ) -> None: ...
    @property
    def heading(self) -> str: ...
    def add_tab(self, key: str, label: str, content_html: str) -> Section: ...


class GraphRow:
    graphs: List[GraphConfig]
    layout: str   # "stack" | "halves" | "thirds" | "sidebar-left" | "sidebar-right"
    gap: int      # px gap between columns
    def __init__(
        self,
        graphs: List[GraphConfig],
        layout: str = ...,
        gap: int = ...,
    ) -> None: ...


# =====================================================================
# Control configs
# =====================================================================

class DropdownControl:
    """A <select> rendered above charts in a view."""
    control_id: str
    label: str
    options: List[str]
    on_change: str
    def __init__(
        self,
        control_id: str,
        label: str,
        options: List[str],
        on_change: str = ...,
    ) -> None: ...


class RangeInputControl:
    """Two numeric <input> fields (lo / hi) for workload-range filtering."""
    lo_id: str
    hi_id: str
    label: str
    result_div_id: str
    def __init__(
        self,
        lo_id: str,
        hi_id: str,
        label: str = ...,
        result_div_id: str = ...,
    ) -> None: ...


ControlConfig = Union[DropdownControl, RangeInputControl]


# =====================================================================
# Graph option types
# =====================================================================

class GraphOptions:
    """Abstract base — never instantiated directly."""


class LineOptions(GraphOptions):
    """One or more series plotted as lines against a shared x-axis."""
    series: List[Dict[str, str]]
    x_col: str
    x_label: str
    y_label: str
    title: str
    connect_gaps: bool
    def __init__(
        self,
        series: List[Dict[str, str]] = ...,
        x_col: str = ...,
        x_label: str = ...,
        y_label: str = ...,
        title: str = ...,
        connect_gaps: bool = ...,
    ) -> None: ...


class BarOptions(GraphOptions):
    series: List[Dict[str, str]]
    x_col: str
    x_label: str
    y_label: str
    title: str
    barmode: str  # "group" | "stack" | "overlay"
    def __init__(
        self,
        series: List[Dict[str, str]] = ...,
        x_col: str = ...,
        x_label: str = ...,
        y_label: str = ...,
        title: str = ...,
        barmode: str = ...,
    ) -> None: ...


class DualAxisOptions(GraphOptions):
    """Left-axis series vs right-axis series, with optional overlay chart."""
    x_col: str
    x_label: str
    left_col: str
    left_label: str
    right_col: str
    right_label: str
    title: str
    show_overlay_chart: bool
    def __init__(
        self,
        x_col: str = ...,
        x_label: str = ...,
        left_col: str = ...,
        left_label: str = ...,
        right_col: str = ...,
        right_label: str = ...,
        title: str = ...,
        show_overlay_chart: bool = ...,
    ) -> None: ...


class RangeFilterOptions:
    """Workload-range filter panel rendered beneath a ScatterOptions chart."""
    result_div_id: str
    lo_input_id: str
    hi_input_id: str
    def __init__(
        self,
        result_div_id: str = ...,
        lo_input_id: str = ...,
        hi_input_id: str = ...,
    ) -> None: ...


class ScatterOptions(GraphOptions):
    x_col: str
    x_label: str
    y_col: str
    y_label: str
    id_col: str
    time_col: str
    title: str
    show_regression: bool
    show_loess: bool
    show_stats_badge: bool
    weight_col: str
    range_filter: Optional[RangeFilterOptions]
    def __init__(
        self,
        x_col: str = ...,
        x_label: str = ...,
        y_col: str = ...,
        y_label: str = ...,
        id_col: str = ...,
        time_col: str = ...,
        title: str = ...,
        show_regression: bool = ...,
        show_loess: bool = ...,
        show_stats_badge: bool = ...,
        weight_col: str = ...,
        range_filter: Optional[RangeFilterOptions] = ...,
    ) -> None: ...


class TableOptions(GraphOptions):
    """Renders a plain HTML table from the view data."""
    columns: List[Dict[str, str]]
    time_col: str
    time_label: str
    def __init__(
        self,
        columns: List[Dict[str, str]] = ...,
        time_col: str = ...,
        time_label: str = ...,
    ) -> None: ...


class ComparisonOptions(GraphOptions):
    """Side-by-side comparison of two groups across time buckets."""
    groups: List[str]
    group_label: str
    filter_keys: List[str]
    filter_label: str
    default_filter: str
    bucket_label: str
    value_label: str
    data_json: str
    t_crit_json: str
    def __init__(
        self,
        groups: List[str] = ...,
        group_label: str = ...,
        filter_keys: List[str] = ...,
        filter_label: str = ...,
        default_filter: str = ...,
        bucket_label: str = ...,
        value_label: str = ...,
        data_json: str = ...,
        t_crit_json: str = ...,
    ) -> None: ...


# =====================================================================
# Graph / view container types
# =====================================================================

class GraphConfig:
    div_id: str
    options: GraphOptions
    height: int  # pixels; ignored for TableOptions
    def __init__(
        self,
        div_id: str,
        options: GraphOptions,
        height: int = ...,
    ) -> None: ...


class ViewConfig:
    key: str
    tab_label: str
    heading: str
    description: str
    data_json: str
    controls: List[ControlConfig]
    rows: List[GraphRow]
    def __init__(
        self,
        key: str,
        tab_label: str,
        heading: str,
        description: str = ...,
        data_json: str = ...,
        controls: List[ControlConfig] = ...,
        rows: List[GraphRow] = ...,
    ) -> None: ...


# =====================================================================
# HTMLBuilder
# =====================================================================

class HTMLBuilder:
    """Assembles a multi-section, multi-view HTML dashboard."""

    title: str
    main_tab_label: str
    dropdown_label: str
    plotly_version: str
    template: str
    sections: List[Section]
    views: List[ViewConfig]

    def __init__(
        self,
        title: str,
        main_tab_label: str,
        dropdown_label: str,
        plotly_version: str,
        template: str,
    ) -> None: ...

    # Building API
    def add_section(
        self,
        key: str,
        label: str,
        date_range: Optional[Tuple[str, str]] = ...,
    ) -> Section: ...

    def add_button(
        self,
        section_key: str,
        tab_key: str,
        button_label: str,
        content_html: str,
    ) -> HTMLBuilder: ...

    def add_dropdown(
        self,
        section_key: str,
        tab_key: str,
        dropdown_id: str,
        label: str,
        options: List[str],
        on_change_js: str = ...,
    ) -> HTMLBuilder: ...

    def add_view(self, view: ViewConfig) -> HTMLBuilder: ...

    # Rendering
    def render(self) -> str: ...
    def save(self, path: str) -> None: ...
