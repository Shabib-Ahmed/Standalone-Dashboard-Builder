from __future__ import annotations

from typing import Any, List, Optional, Tuple


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
    ) -> None: ...
    @property
    def heading(self) -> str: ...
    def add_tab(self, key: str, label: str, content_html: str) -> Section: ...


class ComparisonConfig:
    data_json: str
    t_crit_json: str
    groups: List[str]
    filter_keys: List[Any]
    default_filter: Any
    tab_label: str
    heading: str
    filter_label: str
    value_label: str
    group_label: str
    bucket_label: str
    def __init__(
        self,
        data_json: str,
        t_crit_json: str,
        groups: List[str],
        filter_keys: List[Any],
        default_filter: Any,
        tab_label: str,
        heading: str,
        filter_label: str,
        value_label: str,
        group_label: str,
        bucket_label: str,
    ) -> None: ...


class SeriesConfig:
    col: str
    label: str
    axis: str
    overlay_col: Optional[str]
    overlay_label: str
    def __init__(
        self,
        col: str,
        label: str,
        axis: str = ...,
        overlay_col: Optional[str] = ...,
        overlay_label: str = ...,
    ) -> None: ...


class SecondaryViewConfig:
    data_json: str
    categories: List[str]
    series: List[SeriesConfig]
    tab_label: str
    heading: str
    category_label: str
    time_col: str
    time_label: str
    def __init__(
        self,
        data_json: str,
        categories: List[str],
        series: List[SeriesConfig],
        tab_label: str,
        heading: str,
        category_label: str,
        time_col: str,
        time_label: str,
    ) -> None: ...

class CorrelationConfig:
    scatter_json: str
    departments: List[str]
    group_names: List[str]
    hour: int
    col1_key: str
    col2_key: str
    col1_label: str
    col2_label: str
    tab_label: str
    heading: str
    def __init__(
        self,
        scatter_json: str,
        departments: List[str],
        group_names: List[str],
        hour: int,
        col1_key: str,
        col2_key: str,
        col1_label: str,
        col2_label: str,
        tab_label: str,
        heading: str,
    ) -> None: ...

# =====================================================================
# HTMLBuilder
# =====================================================================

class HTMLBuilder:
    title: str
    main_tab_label: str
    dropdown_label: str
    plotly_version: str
    template: str
    sections: List[Section]
    comparison: Optional[ComparisonConfig]
    secondary: Optional[SecondaryViewConfig]

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

    def set_comparison(
        self,
        data: dict,
        groups: List[str],
        filter_keys: List[Any],
        default_filter: Any,
        tab_label: str,
        heading: str,
        filter_label: str,
        value_label: str,
        group_label: str,
        bucket_label: str,
        t_crit: Optional[dict[int, float]] = ...,
    ) -> None: ...

    def set_secondary_view(
        self,
        data: dict,
        categories: List[str],
        series: List[SeriesConfig],
        tab_label: str,
        heading: str,
        category_label: str,
        time_col: str,
        time_label: str,
    ) -> None: ...

    def set_correlation(
            self,
            data: dict,
            hour: int,
            col1_label: str,
            col2_label: str,
            *,
            tab_label: str = ...,
            heading: str = ...,
        ) -> None: ...

    # Rendering
    def render(self) -> str: ...
    def save(self, path: str) -> None: ...
