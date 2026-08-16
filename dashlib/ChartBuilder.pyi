from __future__ import annotations

from typing import List, Optional, Union

import pandas as pd


class ChartBuilder:
    """Static factory methods for common Plotly chart types.

    Every method returns a self-contained HTML fragment (no ``<html>``/``<body>``)
    that can be embedded directly into a dashboard template built with
    ``HTMLBuilder``.
    """

    @staticmethod
    def table(
        df: pd.DataFrame,
        title: str = "",
        drop_cols: Optional[List[str]] = ...,
        header_color: str = ...,
        height: int = ...,
    ) -> str:
        """Interactive Plotly table rendered from a DataFrame.

        Parameters
        ----------
        df:
            Source DataFrame.
        title:
            Chart title shown above the table.
        drop_cols:
            Column names to exclude from the rendered table.
        header_color:
            Hex colour string for the header row background (default ``"#4472C4"``).
        height:
            Pixel height of the table figure (default ``700``).

        Returns
        -------
        str
            Self-contained HTML ``<div>`` fragment (no ``<html>``/``<body>``).
        """
        ...

    @staticmethod
    def bar(
        df: pd.DataFrame,
        x: str,
        y: str,
        color: str,
        error_y: Optional[str] = ...,
        text: Optional[str] = ...,
        title: str = "",
        x_label: str = "",
        y_label: str = "",
        legend_title: str = "",
        text_format: str = ...,
    ) -> str:
        """Stacked bar chart with optional error bars and value labels.

        Parameters
        ----------
        df:
            Source DataFrame.
        x:
            Column name for the x-axis.
        y:
            Column name for the y-axis (bar height).
        color:
            Column used to colour-encode and stack bars.
        error_y:
            Optional column whose values are used as symmetric error-bar
            magnitudes on each bar.
        text:
            Column whose values are rendered as bar labels.  Defaults to *y*.
        title:
            Figure title.
        x_label:
            X-axis label; defaults to *x* when omitted.
        y_label:
            Y-axis label; defaults to *y* when omitted.
        legend_title:
            Legend title; defaults to *color* when omitted.
        text_format:
            Plotly ``texttemplate`` string applied to bar labels
            (default ``"%{y:.1f}"``).

        Returns
        -------
        str
            Self-contained HTML ``<div>`` fragment.
        """
        ...

    @staticmethod
    def grouped_bar(
        df: pd.DataFrame,
        x: str,
        y: str,
        color: str,
        error_y: Optional[str] = ...,
        text: Optional[str] = ...,
        title: str = "",
        x_label: str = "",
        y_label: str = "",
        legend_title: str = "",
        text_format: str = ...,
    ) -> str:
        """Grouped (side-by-side) bar chart with optional error bars and value labels.

        Identical signature to :meth:`bar` but renders bars in ``"group"``
        mode rather than stacked.

        Parameters
        ----------
        df:
            Source DataFrame.
        x:
            Column name for the x-axis.
        y:
            Column name for the y-axis (bar height).
        color:
            Column used to split bars into side-by-side groups.
        error_y:
            Optional column whose values are used as symmetric error-bar
            magnitudes on each bar.
        text:
            Column whose values are rendered as bar labels.  Defaults to *y*.
        title:
            Figure title.
        x_label:
            X-axis label; defaults to *x* when omitted.
        y_label:
            Y-axis label; defaults to *y* when omitted.
        legend_title:
            Legend title; defaults to *color* when omitted.
        text_format:
            Plotly ``texttemplate`` string applied to bar labels
            (default ``"%{y:.1f}"``).

        Returns
        -------
        str
            Self-contained HTML ``<div>`` fragment.
        """
        ...

    @staticmethod
    def histogram(
        values: Union[pd.Series, pd.Index],
        title: str = "",
        x_label: str = "",
        y_label: str = ...,
        bargap: float = ...,
    ) -> str:
        """Bar chart built from the value-counts of a categorical Series.

        This is not a continuous-data histogram; it counts the occurrences of
        each unique value and renders one bar per category, sorted by index.

        Parameters
        ----------
        values:
            Series whose unique values are counted and plotted.
        title:
            Figure title.
        x_label:
            X-axis label.
        y_label:
            Y-axis label (default ``"Frequency"``).
        bargap:
            Fractional gap between bars in the range ``[0, 1]``
            (default ``0.1``).

        Returns
        -------
        str
            Self-contained HTML ``<div>`` fragment.
        """
        ...

    @staticmethod
    def single_line(
        df: pd.DataFrame,
        x: str,
        y_default: str,
        color_col: str,
        y_options: Optional[List[str]] = ...,
        title: str = "",
        x_label: str = "",
        y_label: str = "",
        legend_title: str = "",
        height: int = ...,
    ) -> str:
        """Single-series line chart with an optional metric-switcher dropdown.

        Rows are sorted by *x* before plotting.  When *y_options* contains
        more than one entry, a Plotly dropdown is injected so viewers can
        switch the y-axis metric without reloading the page.

        Parameters
        ----------
        df:
            Source DataFrame containing *x*, *color_col*, and all metrics
            listed in *y_options*.
        x:
            Column for the x-axis (sorted ascending before plotting).
        y_default:
            Metric column shown on first render.  Should appear in
            *y_options* when that list is provided.
        color_col:
            Column whose unique values become separate line traces.
        y_options:
            If provided and contains more than one entry, a Plotly dropdown
            button group is added to switch the y-axis among these metrics.
        title:
            Figure title.
        x_label:
            X-axis label; defaults to *x* when omitted.
        y_label:
            Y-axis label; defaults to *y_default* when omitted.
        legend_title:
            Legend title; defaults to *color_col* when omitted.
        height:
            Pixel height of the figure (default ``500``).

        Returns
        -------
        str
            Self-contained HTML ``<div>`` fragment.
        """
        ...

    @staticmethod
    def multi_line(
        df: pd.DataFrame,
        x: str,
        y_default: str,
        color_col: str,
        y_options: Optional[List[str]] = ...,
        title: str = "",
        x_label: str = "",
        y_label: str = "",
        legend_title: str = "",
        height: int = ...,
    ) -> str:
        """Multi-series line chart with an optional metric-switcher dropdown.

        Functionally identical to :meth:`single_line`; use this variant when
        the intent is explicitly to overlay multiple groups on the same axes
        for direct comparison.

        Parameters
        ----------
        df:
            Source DataFrame containing *x*, *color_col*, and all metrics
            listed in *y_options*.
        x:
            Column for the x-axis (sorted ascending before plotting).
        y_default:
            Metric column shown on first render.  Should appear in
            *y_options* when that list is provided.
        color_col:
            Column whose unique values become separate line traces.
        y_options:
            If provided and contains more than one entry, a Plotly dropdown
            button group is added to switch the y-axis among these metrics.
        title:
            Figure title.
        x_label:
            X-axis label; defaults to *x* when omitted.
        y_label:
            Y-axis label; defaults to *y_default* when omitted.
        legend_title:
            Legend title; defaults to *color_col* when omitted.
        height:
            Pixel height of the figure (default ``500``).

        Returns
        -------
        str
            Self-contained HTML ``<div>`` fragment.
        """
        ...

    @staticmethod
    def dual_axis_line(
        df: pd.DataFrame,
        x: str,
        y1: str,
        y2: str,
        y1_label: str = "",
        y2_label: str = "",
        title: str = "",
        x_label: str = "",
        height: int = ...,
    ) -> str:
        """Two-series line chart with independent left and right y-axes.

        Useful for overlaying metrics that share an x-axis but have
        incompatible scales (e.g. fall rate vs. nurse-to-patient ratio).

        Parameters
        ----------
        df:
            Source DataFrame, pre-sorted by *x* if order matters.
        x:
            Column for the shared x-axis.
        y1:
            Column plotted against the **left** y-axis.
        y2:
            Column plotted against the **right** y-axis.
        y1_label:
            Left-axis title; defaults to *y1* when omitted.
        y2_label:
            Right-axis title; defaults to *y2* when omitted.
        title:
            Figure title.
        x_label:
            X-axis label; defaults to *x* when omitted.
        height:
            Pixel height of the figure (default ``520``).

        Returns
        -------
        str
            Self-contained HTML ``<div>`` fragment.
        """
        ...

    @staticmethod
    def scatter(
        df: pd.DataFrame,
        x: str,
        y: str,
        color: Optional[str] = ...,
        size: Optional[str] = ...,
        title: str = "",
        x_label: str = "",
        y_label: str = "",
        legend_title: str = "",
        height: int = ...,
    ) -> str:
        """Scatter or bubble chart.

        Providing *size* turns the chart into a bubble chart where point area
        encodes a third numeric dimension.

        Parameters
        ----------
        df:
            Source DataFrame.
        x:
            Column for the x-axis.
        y:
            Column for the y-axis.
        color:
            Optional column used to colour-encode points.
        size:
            Optional column used to size-encode points (bubble chart).
        title:
            Figure title.
        x_label:
            X-axis label; defaults to *x* when omitted.
        y_label:
            Y-axis label; defaults to *y* when omitted.
        legend_title:
            Legend title; defaults to *color* when omitted.
        height:
            Pixel height of the figure (default ``500``).

        Returns
        -------
        str
            Self-contained HTML ``<div>`` fragment.
        """
        ...

    @staticmethod
    def box(
        df: pd.DataFrame,
        x: str,
        y: str,
        color: Optional[str] = ...,
        title: str = "",
        x_label: str = "",
        y_label: str = "",
        height: int = ...,
    ) -> str:
        """Box-plot for distribution comparisons across categorical groups.

        Particularly suited to comparing patient-outcome distributions
        (e.g. length-of-stay, vital signs) across wards or time periods.

        Parameters
        ----------
        df:
            Source DataFrame.
        x:
            Categorical column defining the groups along the x-axis
            (e.g. ward names, time buckets).
        y:
            Continuous column whose distribution is visualised per group.
        color:
            Optional secondary grouping column for colour-encoded sub-groups.
        title:
            Figure title.
        x_label:
            X-axis label; defaults to *x* when omitted.
        y_label:
            Y-axis label; defaults to *y* when omitted.
        height:
            Pixel height of the figure (default ``500``).

        Returns
        -------
        str
            Self-contained HTML ``<div>`` fragment.
        """
        ...
