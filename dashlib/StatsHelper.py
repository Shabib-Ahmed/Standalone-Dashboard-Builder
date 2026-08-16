from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Union

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats
from statsmodels.nonparametric.smoothers_lowess import lowess

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import TypedDict

    class ComparisonRecord(TypedDict):
        bucket: str
        mean: float
        std: float
        ci: float
        n: int


# Public alias used at runtime for annotation strings (from __future__ import annotations)
AggFn = Union[str, Callable[[Any], Any]]

#: Default aggregation dict — pass directly to ``StatsHelper.grouped_agg``.
STANDARD_AGGS: Dict[str, AggFn] = {
    "Average": "mean",
    "StdDev": "std",
    "Median": "median",
    "Q1": lambda x: x.quantile(0.25),
    "Q3": lambda x: x.quantile(0.75),
    "P90": lambda x: x.quantile(0.90),
    "Max": "max",
    "Min": "min",
    "Range": lambda x: x.max() - x.min(),
    "IQR": lambda x: x.quantile(0.75) - x.quantile(0.25),
}

# Runtime-accessible type alias (mirrors the TypedDict shape for documentation)
ComparisonData = Dict[Any, Dict[str, List[Dict[str, Any]]]]


class StatsHelper:
    """Aggregation, row-mutation, and comparison-CI utilities.

    All methods are static — instantiation is never required.
    """

    # ------------------------------------------------------------------
    # Core aggregation
    # ------------------------------------------------------------------

    @staticmethod
    def grouped_agg(
        df: pd.DataFrame,
        group_cols: List[str],
        value_col: str,
        aggs: Optional[Dict[str, AggFn]] = None,
        decimals: int = 2,
    ) -> pd.DataFrame:
        """Group, aggregate, and round a single value column.

        Parameters
        ----------
        df : Source DataFrame.
        group_cols : Columns to group by (e.g. ``["Ward", "Month"]``).
        value_col : The numeric column being aggregated.
        aggs : Mapping of output-column-name → aggregation function or pandas
               aggregation string.  Defaults to ``STANDARD_AGGS``.
        decimals : Rounding precision applied to every aggregated column.

        Returns
        -------
        pd.DataFrame
            Flat DataFrame with *group_cols* plus one column per aggregation.
        """
        aggs = aggs or STANDARD_AGGS
        return (
            df.groupby(group_cols)[value_col]
            .agg(**aggs)
            .reset_index()
            .round(decimals)
        )

    @staticmethod
    def comparison_data(
        df: pd.DataFrame,
        group_col: str,
        value_col: str,
        groups: List[str],
        bucket_col: Optional[str] = None,
        bucket_fn: Optional[Callable[[pd.DataFrame], pd.Series]] = None,
        filter_col: Optional[str] = None,
        filter_values: Optional[List[Any]] = None,
    ) -> ComparisonData:
        """Build a nested ``{filter_value: {group: [record, ...]}}`` structure
        containing mean, std, n, and 95 % CI for every group × bucket.

        Buckets are defined in exactly one of two ways:

        * **bucket_col** — name of an existing column to group by.
        * **bucket_fn** — callable that receives the (optionally sliced)
          DataFrame and returns a Series of bucket labels.

        If *filter_col* / *filter_values* are given, the outer key is each
        filter value (e.g. shift hour).  Otherwise the structure is
        ``{"all": {group: [...]}}`` .

        Parameters
        ----------
        df : Source DataFrame.
        group_col : Column that identifies each group (e.g. ward name).
        value_col : Numeric column to aggregate (e.g. fall count).
        groups : Explicit list of group values to include.
        bucket_col : Column whose distinct values become buckets.
        bucket_fn : Alternative to *bucket_col* — derives buckets on the fly.
        filter_col : Optional column used to slice *df* before aggregating.
        filter_values : Values of *filter_col* to iterate over.

        Returns
        -------
        ComparisonData
            ``{filter_key: {group: [{"bucket", "mean", "std", "ci", "n"}, ...]}}``

        Raises
        ------
        ValueError
            If neither *bucket_col* nor *bucket_fn* is supplied.
        """
        if bucket_col is None and bucket_fn is None:
            raise ValueError("Supply either bucket_col or bucket_fn.")

        if filter_col and filter_values:
            slices = [(fv, df[df[filter_col] == fv]) for fv in filter_values]
        else:
            slices = [("all", df)]

        result: ComparisonData = {}
        for key, slice_df in slices:
            slice_df = slice_df.copy()
            slice_df["_bucket"] = (
                bucket_fn(slice_df) if bucket_fn is not None else slice_df[bucket_col]
            )
            result[key] = {}
            for grp in groups:
                agg = (
                    slice_df[slice_df[group_col] == grp]
                    .groupby("_bucket")[value_col]
                    .agg(["mean", "std", "count"])
                    .sort_index()
                )
                records: List[Dict[str, Any]] = []
                for bucket, row in agg.iterrows():
                    n = int(row["count"])
                    std = float(row["std"]) if pd.notna(row["std"]) else 0.0
                    ci = 0.0
                    if n > 1:
                        ci = scipy_stats.t.ppf(0.975, n - 1) * std / (n ** 0.5)
                    records.append({
                        "bucket": str(bucket),
                        "mean": round(float(row["mean"]), 2),
                        "std": round(std, 4),
                        "ci": round(ci, 2),
                        "n": n,
                    })
                result[key][grp] = records
        return result

    @staticmethod
    def t_crit_table(max_df: int = 120) -> Dict[int, float]:
        """Pre-computed two-tailed t-critical values at α = 0.05.

        Parameters
        ----------
        max_df : Highest degrees-of-freedom to include (default 120).

        Returns
        -------
        Dict[int, float]
            ``{df: t_critical}`` for df in ``range(1, max_df + 1)``.
        """
        return {
            d: round(scipy_stats.t.ppf(0.975, d), 4)
            for d in range(1, max_df + 1)
        }

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
        aggs: Optional[Dict[str, AggFn]] = None,
        decimals: int = 2,
    ) -> pd.DataFrame:
        """Append an aggregated summary row for an ad-hoc group.

        Useful for adding a synthetic "Combined Ward A+B" or
        "All Nights" row to an existing summary table without modifying
        the source DataFrame.

        Parameters
        ----------
        df : Existing summary DataFrame to append to.
        group_col : Name of the column that holds the group label.
        group_label : Label to write into *group_col* for the new row.
        mask : Boolean Series (aligned to the *original* raw DataFrame)
               selecting the rows that belong to this custom group.
        value_col : Numeric column to aggregate.
        aggs : Aggregation spec — defaults to ``STANDARD_AGGS``.
        decimals : Rounding precision.

        Returns
        -------
        pd.DataFrame
            Copy of *df* with the new row appended.
        """
        aggs = aggs or STANDARD_AGGS
        subset = df[mask.reindex(df.index, fill_value=False)][value_col]
        row: Dict[str, Any] = {group_col: group_label}
        for col_name, fn in aggs.items():
            if callable(fn):
                row[col_name] = round(fn(subset), decimals)
            else:
                row[col_name] = round(getattr(subset, fn)(), decimals)
        return pd.concat([df, pd.DataFrame([row])], ignore_index=True)

    @staticmethod
    def add_ci(
        df: pd.DataFrame,
        mean_col: str = "Average",
        std_col: str = "StdDev",
        n_col: str = "Count",
        ci_col: str = "CI_95",
        decimals: int = 2,
    ) -> pd.DataFrame:
        """Append a 95 % confidence-interval column to a summary DataFrame.

        Assumes the DataFrame already contains per-group mean, std, and n.

        Parameters
        ----------
        df : Summary DataFrame (e.g. produced by ``grouped_agg``).
        mean_col, std_col, n_col : Source column names.
        ci_col : Name of the new CI column (half-width).
        decimals : Rounding precision.

        Returns
        -------
        pd.DataFrame
            *df* with *ci_col* added (copy returned).
        """
        df = df.copy()

        def _ci(row: pd.Series) -> float:
            n = row[n_col]
            if n < 2 or pd.isna(row[std_col]):
                return 0.0
            t = scipy_stats.t.ppf(0.975, n - 1)
            return round(t * row[std_col] / (n ** 0.5), decimals)

        df[ci_col] = df.apply(_ci, axis=1)
        return df

    @staticmethod
    def subtraction_row(
        df: pd.DataFrame,
        row_a_mask: pd.Series,  # pd.Series[bool]
        row_b_mask: pd.Series,  # pd.Series[bool]
        label_col: str,
        result_label: str,
        numeric_cols: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """Append a row whose numeric values are row_a − row_b.

        Handy for "difference" rows in summary tables (e.g.
        Night shift minus Day shift).

        Parameters
        ----------
        df : Summary DataFrame with at least one non-numeric label column.
        row_a_mask, row_b_mask : Boolean Series selecting exactly one row each.
        label_col : Column that receives *result_label* in the new row.
        result_label : Text placed in *label_col* (e.g. ``"Δ Night–Day"``).
        numeric_cols : Columns to subtract.  Defaults to all numeric columns.

        Returns
        -------
        pd.DataFrame
            *df* with the difference row appended.
        """
        numeric_cols = numeric_cols or df.select_dtypes("number").columns.tolist()
        a = df[row_a_mask][numeric_cols].iloc[0]
        b = df[row_b_mask][numeric_cols].iloc[0]
        diff_row: Dict[str, Any] = {
            label_col: result_label,
            **{c: round(a[c] - b[c], 4) for c in numeric_cols},
        }
        return pd.concat([df, pd.DataFrame([diff_row])], ignore_index=True)

    @staticmethod
    def addition_row(
        df: pd.DataFrame,
        row_masks: List[pd.Series],  # List[pd.Series[bool]]
        label_col: str,
        result_label: str,
        numeric_cols: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """Append a row whose numeric values are the element-wise sum of
        two or more selected rows.

        Parameters
        ----------
        df : Summary DataFrame.
        row_masks : List of boolean Series, each selecting exactly one row.
        label_col : Column that receives *result_label* in the new row.
        result_label : Text placed in *label_col* (e.g. ``"Combined A+B"``).
        numeric_cols : Columns to sum.  Defaults to all numeric columns.

        Returns
        -------
        pd.DataFrame
            *df* with the sum row appended.
        """
        numeric_cols = numeric_cols or df.select_dtypes("number").columns.tolist()
        total = sum(df[m][numeric_cols].iloc[0] for m in row_masks)
        sum_row: Dict[str, Any] = {
            label_col: result_label,
            **{c: round(total[c], 4) for c in numeric_cols},
        }
        return pd.concat([df, pd.DataFrame([sum_row])], ignore_index=True)

    @staticmethod
    def lambda_row(
        df: pd.DataFrame,
        fn: Callable[[pd.DataFrame], Dict[str, Any]],
        label_col: str,
        result_label: str,
    ) -> pd.DataFrame:
        """Append a fully custom row computed by an arbitrary callable.

        The callable receives the current DataFrame and must return a dict
        mapping column names to values.  The *label_col* / *result_label*
        pair is merged in automatically so the callable need not include it.

        Parameters
        ----------
        df : Summary DataFrame passed to *fn*.
        fn : ``lambda df: {"Average": df["Average"].mean(), ...}``
        label_col : Column that receives *result_label*.
        result_label : Text placed in *label_col*.

        Returns
        -------
        pd.DataFrame
            *df* with the computed row appended.

        Example
        -------
        >>> df = StatsHelper.lambda_row(
        ...     df,
        ...     fn=lambda d: {"Average": d["Average"].mean()},
        ...     label_col="Ward",
        ...     result_label="Global Mean",
        ... )
        """
        computed = fn(df)
        new_row = {label_col: result_label, **computed}
        return pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    # ------------------------------------------------------------------
    # Correlation / scatter helpers
    # ------------------------------------------------------------------

    @staticmethod
    def pearson_r(
        x: np.ndarray,
        y: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray, float, float]:
        """Compute Pearson r after dropping non-finite pairs.

        Parameters
        ----------
        x, y : Raw paired arrays (need not be pre-filtered).

        Returns
        -------
        tuple
            ``(x_clean, y_clean, r, p)`` where *x_clean* / *y_clean* contain
            only the finite-pair rows and *r* / *p* are ``float("nan")`` when
            fewer than 3 valid pairs exist.
        """
        mask = np.isfinite(x) & np.isfinite(y)
        x_c, y_c = x[mask], y[mask]
        if len(x_c) >= 3:
            r, p = scipy_stats.pearsonr(x_c, y_c)
        else:
            r = p = float("nan")
        return x_c, y_c, float(r), float(p)

    @staticmethod
    def scatter_stats(
        df: pd.DataFrame,
        x_col: str,
        y_cols: List[str],
        label: str,
        id_col: Optional[str] = None,
        time_col: Optional[str] = None,
        loess_frac: float = 0.6,
    ) -> Dict[str, Any]:
        """Compute per-metric scatter statistics for one labelled segment.

        For each column in *y_cols* the method calculates:

        * Pearson *r* and two-tailed *p*-value (NaN when ``n < 3``).
        * OLS slope and intercept (NaN when ``n < 2``).
        * LOESS smoothed curve (empty when ``n < 5``).

        Parameters
        ----------
        df : DataFrame containing *x_col* and every column in *y_cols*.
        x_col : Name of the predictor / x-axis column.
        y_cols :
            Names of the outcome / y-axis columns (one entry → one scatter
            series; two entries → two series, e.g. falls and pressure).
        label : Human-readable name for this segment (stored under ``"label"``).
        id_col :
            Optional column whose values are included in the output as
            ``"ids"`` — useful for tooltip look-ups (e.g. department names
            when *df* spans multiple departments).
        time_col :
            Optional column whose values are stored as ``"timepoints"``
            (e.g. a ``"YearMonth"`` string column for x-axis tooltips).
        loess_frac :
            Smoothing bandwidth passed to LOWESS (default ``0.6``).
            Automatically raised to ``3 / n`` when the dataset is small.

        Returns
        -------
        Dict[str, Any]
            ``{"label": label, <y_col>: ScatterInfo, ...}`` where each
            ``ScatterInfo`` value contains ``x``, ``y``, ``r``, ``p``,
            ``slope``, ``intercept``, ``loess_x``, ``loess_y``, ``n``,
            ``ids``, and ``timepoints``.
        """
        out: Dict[str, Any] = {"label": label}
        for y_col in y_cols:
            x_raw = df[x_col].values.astype(float)
            y_raw = df[y_col].values.astype(float)
            x, y, r, p = StatsHelper.pearson_r(x_raw, y_raw)

            slope = intercept = float("nan")
            if len(x) >= 2:
                slope, intercept = np.polyfit(x, y, 1)

            loess_x: List[float] = []
            loess_y: List[float] = []
            if len(x) >= 5:
                frac = max(loess_frac, 3.0 / len(x))
                sm = lowess(y, x, frac=frac, is_sorted=False)
                loess_x = np.round(sm[:, 0], 6).tolist()
                loess_y = np.round(sm[:, 1], 6).tolist()

            out[y_col] = {
                "x":          x.tolist(),
                "y":          y.tolist(),
                "r":          round(r, 4) if np.isfinite(r) else None,
                "p":          round(p, 6) if np.isfinite(p) else None,
                "slope":      round(float(slope), 6) if np.isfinite(slope) else None,
                "intercept":  round(float(intercept), 6) if np.isfinite(intercept) else None,
                "loess_x":    loess_x,
                "loess_y":    loess_y,
                "n":          int(len(x)),
                "ids":        df[id_col].tolist() if id_col and id_col in df.columns else [],
                "timepoints": df[time_col].tolist() if time_col and time_col in df.columns else [],
            }
        return out

    @staticmethod
    def build_correlation_data(
        df_workload: pd.DataFrame,
        df_secondary: pd.DataFrame,
        hour: int,
        sec_col1: str,
        sec_col2: str,
        workload_date_col: str = "Date",
        workload_dept_col: str = "Department_Name",
        workload_value_col: str = "Value_Per_Employee",
        secondary_year_col: str = "Year",
        secondary_month_col: str = "Month",
        secondary_dept_col: str = "Department_Name",
        named_groups: Optional[Dict[str, List[str]]] = None,
        loess_frac: float = 0.6,
    ) -> Dict[str, Any]:
        """Build scatter data (Pearson + OLS + LOESS) for *hour*, keyed by
        department, named group, and an "Overall" aggregate.

        Parameters
        ----------
        df_workload :
            Workload DataFrame; must contain *workload_date_col*,
            *workload_dept_col*, ``"Hour"``, and *workload_value_col*.
        df_secondary :
            Secondary-metric DataFrame; must contain *secondary_year_col*,
            *secondary_month_col*, *secondary_dept_col*, *sec_col1*, and
            *sec_col2*.
        hour : Shift hour to filter on (e.g. ``10`` for 10:00).
        sec_col1 : First secondary-metric column (e.g. ``"FALLS"``).
        sec_col2 : Second secondary-metric column (e.g. ``"PRESSURE"``).
        workload_date_col : Date column in *df_workload* (default ``"Date"``).
        workload_dept_col : Department column in *df_workload*.
        workload_value_col : Numeric workload column in *df_workload*.
        secondary_year_col : Year column in *df_secondary*.
        secondary_month_col : Month column in *df_secondary*.
        secondary_dept_col : Department column in *df_secondary*.
        named_groups :
            Optional ``{group_label: [dept, ...]}`` mapping.  When supplied,
            a scatter entry is built for each group (pooling its member
            departments) and the group labels are recorded under
            ``"__department_groups__"``.
        loess_frac : LOESS smoothing bandwidth (default ``0.6``).

        Returns
        -------
        Dict[str, Any]
            Keys: ``__scatter__``, ``__departments__``,
            ``__department_groups__``, ``__col1__``, ``__col2__``.
            Pass directly to :meth:`HTMLBuilder.set_correlation`.
        """
        # --- workload: filter hour, build YearMonth ---
        wl = df_workload[df_workload["Hour"] == hour].copy()
        wl[workload_date_col] = pd.to_datetime(wl[workload_date_col])
        wl["YearMonth"] = (
            wl[workload_date_col].dt.year.astype(str)
            + "-"
            + wl[workload_date_col].dt.month.astype(str).str.zfill(2)
        )
        wl_agg = (
            wl.groupby([workload_dept_col, "YearMonth"])[workload_value_col]
            .mean()
            .reset_index()
            .rename(columns={workload_value_col: "Workload_Avg"})
            .round(4)
        )

        # --- secondary: build YearMonth ---
        sec = df_secondary.copy()
        sec["YearMonth"] = (
            sec[secondary_year_col].astype(str)
            + "-"
            + sec[secondary_month_col].astype(str).str.zfill(2)
        )
        sec_agg = (
            sec.groupby([secondary_dept_col, "YearMonth"])
            .agg(col1_avg=(sec_col1, "mean"), col2_avg=(sec_col2, "mean"))
            .reset_index()
            .round(4)
        )
        # normalise to a shared dept key
        sec_agg = sec_agg.rename(columns={secondary_dept_col: workload_dept_col})

        merged = wl_agg.merge(sec_agg, on=[workload_dept_col, "YearMonth"], how="inner")
        # rename aggregated columns to the original metric names for scatter_stats
        merged = merged.rename(columns={"col1_avg": sec_col1, "col2_avg": sec_col2})

        departments = sorted(merged[workload_dept_col].unique().tolist())

        scatter: Dict[str, Any] = {}

        # per-department entries
        for dept in departments:
            sub = merged[merged[workload_dept_col] == dept]
            scatter[dept] = StatsHelper.scatter_stats(
                sub,
                x_col=     "Workload_Avg",
                y_cols=    [sec_col1, sec_col2],
                label=     dept,
                time_col=  "YearMonth",
                loess_frac=loess_frac,
            )

        # overall (all departments pooled)
        scatter["Overall"] = StatsHelper.scatter_stats(
            merged,
            x_col=     "Workload_Avg",
            y_cols=    [sec_col1, sec_col2],
            label=     "Overall",
            id_col=    workload_dept_col,
            time_col=  "YearMonth",
            loess_frac=loess_frac,
        )

        # named groups (e.g. MED SURGE, ICU)
        group_labels: List[str] = []
        if named_groups:
            for group_name, group_depts in named_groups.items():
                sub = merged[merged[workload_dept_col].isin(group_depts)]
                scatter[group_name] = StatsHelper.scatter_stats(
                    sub,
                    x_col=     "Workload_Avg",
                    y_cols=    [sec_col1, sec_col2],
                    label=     group_name,
                    id_col=    workload_dept_col,
                    time_col=  "YearMonth",
                    loess_frac=loess_frac,
                )
                group_labels.append(group_name)

        return {
            "__scatter__":           scatter,
            "__departments__":       departments,
            "__department_groups__": group_labels,
            "__col1__":              sec_col1,
            "__col2__":              sec_col2,
        }