from __future__ import annotations

from typing import List, Optional, Union

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.offline import plot as plotly_div


class ChartBuilder:
    """Static factory methods for common Plotly chart types.

    Every method returns a self-contained HTML fragment (no <html>/<body>)
    that can be embedded directly into a dashboard template built with
    ``HTMLBuilder``.
    """

    @staticmethod
    def table(
        df: pd.DataFrame,
        title: str = "",
        drop_cols: Optional[List[str]] = None,
        header_color: str = "#4472C4",
        height: int = 700,
    ) -> str:
        """Interactive Plotly table rendered from a DataFrame.

        Parameters
        ----------
        df : Source DataFrame.
        title : Chart title shown above the table.
        drop_cols : Column names to exclude from the rendered table.
        header_color : Hex colour string for the header row background.
        height : Pixel height of the table figure.

        Returns
        -------
        str
            Self-contained HTML ``<div>`` fragment (no ``<html>``/``<body>``).
        """
        display_df = df.drop(columns=drop_cols or [], errors="ignore")
        fig = go.Figure(
            data=[
                go.Table(
                    header=dict(
                        values=list(display_df.columns),
                        fill_color=header_color,
                        font=dict(color="white", size=12),
                        align="left",
                    ),
                    cells=dict(
                        values=[display_df[c] for c in display_df.columns],
                        align="left",
                    ),
                )
            ]
        )
        fig.update_layout(title=title, margin=dict(l=10, r=10, t=40, b=10), height=height)
        return plotly_div(fig, include_plotlyjs=False, output_type="div")

    @staticmethod
    def bar(
        df: pd.DataFrame,
        x: str,
        y: str,
        color: str,
        error_y: Optional[str] = None,
        text: Optional[str] = None,
        title: str = "",
        x_label: str = "",
        y_label: str = "",
        legend_title: str = "",
        text_format: str = "%{y:.1f}",
    ) -> str:
        """Stacked bar chart with optional error bars and value labels.

        Parameters
        ----------
        df : Source DataFrame.
        x : Column name for the x-axis.
        y : Column name for the y-axis (bar height).
        color : Column used to colour-encode and stack bars.
        error_y : Optional column with symmetric error-bar magnitudes.
        text : Column whose values are rendered as bar labels; defaults to *y*.
        title : Figure title.
        x_label : X-axis label; defaults to *x* when omitted.
        y_label : Y-axis label; defaults to *y* when omitted.
        legend_title : Legend title; defaults to *color* when omitted.
        text_format : Plotly ``texttemplate`` string applied to bar labels.

        Returns
        -------
        str
            Self-contained HTML ``<div>`` fragment.
        """
        plot_df = df.copy()
        plot_df[color] = plot_df[color].astype(str)
        fig = px.bar(
            plot_df,
            x=x, y=y, color=color,
            error_y=error_y,
            text=text or y,
            title=title,
        )
        fig.update_layout(
            xaxis_title=x_label or x,
            yaxis_title=y_label or y,
            legend_title=legend_title or color,
        )
        fig.update_traces(texttemplate=text_format, textposition="outside")
        return fig.to_html(full_html=False, include_plotlyjs=False)

    @staticmethod
    def grouped_bar(
        df: pd.DataFrame,
        x: str,
        y: str,
        color: str,
        error_y: Optional[str] = None,
        text: Optional[str] = None,
        title: str = "",
        x_label: str = "",
        y_label: str = "",
        legend_title: str = "",
        text_format: str = "%{y:.1f}",
    ) -> str:
        """Grouped (side-by-side) bar chart with optional error bars and value labels.

        Parameters
        ----------
        df : Source DataFrame.
        x : Column name for the x-axis.
        y : Column name for the y-axis (bar height).
        color : Column used to split bars into side-by-side groups.
        error_y : Optional column with symmetric error-bar magnitudes.
        text : Column whose values are rendered as bar labels; defaults to *y*.
        title : Figure title.
        x_label : X-axis label; defaults to *x* when omitted.
        y_label : Y-axis label; defaults to *y* when omitted.
        legend_title : Legend title; defaults to *color* when omitted.
        text_format : Plotly ``texttemplate`` string applied to bar labels.

        Returns
        -------
        str
            Self-contained HTML ``<div>`` fragment.
        """
        plot_df = df.copy()
        plot_df[color] = plot_df[color].astype(str)
        fig = px.bar(
            plot_df,
            x=x, y=y, color=color,
            barmode="group",
            error_y=error_y,
            text=text or y,
            title=title,
        )
        fig.update_layout(
            xaxis_title=x_label or x,
            yaxis_title=y_label or y,
            legend_title=legend_title or color,
        )
        fig.update_traces(texttemplate=text_format, textposition="outside")
        return fig.to_html(full_html=False, include_plotlyjs=False)

    @staticmethod
    def histogram(
        values: Union[pd.Series, pd.Index],
        title: str = "",
        x_label: str = "",
        y_label: str = "Frequency",
        bargap: float = 0.1,
    ) -> str:
        """Bar chart built from the value-counts of a categorical Series.

        This counts occurrences of each unique value and renders one bar per
        category, sorted by index.  It is *not* a continuous-data histogram.

        Parameters
        ----------
        values : Series (or Index) whose unique values are counted and plotted.
        title : Figure title.
        x_label : X-axis label.
        y_label : Y-axis label (default ``"Frequency"``).
        bargap : Fractional gap between bars in the range ``[0, 1]``.

        Returns
        -------
        str
            Self-contained HTML ``<div>`` fragment.
        """
        counts = values.value_counts().sort_index()
        fig = go.Figure(data=[go.Bar(x=counts.index, y=counts.values)])
        fig.update_layout(
            title=title,
            xaxis_title=x_label,
            yaxis_title=y_label,
            bargap=bargap,
        )
        return fig.to_html(include_plotlyjs=False, full_html=False)

    @staticmethod
    def single_line(
        df: pd.DataFrame,
        x: str,
        y_default: str,
        color_col: str,
        y_options: Optional[List[str]] = None,
        title: str = "",
        x_label: str = "",
        y_label: str = "",
        legend_title: str = "",
        height: int = 500,
    ) -> str:
        """Single-series line chart with an optional metric-switcher dropdown.

        Rows are sorted by *x* before plotting.  When *y_options* contains
        more than one entry, a Plotly dropdown is injected so viewers can
        switch the y-axis metric without reloading the page.

        Parameters
        ----------
        df : Source DataFrame.
        x : Column for the x-axis (sorted ascending before plotting).
        y_default : Metric column shown on first render.
        color_col : Column whose unique values become separate line traces.
        y_options : If provided and contains more than one entry, a Plotly
                    dropdown button group is added to switch the y-axis.
        title : Figure title.
        x_label : X-axis label; defaults to *x* when omitted.
        y_label : Y-axis label; defaults to *y_default* when omitted.
        legend_title : Legend title; defaults to *color_col* when omitted.
        height : Pixel height of the figure.

        Returns
        -------
        str
            Self-contained HTML ``<div>`` fragment.
        """
        plot_df = df.copy().sort_values(x)
        groups = sorted(plot_df[color_col].unique())

        fig = go.Figure()
        for grp in groups:
            grp_df = plot_df[plot_df[color_col] == grp]
            fig.add_trace(
                go.Scatter(
                    x=grp_df[x], y=grp_df[y_default],
                    mode="lines+markers", name=str(grp),
                )
            )

        if y_options and len(y_options) > 1:
            buttons = []
            for metric in y_options:
                y_vals = [plot_df[plot_df[color_col] == g][metric] for g in groups]
                buttons.append(dict(
                    label=metric,
                    method="update",
                    args=[
                        {"y": y_vals},
                        {"title": title.replace(y_default, metric),
                         "yaxis": {"title": metric}},
                    ],
                ))
            fig.update_layout(updatemenus=[dict(
                buttons=buttons, direction="down",
                showactive=True, x=1.02, y=1.15,
            )])

        fig.update_layout(
            title=title, height=height,
            xaxis_title=x_label or x,
            yaxis_title=y_label or y_default,
            legend_title=legend_title or color_col,
        )
        return fig.to_html(include_plotlyjs=False, full_html=False)

    @staticmethod
    def multi_line(
        df: pd.DataFrame,
        x: str,
        y_default: str,
        color_col: str,
        y_options: Optional[List[str]] = None,
        title: str = "",
        x_label: str = "",
        y_label: str = "",
        legend_title: str = "",
        height: int = 500,
    ) -> str:
        """Multi-series line chart with an optional metric-switcher dropdown.

        Functionally identical to :meth:`single_line`; use this variant when
        the intent is explicitly to overlay multiple groups for direct
        comparison.

        Parameters
        ----------
        df : Source DataFrame.
        x : Column for the x-axis (sorted ascending before plotting).
        y_default : Metric column shown on first render.
        color_col : Column whose unique values become separate line traces.
        y_options : If provided and contains more than one entry, a Plotly
                    dropdown button group is added to switch the y-axis.
        title : Figure title.
        x_label : X-axis label; defaults to *x* when omitted.
        y_label : Y-axis label; defaults to *y_default* when omitted.
        legend_title : Legend title; defaults to *color_col* when omitted.
        height : Pixel height of the figure.

        Returns
        -------
        str
            Self-contained HTML ``<div>`` fragment.
        """
        plot_df = df.copy().sort_values(x)
        groups = sorted(plot_df[color_col].unique())

        fig = go.Figure()
        for grp in groups:
            grp_df = plot_df[plot_df[color_col] == grp]
            fig.add_trace(
                go.Scatter(
                    x=grp_df[x], y=grp_df[y_default],
                    mode="lines+markers", name=str(grp),
                )
            )

        if y_options and len(y_options) > 1:
            buttons = []
            for metric in y_options:
                y_vals = [plot_df[plot_df[color_col] == g][metric] for g in groups]
                buttons.append(dict(
                    label=metric,
                    method="update",
                    args=[
                        {"y": y_vals},
                        {"title": title.replace(y_default, metric),
                         "yaxis": {"title": metric}},
                    ],
                ))
            fig.update_layout(updatemenus=[dict(
                buttons=buttons, direction="down",
                showactive=True, x=1.02, y=1.15,
            )])

        fig.update_layout(
            title=title, height=height,
            xaxis_title=x_label or x,
            yaxis_title=y_label or y_default,
            legend_title=legend_title or color_col,
        )
        return fig.to_html(include_plotlyjs=False, full_html=False)

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
        height: int = 520,
    ) -> str:
        """Two-series line chart with independent left and right y-axes.

        Useful for overlaying metrics that share an x-axis but have
        incompatible scales (e.g. fall rate vs. nurse-to-patient ratio).

        Parameters
        ----------
        df : Source DataFrame, pre-sorted by *x* if order matters.
        x : Column for the shared x-axis.
        y1 : Column plotted against the left y-axis.
        y2 : Column plotted against the right y-axis.
        y1_label : Left-axis title; defaults to *y1* when omitted.
        y2_label : Right-axis title; defaults to *y2* when omitted.
        title : Figure title.
        x_label : X-axis label; defaults to *x* when omitted.
        height : Pixel height of the figure.

        Returns
        -------
        str
            Self-contained HTML ``<div>`` fragment.
        """
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df[x], y=df[y1],
            mode="lines+markers", name=y1_label or y1,
            yaxis="y",
        ))
        fig.add_trace(go.Scatter(
            x=df[x], y=df[y2],
            mode="lines+markers", name=y2_label or y2,
            yaxis="y2",
        ))
        fig.update_layout(
            title=title,
            xaxis=dict(title=x_label or x, tickangle=-45),
            yaxis=dict(title=y1_label or y1, side="left"),
            yaxis2=dict(title=y2_label or y2, side="right", overlaying="y"),
            height=height,
            legend=dict(x=0.01, y=1.15, orientation="h"),
        )
        return fig.to_html(include_plotlyjs=False, full_html=False)

    @staticmethod
    def scatter(
        df: pd.DataFrame,
        x: str,
        y: str,
        color: Optional[str] = None,
        size: Optional[str] = None,
        title: str = "",
        x_label: str = "",
        y_label: str = "",
        legend_title: str = "",
        height: int = 500,
    ) -> str:
        """Scatter or bubble chart.

        Providing *size* turns the chart into a bubble chart where point area
        encodes a third numeric dimension.

        Parameters
        ----------
        df : Source DataFrame.
        x : Column for the x-axis.
        y : Column for the y-axis.
        color : Optional column used to colour-encode points.
        size : Optional column used to size-encode points (bubble chart).
        title : Figure title.
        x_label : X-axis label; defaults to *x* when omitted.
        y_label : Y-axis label; defaults to *y* when omitted.
        legend_title : Legend title; defaults to *color* when omitted.
        height : Pixel height of the figure.

        Returns
        -------
        str
            Self-contained HTML ``<div>`` fragment.
        """
        fig = px.scatter(
            df, x=x, y=y, color=color, size=size, title=title,
        )
        fig.update_layout(
            xaxis_title=x_label or x,
            yaxis_title=y_label or y,
            legend_title=legend_title or (color or ""),
            height=height,
        )
        return fig.to_html(include_plotlyjs=False, full_html=False)

    @staticmethod
    def box(
        df: pd.DataFrame,
        x: str,
        y: str,
        color: Optional[str] = None,
        title: str = "",
        x_label: str = "",
        y_label: str = "",
        height: int = 500,
    ) -> str:
        """Box-plot for distribution comparisons across categorical groups.

        Parameters
        ----------
        df : Source DataFrame.
        x : Categorical column defining the groups along the x-axis.
        y : Continuous column whose distribution is visualised per group.
        color : Optional secondary grouping column for colour-encoded sub-groups.
        title : Figure title.
        x_label : X-axis label; defaults to *x* when omitted.
        y_label : Y-axis label; defaults to *y* when omitted.
        height : Pixel height of the figure.

        Returns
        -------
        str
            Self-contained HTML ``<div>`` fragment.
        """
        fig = px.box(df, x=x, y=y, color=color, title=title)
        fig.update_layout(
            xaxis_title=x_label or x,
            yaxis_title=y_label or y,
            height=height,
        )
        return fig.to_html(include_plotlyjs=False, full_html=False)
