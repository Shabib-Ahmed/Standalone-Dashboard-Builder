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


def _build_yearmonth(df: pd.DataFrame, date_col: str) -> pd.Series:
    """Derive a YYYY-MM period key from a parsed datetime column."""
    dt = pd.to_datetime(df[date_col])
    return dt.dt.year.astype(str) + "-" + dt.dt.month.astype(str).str.zfill(2)


def _build_yearmonth_from_parts(
    df: pd.DataFrame, year_col: str, month_col: str
) -> pd.Series:
    """Derive a YYYY-MM period key from separate year/month integer columns."""
    return df[year_col].astype(str) + "-" + df[month_col].astype(str).str.zfill(2)


class StatsHelper:

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
        df_primary: pd.DataFrame,
        df_secondary: pd.DataFrame,
        # --- primary (x-axis / "workload") configuration ---
        primary_value_col: str,
        primary_entity_col: str,
        primary_date_col: str,
        primary_agg_col: str = "Primary_Avg",
        # --- optional scalar filter on primary (e.g. hour-of-day) ---
        primary_filter_col: Optional[str] = None,
        primary_filter_value: Optional[Any] = None,
        # --- secondary (y-axis) configuration ---
        secondary_y_cols: List[str] = (),           # type: ignore[assignment]
        secondary_entity_col: Optional[str] = None, # defaults to primary_entity_col
        # secondary date: either a single datetime column …
        secondary_date_col: Optional[str] = None,
        # … or two integer part-columns (year + month)
        secondary_year_col: Optional[str] = None,
        secondary_month_col: Optional[str] = None,
        # --- grouping ---
        named_groups: Optional[Dict[str, List[str]]] = None,
        loess_frac: float = 0.6,
    ) -> Dict[str, Any]:
        secondary_y_cols = list(secondary_y_cols)
        if not secondary_y_cols:
            raise ValueError("secondary_y_cols must contain at least one column name.")

        sec_entity_col = secondary_entity_col or primary_entity_col

        # Validate secondary date specification
        has_single_date = secondary_date_col is not None
        has_part_dates  = secondary_year_col is not None and secondary_month_col is not None
        if not has_single_date and not has_part_dates:
            raise ValueError(
                "Provide either secondary_date_col or both secondary_year_col "
                "and secondary_month_col."
            )

        # ------------------------------------------------------------------
        # 1. Prepare primary
        # ------------------------------------------------------------------
        prim = df_primary.copy()
        if primary_filter_col is not None and primary_filter_value is not None:
            prim = prim[prim[primary_filter_col] == primary_filter_value]

        prim["_period"] = _build_yearmonth(prim, primary_date_col)

        prim_agg = (
            prim.groupby([primary_entity_col, "_period"])[primary_value_col]
            .mean()
            .reset_index()
            .rename(columns={
                primary_value_col: primary_agg_col,
                primary_entity_col: "_entity",
            })
            .round(4)
        )

        # ------------------------------------------------------------------
        # 2. Prepare secondary
        # ------------------------------------------------------------------
        sec = df_secondary.copy()
        if has_single_date:
            sec["_period"] = _build_yearmonth(sec, secondary_date_col)
        else:
            sec["_period"] = _build_yearmonth_from_parts(
                sec, secondary_year_col, secondary_month_col  # type: ignore[arg-type]
            )

        sec_agg = (
            sec.groupby([sec_entity_col, "_period"])[secondary_y_cols]
            .mean()
            .reset_index()
            .rename(columns={sec_entity_col: "_entity"})
            .round(4)
        )

        # ------------------------------------------------------------------
        # 3. Merge
        # ------------------------------------------------------------------
        merged = prim_agg.merge(sec_agg, on=["_entity", "_period"], how="inner")

        entities: List[str] = sorted(merged["_entity"].unique().tolist())

        # ------------------------------------------------------------------
        # 4. Build scatter data
        # ------------------------------------------------------------------
        scatter: Dict[str, Any] = {}

        for entity in entities:
            sub = merged[merged["_entity"] == entity]
            scatter[entity] = StatsHelper.scatter_stats(
                sub,
                x_col=      primary_agg_col,
                y_cols=     secondary_y_cols,
                label=      entity,
                time_col=   "_period",
                loess_frac= loess_frac,
            )

        scatter["Overall"] = StatsHelper.scatter_stats(
            merged,
            x_col=     primary_agg_col,
            y_cols=    secondary_y_cols,
            label=     "Overall",
            id_col=    "_entity",
            time_col=  "_period",
            loess_frac=loess_frac,
        )

        group_labels: List[str] = []
        if named_groups:
            for group_name, group_entities in named_groups.items():
                sub = merged[merged["_entity"].isin(group_entities)]
                scatter[group_name] = StatsHelper.scatter_stats(
                    sub,
                    x_col=     primary_agg_col,
                    y_cols=    secondary_y_cols,
                    label=     group_name,
                    id_col=    "_entity",
                    time_col=  "_period",
                    loess_frac=loess_frac,
                )
                group_labels.append(group_name)

        return {
            "__scatter__":        scatter,
            "__entities__":       entities,
            "__entity_groups__":  group_labels,
            "__y_cols__":         secondary_y_cols,
            "__primary_agg_col__": primary_agg_col,
        }