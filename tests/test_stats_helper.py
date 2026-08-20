import math

import numpy as np
import pandas as pd
import pytest

from dashlib.StatsHelper import StatsHelper

# ---------------------------------------------------------------------------
# grouped_agg
# ---------------------------------------------------------------------------

class TestGroupedAgg:
    def test_returns_dataframe(self, ward_df):
        result = StatsHelper.grouped_agg(ward_df, group_cols=["Group"], value_col="Metric")
        assert isinstance(result, pd.DataFrame)

    def test_group_columns_present(self, ward_df):
        result = StatsHelper.grouped_agg(ward_df, group_cols=["Group"], value_col="Metric")
        assert "Group" in result.columns

    def test_standard_agg_columns_present(self, ward_df):
        result = StatsHelper.grouped_agg(ward_df, group_cols=["Group"], value_col="Metric")
        for col in ("Average", "StdDev", "Median", "Q1", "Q3", "P90", "Max", "Min", "Range", "IQR"):
            assert col in result.columns, f"Missing column: {col}"

    def test_average_correct(self, ward_df):
        result = StatsHelper.grouped_agg(ward_df, group_cols=["Group"], value_col="Metric")
        group_x_avg = result.loc[result["Group"] == "X", "Average"].iloc[0]
        assert group_x_avg == pytest.approx(20.0, abs=0.01)

    def test_rounding_applied(self, ward_df):
        result = StatsHelper.grouped_agg(ward_df, group_cols=["Group"], value_col="Metric", decimals=1)
        numeric_cols = result.select_dtypes(include="number").columns
        for col in numeric_cols:
            for val in result[col]:
                if val != val:  # skip NaN (NaN != NaN is always True)
                    continue
                assert round(val, 1) == pytest.approx(val, abs=1e-9)

    def test_multi_group_cols(self, ward_df):
        result = StatsHelper.grouped_agg(
            ward_df, group_cols=["Group", "Bucket"], value_col="Metric"
        )
        assert "Group" in result.columns
        assert "Bucket" in result.columns

    def test_custom_agg(self, ward_df):
        result = StatsHelper.grouped_agg(
            ward_df,
            group_cols=["Group"],
            value_col="Metric",
            aggs={"MyMean": "mean", "MyMax": "max"},
        )
        assert "MyMean" in result.columns
        assert "MyMax" in result.columns

    def test_one_row_per_group(self, ward_df):
        result = StatsHelper.grouped_agg(ward_df, group_cols=["Group"], value_col="Metric")
        assert len(result) == ward_df["Group"].nunique()


# ---------------------------------------------------------------------------
# comparison_data
# ---------------------------------------------------------------------------

class TestComparisonData:
    def test_raises_without_bucket(self, two_group_df):
        with pytest.raises(ValueError):
            StatsHelper.comparison_data(
                two_group_df,
                group_col="Group",
                value_col="Metric",
                groups=["X", "Y"],
                # neither bucket_col nor bucket_fn supplied
            )

    def test_bucket_col_returns_all_key(self, two_group_df):
        result = StatsHelper.comparison_data(
            two_group_df,
            group_col="Group",
            value_col="Metric",
            groups=["X", "Y"],
            bucket_col="Category",
        )
        assert "all" in result

    def test_filter_col_creates_per_value_keys(self, two_group_df):
        result = StatsHelper.comparison_data(
            two_group_df,
            group_col="Group",
            value_col="Metric",
            groups=["X", "Y"],
            bucket_col="Category",
            filter_col="Category",
            filter_values=["Alpha", "Beta"],
        )
        assert "Alpha" in result
        assert "Beta" in result

    def test_records_have_required_keys(self, two_group_df):
        result = StatsHelper.comparison_data(
            two_group_df,
            group_col="Group",
            value_col="Metric",
            groups=["X", "Y"],
            bucket_col="Category",
        )
        for group_dict in result.values():
            for records in group_dict.values():
                for rec in records:
                    for key in ("bucket", "mean", "std", "ci", "n"):
                        assert key in rec, f"Missing key '{key}' in record"

    def test_bucket_fn_accepted(self, two_group_df):
        result = StatsHelper.comparison_data(
            two_group_df,
            group_col="Group",
            value_col="Metric",
            groups=["X", "Y"],
            bucket_fn=lambda df: df["Category"],
        )
        assert result  # non-empty

    def test_ci_zero_when_n_less_than_2(self):
        df = pd.DataFrame({
            "Group":  ["X"],
            "Category": ["Alpha"],
            "Metric": [5.0],
        })
        result = StatsHelper.comparison_data(
            df,
            group_col="Group",
            value_col="Metric",
            groups=["X"],
            bucket_col="Category",
        )
        records = result["all"]["X"]
        assert all(rec["ci"] == 0.0 for rec in records if rec["n"] < 2)


# ---------------------------------------------------------------------------
# t_crit_table
# ---------------------------------------------------------------------------

class TestTCritTable:
    def test_returns_dict(self):
        table = StatsHelper.t_crit_table()
        assert isinstance(table, dict)

    def test_df_1_approx(self):
        table = StatsHelper.t_crit_table()
        assert abs(table[1] - 12.706) < 0.01

    def test_df_30_approx(self):
        table = StatsHelper.t_crit_table()
        assert abs(table[30] - 2.042) < 0.01

    def test_df_120_approx(self):
        table = StatsHelper.t_crit_table()
        assert abs(table[120] - 1.980) < 0.01

    def test_custom_max_df(self):
        table = StatsHelper.t_crit_table(max_df=10)
        assert set(table.keys()) == set(range(1, 11))

    def test_values_decrease_with_df(self):
        table = StatsHelper.t_crit_table()
        keys = sorted(table.keys())
        for a, b in zip(keys, keys[1:]):
            assert table[a] >= table[b], f"t_crit not monotone at df={a},{b}"


# ---------------------------------------------------------------------------
# add_ci
# ---------------------------------------------------------------------------

class TestAddCi:
    def test_appends_ci_column(self, summary_df):
        result = StatsHelper.add_ci(summary_df, mean_col="Average", std_col="StdDev", n_col="n")
        assert "CI_95" in result.columns

    def test_does_not_mutate_input(self, summary_df):
        original_cols = list(summary_df.columns)
        StatsHelper.add_ci(summary_df, mean_col="Average", std_col="StdDev", n_col="n")
        assert list(summary_df.columns) == original_cols

    def test_ci_zero_when_n_is_1(self, summary_df):
        result = StatsHelper.add_ci(summary_df, mean_col="Average", std_col="StdDev", n_col="n")
        ci_for_c = result.loc[result["Group"] == "Z", "CI_95"].iloc[0]
        assert ci_for_c == 0.0

    def test_ci_positive_when_n_gte_2(self, summary_df):
        result = StatsHelper.add_ci(summary_df, mean_col="Average", std_col="StdDev", n_col="n")
        ci_for_a = result.loc[result["Group"] == "X", "CI_95"].iloc[0]
        assert ci_for_a > 0.0


# ---------------------------------------------------------------------------
# add_custom_group
# ---------------------------------------------------------------------------

class TestAddCustomGroup:
    def test_appends_one_row(self, summary_df):
        # add_custom_group appends to an existing summary df but pulls raw
        # values via the mask — so the summary_df must contain value_col too.
        # Use a summary that already has the aggregated "Average" column as
        # the value_col, and a mask into that same frame.
        mask = summary_df["Group"].isin(["X", "Y"])
        result = StatsHelper.add_custom_group(
            summary_df,
            group_col="Group",
            group_label="A+B",
            mask=mask,
            value_col="Average",
        )
        assert len(result) == len(summary_df) + 1

    def test_new_row_has_correct_label(self, summary_df):
        mask = summary_df["Group"] == "X"
        result = StatsHelper.add_custom_group(
            summary_df,
            group_col="Group",
            group_label="CustomA",
            mask=mask,
            value_col="Average",
        )
        assert "CustomA" in result["Group"].values


# ---------------------------------------------------------------------------
# subtraction_row / addition_row
# ---------------------------------------------------------------------------

class TestRowMutators:
    def test_subtraction_row_appended(self, summary_df):
        mask_a = summary_df["Group"] == "X"
        mask_b = summary_df["Group"] == "Y"
        result = StatsHelper.subtraction_row(
            summary_df,
            row_a_mask=mask_a,
            row_b_mask=mask_b,
            label_col="Group",
            result_label="Δ A-B",
        )
        assert len(result) == len(summary_df) + 1
        assert "Δ A-B" in result["Group"].values

    def test_subtraction_values_correct(self, summary_df):
        mask_a = summary_df["Group"] == "X"
        mask_b = summary_df["Group"] == "Y"
        result = StatsHelper.subtraction_row(
            summary_df,
            row_a_mask=mask_a,
            row_b_mask=mask_b,
            label_col="Group",
            result_label="Δ A-B",
            numeric_cols=["Average"],
        )
        diff_row = result.loc[result["Group"] == "Δ A-B", "Average"].iloc[0]
        assert diff_row == pytest.approx(20.0 - 45.0, abs=0.01)

    def test_addition_row_appended(self, summary_df):
        masks = [summary_df["Group"] == "X", summary_df["Group"] == "Y"]
        result = StatsHelper.addition_row(
            summary_df,
            row_masks=masks,
            label_col="Group",
            result_label="A+B",
        )
        assert len(result) == len(summary_df) + 1
        assert "A+B" in result["Group"].values

    def test_addition_values_correct(self, summary_df):
        masks = [summary_df["Group"] == "X", summary_df["Group"] == "Y"]
        result = StatsHelper.addition_row(
            summary_df,
            row_masks=masks,
            label_col="Group",
            result_label="A+B",
            numeric_cols=["Average"],
        )
        sum_row = result.loc[result["Group"] == "A+B", "Average"].iloc[0]
        assert sum_row == pytest.approx(20.0 + 45.0, abs=0.01)

    def test_lambda_row_appended(self, summary_df):
        result = StatsHelper.lambda_row(
            summary_df,
            fn=lambda d: {"Average": d["Average"].mean()},
            label_col="Group",
            result_label="Global Mean",
        )
        assert len(result) == len(summary_df) + 1
        assert "Global Mean" in result["Group"].values


# ---------------------------------------------------------------------------
# pearson_r
# ---------------------------------------------------------------------------

class TestPearsonR:
    def test_returns_four_values(self):
        x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y = np.array([2.0, 4.0, 6.0, 8.0, 10.0])
        out = StatsHelper.pearson_r(x, y)
        assert len(out) == 4

    def test_perfect_positive_correlation(self):
        x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y = np.array([2.0, 4.0, 6.0, 8.0, 10.0])
        _, _, r, p = StatsHelper.pearson_r(x, y)
        assert r == pytest.approx(1.0, abs=1e-6)
        assert p == pytest.approx(0.0, abs=1e-6)

    def test_nan_when_fewer_than_3_pairs(self):
        x = np.array([1.0, 2.0])
        y = np.array([1.0, 2.0])
        _, _, r, p = StatsHelper.pearson_r(x, y)
        assert math.isnan(r)
        assert math.isnan(p)

    def test_drops_nan_values(self):
        x = np.array([1.0, np.nan, 3.0, 4.0, 5.0])
        y = np.array([2.0, 4.0,   6.0, 8.0, 10.0])
        x_clean, y_clean, _, _ = StatsHelper.pearson_r(x, y)
        assert len(x_clean) == len(y_clean)
        assert not any(np.isnan(x_clean))

    def test_drops_inf_values(self):
        x = np.array([1.0, np.inf, 3.0, 4.0, 5.0])
        y = np.array([2.0, 4.0,    6.0, 8.0, 10.0])
        x_clean, _, _, _ = StatsHelper.pearson_r(x, y)
        assert not any(np.isinf(x_clean))


# ---------------------------------------------------------------------------
# scatter_stats
# ---------------------------------------------------------------------------

class TestScatterStats:
    def test_returns_dict_with_label(self, ward_df):
        result = StatsHelper.scatter_stats(
            ward_df, x_col="Metric", y_cols=["Error"], label="Group X"
        )
        assert result["label"] == "Group X"

    def test_contains_y_col_key(self, ward_df):
        result = StatsHelper.scatter_stats(
            ward_df, x_col="Metric", y_cols=["Error"], label="Test"
        )
        assert "Error" in result

    def test_scatter_info_fields(self, ward_df):
        result = StatsHelper.scatter_stats(
            ward_df, x_col="Metric", y_cols=["Error"], label="Test"
        )
        info = result["Error"]
        for key in ("x", "y", "r", "p", "slope", "intercept", "loess_x", "loess_y", "n", "ids", "timepoints"):
            assert key in info, f"Missing key '{key}' in ScatterInfo"

    def test_n_matches_dataframe_length(self, ward_df):
        result = StatsHelper.scatter_stats(
            ward_df, x_col="Metric", y_cols=["Error"], label="Test"
        )
        assert result["Error"]["n"] == len(ward_df)
