from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from typing import TypedDict

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Aggregation function type
# ---------------------------------------------------------------------------

AggFn = Union[str, Callable[[Any], Any]]
"""A pandas aggregation: either a method-name string (e.g. ``"mean"``) or a
callable that accepts a ``SeriesGroupBy`` / ``Series`` and returns a scalar."""


# ---------------------------------------------------------------------------
# Module-level constant
# ---------------------------------------------------------------------------

STANDARD_AGGS: Dict[str, AggFn]
"""Default aggregation spec passed to :meth:`StatsHelper.grouped_agg`.

Pre-defined keys: ``"Average"``, ``"StdDev"``, ``"Median"``, ``"Q1"``,
``"Q3"``, ``"P90"``, ``"Max"``, ``"Min"``, ``"Range"``, ``"IQR"``.
"""


# ---------------------------------------------------------------------------
# Typed structures
# ---------------------------------------------------------------------------

class ComparisonRecord(TypedDict):
    """A single aggregated record produced by :meth:`StatsHelper.comparison_data`."""

    bucket: str
    """Bucket label (stringified value of the bucket column or function)."""

    mean: float
    """Group mean within this bucket, rounded to 2 d.p."""

    std: float
    """Standard deviation within this bucket, rounded to 4 d.p."""

    ci: float
    """95 % confidence-interval half-width (t-based); ``0.0`` when ``n < 2``."""

    n: int
    """Sample count contributing to this bucket."""


#: Nested return type of :meth:`StatsHelper.comparison_data`.
#: Shape: ``{filter_key: {group_name: [ComparisonRecord, ...]}}``
ComparisonData = Dict[Any, Dict[str, List[ComparisonRecord]]]

class ScatterInfo(TypedDict):
    """Per-metric scatter payload produced by :func:`build_correlation_data`."""
    x: List[float]
    y: List[float]
    r: Optional[float]
    p: Optional[float]
    slope: Optional[float]
    intercept: Optional[float]
    loess_x: List[float]
    loess_y: List[float]
    n: int
    depts: List[str]
    yearmonths: List[str]

# ---------------------------------------------------------------------------
# StatsHelper
# ---------------------------------------------------------------------------

class StatsHelper:
    """Aggregation, row-mutation, and confidence-interval utilities.

    All methods are **static** — the class is never instantiated.
    """

    # ------------------------------------------------------------------
    # Core aggregation
    # ------------------------------------------------------------------

    @staticmethod
    def grouped_agg(
        df: pd.DataFrame,
        group_cols: List[str],
        value_col: str,
        aggs: Optional[Dict[str, AggFn]] = ...,
        decimals: int = ...,
    ) -> pd.DataFrame:
        """Group a DataFrame by one or more columns and aggregate a single
        numeric column.

        Parameters
        ----------
        df:
            Source DataFrame.
        group_cols:
            Columns to group by (e.g. ``["Ward", "Month"]``).
        value_col:
            The numeric column to aggregate.
        aggs:
            Mapping of *output column name* → :data:`AggFn`.
            Defaults to :data:`STANDARD_AGGS`.
        decimals:
            Rounding precision applied to every aggregated column
            (default ``2``).

        Returns
        -------
        pd.DataFrame
            Flat DataFrame containing *group_cols* plus one column per
            entry in *aggs*, with values rounded to *decimals*.
        """
        ...

    @staticmethod
    def comparison_data(
        df: pd.DataFrame,
        group_col: str,
        value_col: str,
        groups: List[str],
        bucket_col: Optional[str] = ...,
        bucket_fn: Optional[Callable[[pd.DataFrame], pd.Series]] = ...,
        filter_col: Optional[str] = ...,
        filter_values: Optional[List[Any]] = ...,
    ) -> ComparisonData:
        """Build a nested structure of descriptive statistics suitable for
        passing to ``HTMLBuilder.set_comparison``.

        Exactly **one** of *bucket_col* or *bucket_fn* must be supplied.

        When *filter_col* / *filter_values* are given, the top-level keys of
        the returned dict are the individual filter values (e.g. shift hours).
        Otherwise the dict has a single key ``"all"``.

        Parameters
        ----------
        df:
            Source DataFrame.
        group_col:
            Column that identifies each group (e.g. ward name).
        value_col:
            Numeric column to aggregate (e.g. fall count per shift).
        groups:
            Explicit ordered list of group values to include.
        bucket_col:
            Name of an existing column whose distinct values become buckets
            along the comparison x-axis.
        bucket_fn:
            Callable ``(df: DataFrame) -> Series`` that derives bucket labels
            on the fly.  Use this when no single column captures the desired
            bucketing (e.g. hour-of-day derived from a timestamp column).
        filter_col:
            Optional column used to pre-slice *df* before aggregating.
        filter_values:
            Ordered list of values from *filter_col* to iterate over.

        Returns
        -------
        ComparisonData
            ``{filter_key: {group: [ComparisonRecord, ...]}}``

        Raises
        ------
        ValueError
            If neither *bucket_col* nor *bucket_fn* is supplied.
        """
        ...

    @staticmethod
    def t_crit_table(max_df: int = ...) -> Dict[int, float]:
        """Pre-compute two-tailed t-critical values at α = 0.05.

        Parameters
        ----------
        max_df:
            Highest degrees-of-freedom to include (default ``120``).

        Returns
        -------
        Dict[int, float]
            ``{df: t_critical}`` for ``df`` in ``range(1, max_df + 1)``.
        """
        ...

    # ------------------------------------------------------------------
    # Row-level helpers
    # ------------------------------------------------------------------

    @staticmethod
    def add_custom_group(
        df: pd.DataFrame,
        group_col: str,
        group_label: str,
        mask: pd.Series,  # pd.Series[bool]
        value_col: str,
        aggs: Optional[Dict[str, AggFn]] = ...,
        decimals: int = ...,
    ) -> pd.DataFrame:
        """Append an aggregated summary row for an ad-hoc group.

        Parameters
        ----------
        df:
            Existing summary DataFrame to append to.
        group_col:
            Name of the column that holds the group label.
        group_label:
            Label written into *group_col* for the new row.
        mask:
            Boolean ``Series`` aligned to the **original raw DataFrame**
            selecting the rows that belong to this custom group.
        value_col:
            Numeric column to aggregate.
        aggs:
            Aggregation spec — defaults to :data:`STANDARD_AGGS`.
        decimals:
            Rounding precision (default ``2``).

        Returns
        -------
        pd.DataFrame
            Copy of *df* with the new aggregated row appended.
        """
        ...

    @staticmethod
    def add_ci(
        df: pd.DataFrame,
        mean_col: str = ...,
        std_col: str = ...,
        n_col: str = ...,
        ci_col: str = ...,
        decimals: int = ...,
    ) -> pd.DataFrame:
        """Append a 95 % confidence-interval (half-width) column to a
        summary DataFrame.

        Assumes the DataFrame already contains per-group mean, standard
        deviation, and sample count — as produced by :meth:`grouped_agg`.

        Parameters
        ----------
        df:
            Summary DataFrame to extend.
        mean_col:
            Column holding per-group means (default ``"Average"``).
        std_col:
            Column holding per-group standard deviations (default
            ``"StdDev"``).
        n_col:
            Column holding per-group sample counts (default ``"Count"``).
        ci_col:
            Name of the new CI column to add (default ``"CI_95"``).
        decimals:
            Rounding precision (default ``2``).

        Returns
        -------
        pd.DataFrame
            Copy of *df* with *ci_col* appended.  Rows where ``n < 2`` or
            *std_col* is ``NaN`` receive a CI of ``0.0``.
        """
        ...

    @staticmethod
    def subtraction_row(
        df: pd.DataFrame,
        row_a_mask: pd.Series,  # pd.Series[bool]
        row_b_mask: pd.Series,  # pd.Series[bool]
        label_col: str,
        result_label: str,
        numeric_cols: Optional[List[str]] = ...,
    ) -> pd.DataFrame:
        """Append a row whose numeric values are ``row_a − row_b``.

        Parameters
        ----------
        df:
            Summary DataFrame with at least one non-numeric label column.
        row_a_mask:
            Boolean ``Series`` selecting **exactly one** row (the minuend).
        row_b_mask:
            Boolean ``Series`` selecting **exactly one** row (the subtrahend).
        label_col:
            Column that receives *result_label* in the new row.
        result_label:
            Text placed in *label_col* (e.g. ``"Δ Night–Day"``).
        numeric_cols:
            Columns to subtract.  Defaults to all numeric columns in *df*.

        Returns
        -------
        pd.DataFrame
            Copy of *df* with the difference row appended.
        """
        ...

    @staticmethod
    def addition_row(
        df: pd.DataFrame,
        row_masks: List[pd.Series],  # List[pd.Series[bool]]
        label_col: str,
        result_label: str,
        numeric_cols: Optional[List[str]] = ...,
    ) -> pd.DataFrame:
        """Append a row whose numeric values are the element-wise sum of two
        or more selected rows.

        Parameters
        ----------
        df:
            Summary DataFrame.
        row_masks:
            List of boolean ``Series``, each selecting **exactly one** row.
        label_col:
            Column that receives *result_label* in the new row.
        result_label:
            Text placed in *label_col* (e.g. ``"Combined A+B"``).
        numeric_cols:
            Columns to sum.  Defaults to all numeric columns in *df*.

        Returns
        -------
        pd.DataFrame
            Copy of *df* with the summed row appended.
        """
        ...

    @staticmethod
    def lambda_row(
        df: pd.DataFrame,
        fn: Callable[[pd.DataFrame], Dict[str, Any]],
        label_col: str,
        result_label: str,
    ) -> pd.DataFrame:
        """Append a fully custom row computed by an arbitrary callable.

        Parameters
        ----------
        df:
            Summary DataFrame passed to *fn*.
        fn:
            Callable with signature ``(df: DataFrame) -> Dict[str, Any]``.

            Example::

                fn=lambda d: {"Average": d["Average"].mean()}

        label_col:
            Column that receives *result_label* in the new row.
        result_label:
            Text placed in *label_col* (e.g. ``"Global Mean"``).

        Returns
        -------
        pd.DataFrame
            Copy of *df* with the computed row appended.

        Example
        -------
        >>> df = StatsHelper.lambda_row(
        ...     df,
        ...     fn=lambda d: {"Average": d["Average"].mean()},
        ...     label_col="Ward",
        ...     result_label="Global Mean",
        ... )
        """
        ...

    # ------------------------------------------------------------------
    # Correlation / scatter helpers
    # ------------------------------------------------------------------

    @staticmethod
    def pearson_r(
        x: np.ndarray,
        y: np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray, float, float]:
        """Compute Pearson *r* after dropping non-finite pairs.

        Parameters
        ----------
        x, y:
            Raw paired arrays.  Need not be pre-filtered for NaN / inf.

        Returns
        -------
        Tuple[np.ndarray, np.ndarray, float, float]
            ``(x_clean, y_clean, r, p)`` — the filtered arrays and the
            Pearson correlation coefficient and two-tailed p-value.
            *r* and *p* are ``float("nan")`` when fewer than 3 valid pairs
            remain after filtering.
        """
        ...

    @staticmethod
    def scatter_stats(
        df: pd.DataFrame,
        x_col: str,
        y_cols: List[str],
        label: str,
        id_col: Optional[str] = ...,
        time_col: Optional[str] = ...,
        loess_frac: float = ...,
    ) -> Dict[str, Any]:
        """Compute per-metric scatter statistics for one labelled segment.

        For each column in *y_cols* the method calculates Pearson *r* / *p*,
        OLS slope and intercept, and a LOESS smoothed curve.

        Parameters
        ----------
        df:
            DataFrame containing *x_col* and all columns in *y_cols*.
        x_col:
            Predictor / x-axis column name.
        y_cols:
            Outcome / y-axis column names (one entry per scatter series).
        label:
            Human-readable segment name stored under ``"label"`` in the
            returned dict.
        id_col:
            Optional column whose values are stored as ``"ids"`` — useful for
            tooltip look-ups when *df* spans multiple groups.
        time_col:
            Optional column whose values are stored as ``"timepoints"``
            (e.g. ``"YearMonth"`` strings for x-axis tooltips).
        loess_frac:
            LOWESS smoothing bandwidth (default ``0.6``).  Automatically
            raised to ``3 / n`` for small datasets.

        Returns
        -------
        Dict[str, Any]
            ``{"label": label, <y_col>: ScatterInfo, ...}``
        """
        ...

    @staticmethod
    def build_correlation_data(
        df_workload: pd.DataFrame,
        df_secondary: pd.DataFrame,
        hour: int,
        sec_col1: str,
        sec_col2: str,
        workload_date_col: str = ...,
        workload_dept_col: str = ...,
        workload_value_col: str = ...,
        secondary_year_col: str = ...,
        secondary_month_col: str = ...,
        secondary_dept_col: str = ...,
        named_groups: Optional[Dict[str, List[str]]] = ...,
        loess_frac: float = ...,
    ) -> Dict[str, Any]:
        """Build scatter data (Pearson + OLS + LOESS) for the given *hour*,
        keyed by department, named group, and an ``"Overall"`` aggregate.

        Parameters
        ----------
        df_workload:
            Workload DataFrame; must contain *workload_date_col*,
            *workload_dept_col*, ``"Hour"``, and *workload_value_col*.
        df_secondary:
            Secondary-metric DataFrame; must contain *secondary_year_col*,
            *secondary_month_col*, *secondary_dept_col*, *sec_col1*, and
            *sec_col2*.
        hour:
            Shift hour to filter on (e.g. ``10``).
        sec_col1:
            First secondary-metric column (e.g. ``"FALLS"``).
        sec_col2:
            Second secondary-metric column (e.g. ``"PRESSURE"``).
        workload_date_col:
            Date column in *df_workload* (default ``"Date"``).
        workload_dept_col:
            Department column in *df_workload* (default ``"Department_Name"``).
        workload_value_col:
            Numeric workload column in *df_workload*
            (default ``"Value_Per_Employee"``).
        secondary_year_col:
            Year column in *df_secondary* (default ``"Year"``).
        secondary_month_col:
            Month column in *df_secondary* (default ``"Month"``).
        secondary_dept_col:
            Department column in *df_secondary* (default ``"Department_Name"``).
        named_groups:
            Optional ``{group_label: [dept, ...]}`` mapping.  When supplied,
            a pooled scatter entry is built for each group and the group
            labels are recorded under ``"__department_groups__"``.
        loess_frac:
            LOESS smoothing bandwidth (default ``0.6``).

        Returns
        -------
        Dict[str, Any]
            Keys: ``__scatter__``, ``__departments__``,
            ``__department_groups__``, ``__col1__``, ``__col2__``.
            Pass directly to :meth:`HTMLBuilder.set_correlation`.
        """
        ...
