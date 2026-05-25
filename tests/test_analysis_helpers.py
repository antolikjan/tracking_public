import numpy as np
import pandas as pd
import scipy.stats

from scripts.data import (
    both_valid,
    convert_to_dataframe,
    cross_corr,
    data_aquisition_overlap,
    data_aquisition_overlap_non_nans,
    event_triggered_change,
    event_weighted_average,
    filter_data,
    special_preprocessing_rules,
)
from scripts.data_enrichment import enrich_data
from scripts.correlations import pairwise_regression_stats, past_gauss_filter_matrix


def test_both_valid_removes_pairwise_nans_and_preserves_order():
    data1 = np.array([1.0, np.nan, 3.0, 4.0, np.nan])
    data2 = np.array([10.0, 20.0, np.nan, 40.0, 50.0])

    valid1, valid2 = both_valid(data1, data2)

    np.testing.assert_array_equal(valid1, np.array([1.0, 4.0]))
    np.testing.assert_array_equal(valid2, np.array([10.0, 40.0]))


def test_data_aquisition_overlap_returns_common_observation_span():
    data1 = np.array([np.nan, 1.0, 2.0, np.nan, 4.0, np.nan])
    data2 = np.array([np.nan, np.nan, 20.0, 30.0, 40.0, np.nan])

    assert data_aquisition_overlap(data1, data2) == (2, 4)


def test_data_aquisition_overlap_returns_zero_span_when_either_side_is_all_nan():
    valid = np.array([np.nan, 1.0, 2.0])
    empty = np.array([np.nan, np.nan, np.nan])

    assert data_aquisition_overlap(valid, empty) == (0, 0)
    assert data_aquisition_overlap(empty, valid) == (0, 0)


def test_data_aquisition_overlap_non_nans_uses_current_slice_stop_behavior():
    data1 = np.array([np.nan, 1.0, np.nan, 3.0, 4.0, np.nan])
    data2 = np.array([np.nan, np.nan, 2.0, 30.0, 40.0, np.nan])

    valid1, valid2 = data_aquisition_overlap_non_nans(data1, data2)

    np.testing.assert_array_equal(valid1, np.array([3.0]))
    np.testing.assert_array_equal(valid2, np.array([30.0]))


def test_filter_data_gauss_ignores_nans_in_weighted_average():
    data = np.array([1.0, np.nan, 3.0])

    kernel, result = filter_data("Gauss", data, sig=1)

    expected_kernel = np.exp(-np.power(np.array([0, 1, 2]) - 1, 2.0) / 2)
    first_weights = np.exp(-np.power(np.array([0, 2]) - 0, 2.0) / 2)
    expected_first = np.average(
        np.array([1.0, 3.0]),
        weights=first_weights,
    )
    np.testing.assert_allclose(kernel, expected_kernel)
    np.testing.assert_allclose(result[0], expected_first)
    assert result.shape == data.shape


def test_filter_data_past_and_future_gauss_use_asymmetric_windows():
    data = np.array([1.0, 2.0, 4.0])

    past_kernel, past_result = filter_data("PastGauss", data, sig=1)
    future_kernel, future_result = filter_data("FutureGauss", data, sig=1)

    np.testing.assert_allclose(past_kernel, np.array([np.exp(-0.5), 1.0, 0.0]))
    np.testing.assert_allclose(future_kernel, np.array([0.0, 1.0, np.exp(-0.5)]))
    np.testing.assert_allclose(past_result[0], data[0])
    np.testing.assert_allclose(future_result[-1], data[-1])


def test_fast_past_gauss_matrix_matches_filter_data_for_2d_arrays():
    data = np.array(
        [
            [1.0, np.nan],
            [np.nan, 2.0],
            [3.0, 4.0],
            [4.0, np.nan],
            [np.nan, 7.0],
        ]
    )

    _, expected = filter_data("PastGauss", data, sig=1)

    np.testing.assert_allclose(
        past_gauss_filter_matrix(data, sig=1),
        expected,
        equal_nan=True,
    )


def test_pairwise_regression_stats_matches_linregress_overlap_behavior():
    data = np.array(
        [
            [np.nan, np.nan, 5.0],
            [1.0, np.nan, 4.0],
            [2.0, 2.0, np.nan],
            [3.0, 4.0, 2.0],
            [4.0, 6.0, 1.0],
            [np.nan, 8.0, np.nan],
        ]
    )

    r, pvalue = pairwise_regression_stats(data, data, min_count=1, var_tol=0.0)
    expected = scipy.stats.linregress(np.array([2.0, 3.0]), np.array([2.0, 4.0]))

    np.testing.assert_allclose(r[0, 1], expected.rvalue)
    np.testing.assert_allclose(pvalue[0, 1], expected.pvalue)


def test_cross_corr_returns_none_without_positive_overlap():
    data1 = np.array([1.0, np.nan, np.nan])
    data2 = np.array([np.nan, np.nan, 2.0])

    assert cross_corr(data1, data2, data1, data2) is None


def test_cross_corr_shortens_even_overlap_to_symmetric_odd_lag_axis():
    data1 = np.array([np.nan, 1.0, 2.0, 3.0, 4.0, np.nan])
    data2 = np.array([np.nan, 4.0, 3.0, 2.0, 1.0, np.nan])

    corr, lags = cross_corr(data1, data2, data1, data2)

    np.testing.assert_array_equal(lags, np.array([-1, 0, 1]))
    assert len(corr) == 3
    assert corr[1] < 0


def test_event_weighted_average_ignores_response_nans_and_normalizes_by_event_mean():
    events = np.array([np.nan, 2.0, np.nan])
    response = np.array([1.0, np.nan, 3.0])

    result = event_weighted_average(events, response)

    np.testing.assert_allclose(result, np.array([1.0, np.nan, 3.0]))


def test_event_triggered_change_returns_before_after_pairs_and_wilcoxon_result():
    events = np.array([0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0])
    response = np.array([1.0, 2.0, 5.0, 6.0, 2.0, 3.0, 7.0, 8.0])

    pairs, stat, pvalue = event_triggered_change(events, response, w=2, default=0)

    assert pairs == [(1.5, 5.5), (4.0, 5.0)]
    assert np.isfinite(stat)
    assert np.isfinite(pvalue)


def test_convert_to_dataframe_uses_record_id_index_by_default():
    records = [
        {"id": "rec1", "fields": {"A": 1}},
        {"id": "rec2", "fields": {"A": 2}},
    ]

    df = convert_to_dataframe(records)

    assert list(df.index) == ["rec1", "rec2"]
    assert list(df["A"]) == [1, 2]


def test_convert_to_dataframe_can_use_datetime_index_column():
    records = [
        {"id": "rec1", "fields": {"Date": "2024-01-01", "A": 1}},
        {"id": "rec2", "fields": {"Date": "2024-01-02", "A": 2}},
    ]

    df = convert_to_dataframe(records, index_column="Date", datatime_index=True)

    assert isinstance(df.index, pd.DatetimeIndex)
    assert list(df.index) == [pd.Timestamp("2024-01-01"), pd.Timestamp("2024-01-02")]
    assert "Date" not in df.columns
    assert list(df["A"]) == [1, 2]


def test_enrich_data_adds_calendar_columns_categories_and_metadata_rows():
    df = pd.DataFrame(index=pd.to_datetime(["2024-01-05", "2024-01-06"]))
    categories = {"Measurements": ["Existing"]}
    metadata = pd.DataFrame(
        columns=["Category", "Default", "Intervention", "Start of valid records"],
        index=["Existing"],
    )

    enrich_data(df, categories, metadata)

    assert list(df["Week day"]) == [4, 5]
    assert list(df["Weekend"]) == [0, 1]
    assert list(df["Month"]) == [1, 1]
    assert categories["Measurements"] == ["Existing", "Week day", "Weekend", "Month"]
    assert metadata.loc["Week day", "Category"] == "Measurements"
    assert metadata.loc["Week day", "Units"] == "enum"
    assert metadata.loc["Week day", "Enum index start"] == 0
    assert metadata.loc["Weekend", "Default"] == 0
    assert metadata.loc["Weekend", "Enum order"] == "Weekday;Weekend"
    assert metadata.loc["Month", "Intervention"] == "Intervention"
    assert metadata.loc["Month", "Enum order"].startswith("January;February")


def test_special_preprocessing_rules_invalidates_fitbit_values_when_steps_are_low():
    df = pd.DataFrame(
        {
            "Steps": [499.0, 500.0],
            "Heart Rate": [70.0, 72.0],
            "Mood": [3.0, 4.0],
        }
    )
    metadata = pd.DataFrame(
        {
            "Category": {
                "Steps": "Fitbit",
                "Heart Rate": "Fitbit",
                "Mood": "Symptoms",
            }
        }
    )

    special_preprocessing_rules(df, metadata)

    assert np.isnan(df.loc[0, "Steps"])
    assert np.isnan(df.loc[0, "Heart Rate"])
    assert df.loc[0, "Mood"] == 3.0
    assert df.loc[1, "Steps"] == 500.0
    assert df.loc[1, "Heart Rate"] == 72.0
