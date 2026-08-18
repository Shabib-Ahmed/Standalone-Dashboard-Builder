from __future__ import annotations

from typing import List, Optional, Union

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.offline import plot as plotly_div


class ChartBuilder:
    @staticmethod
    def table(
        df: pd.DataFrame,
        title: str = "",
        drop_cols: Optional[List[str]] = None,
        header_color: str = "#4472C4",
        height: int = 700,
    ) -> str:
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
        fig.update_layout(autosize=True, title=title, margin=dict(l=10, r=10, t=40, b=10))
        return fig.to_html(include_plotlyjs=False, full_html=False, config={"responsive": True})
        
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
        plot_df = df.copy()
        plot_df[color] = plot_df[color].astype(str)
        fig = px.bar(
            plot_df,
            x=x, y=y, color=color,
            error_y=error_y,
            text=text or y,
            title=title,
        )
        fig.update_layout(autosize=True,
            xaxis_title=x_label or x,
            yaxis_title=y_label or y,
            legend_title=legend_title or color,
        )
        fig.update_traces(texttemplate=text_format, textposition="outside")
        return fig.to_html(full_html=False, include_plotlyjs=False, config={"responsive": True})

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
        fig.update_layout(autosize=True,
            xaxis_title=x_label or x,
            yaxis_title=y_label or y,
            legend_title=legend_title or color,
        )
        fig.update_traces(texttemplate=text_format, textposition="outside")
        return fig.to_html(full_html=False, include_plotlyjs=False, config={"responsive": True})

    @staticmethod
    def histogram(
        values: Union[pd.Series, pd.Index],
        title: str = "",
        x_label: str = "",
        y_label: str = "Frequency",
        bargap: float = 0.1,
    ) -> str:
        counts = values.value_counts().sort_index()
        fig = go.Figure(data=[go.Bar(x=counts.index, y=counts.values)])
        fig.update_layout(autosize=True,
            title=title,
            xaxis_title=x_label,
            yaxis_title=y_label,
            bargap=bargap,
        )
        return fig.to_html(include_plotlyjs=False, full_html=False, config={"responsive": True})

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
            fig.update_layout(autosize=True,updatemenus=[dict(
                buttons=buttons, direction="down",
                showactive=True, x=1.02, y=1.15,
            )])

        fig.update_layout(autosize=True,
            title=title,
            xaxis_title=x_label or x,
            yaxis_title=y_label or y_default,
            legend_title=legend_title or color_col,
        )
        return fig.to_html(include_plotlyjs=False, full_html=False, config={"responsive": True})

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
            fig.update_layout(autosize=True,updatemenus=[dict(
                buttons=buttons, direction="down",
                showactive=True, x=1.02, y=1.15,
            )])

        fig.update_layout(autosize=True,
            title=title,
            xaxis_title=x_label or x,
            yaxis_title=y_label or y_default,
            legend_title=legend_title or color_col,
        )
        return fig.to_html(include_plotlyjs=False, full_html=False, config={"responsive": True})

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
        fig.update_layout(autosize=True,
            title=title,
            xaxis=dict(title=x_label or x, tickangle=-45),
            yaxis=dict(title=y1_label or y1, side="left"),
            yaxis2=dict(title=y2_label or y2, side="right", overlaying="y"),
            legend=dict(x=0.01, y=1.15, orientation="h"),
        )
        return fig.to_html(include_plotlyjs=False, full_html=False, config={"responsive": True})

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
        fig = px.scatter(
            df, x=x, y=y, color=color, size=size, title=title,
        )
        fig.update_layout(autosize=True,
            xaxis_title=x_label or x,
            yaxis_title=y_label or y,
            legend_title=legend_title or (color or ""),
        )
        return fig.to_html(include_plotlyjs=False, full_html=False, config={"responsive": True})

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
        fig = px.box(df, x=x, y=y, color=color, title=title)
        fig.update_layout(autosize=True,
            xaxis_title=x_label or x,
            yaxis_title=y_label or y,
        )
        return fig.to_html(include_plotlyjs=False, full_html=False, config={"responsive": True})



