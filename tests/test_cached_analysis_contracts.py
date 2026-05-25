from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import scripts.data as data
from scripts.data import (
    cross_corr,
    data_aquisition_overlap,
    data_aquisition_overlap_non_nans,
    event_triggered_change,
    event_weighted_average,
    filter_data,
)
from scripts.relationship_metadata import RelationshipMetadata


ROOT = Path(__file__).resolve().parents[1]
CACHE_FILE = ROOT / "locals" / "cache.pickle"
BLOOD_TEST_CACHE_FILE = ROOT / "locals" / "cache_bt.pickle"
RELATIONSHIP_METADATA_FILE = ROOT / "relationship_metadata"
REQUIRED_METADATA_COLUMNS = {
    "Category",
    "Default",
    "Intervention",
    "Start of valid records",
    "End of valid records",
    "Units",
}


def require_cache_files(*paths):
    missing = [str(path.relative_to(ROOT)) for path in paths if not path.exists()]
    if missing:
        pytest.skip("Missing local cache file(s): " + ", ".join(missing))


@pytest.fixture
def table_names():
    try:
        from locals.config import config
    except ModuleNotFoundError:
        try:
            from locals.config_example import config
        except ModuleNotFoundError:
            pytest.skip("Missing locals/config.py and locals/config_example.py")

    return config["tables_to_load"]


@pytest.fixture(autouse=True)
def fail_on_airtable(monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError("Tests must use local cache data and not call Airtable")

    monkeypatch.setattr(data, "Table", fail)


@pytest.fixture
def cached_tracking_data(table_names):
    require_cache_files(CACHE_FILE)
    return data.load_tables(
        table_names,
        api_key="unused",
        base_id="unused",
        cache=True,
    )


@pytest.fixture
def cached_blood_tests():
    require_cache_files(BLOOD_TEST_CACHE_FILE)
    return data.load_blood_tests(
        api_key="unused",
        base_id="unused",
        cache=True,
    )


def numeric_series(df, min_valid=3, exclude=()):
    for column in df.columns:
        if column in exclude:
            continue
        series = pd.to_numeric(df[column], errors="coerce")
        if series.notna().sum() >= min_valid and series.nunique(dropna=True) > 1:
            return column, series.to_numpy(dtype=float)
    pytest.skip(f"No cached numeric column with at least {min_valid} valid values")


def numeric_pair(df, min_valid=3):
    first_column, first = numeric_series(df, min_valid=min_valid)
    second_column, second = numeric_series(
        df,
        min_valid=min_valid,
        exclude={first_column},
    )
    return (first_column, first), (second_column, second)


def event_series(df, metadata, min_events=1):
    for column in df.columns:
        series = pd.to_numeric(df[column], errors="coerce")
        default = metadata.loc[column, "Default"] if column in metadata.index else 0
        default = 0 if pd.isna(default) else default
        event_count = ((series.notna()) & (series != default)).sum()
        if event_count >= min_events:
            return column, series.to_numpy(dtype=float), default
    pytest.skip(f"No cached event-like column with at least {min_events} events")


def test_cached_daily_dataframe_and_metadata_are_analysis_ready(cached_tracking_data):
    df, metadata, categories = cached_tracking_data

    assert isinstance(df.index, pd.DatetimeIndex)
    assert df.index.is_monotonic_increasing
    assert df.index.notna().all()

    missing_metadata = sorted(set(df.columns) - set(metadata.index))
    assert not missing_metadata, "Dataframe columns missing metadata: " + ", ".join(
        missing_metadata
    )

    missing_metadata_columns = sorted(REQUIRED_METADATA_COLUMNS - set(metadata.columns))
    assert not missing_metadata_columns, "Metadata missing required columns: " + ", ".join(
        missing_metadata_columns
    )

    missing_category_columns = {
        category: sorted(set(columns) - set(df.columns))
        for category, columns in categories.items()
        if set(columns) - set(df.columns)
    }
    assert not missing_category_columns

    non_numeric_columns = [
        column
        for column in df.columns
        if pd.to_numeric(df[column], errors="coerce").isna().all()
    ]
    assert not non_numeric_columns, "Analysis columns are not numeric-consumable: " + ", ".join(
        non_numeric_columns
    )


def test_cached_columns_pass_core_analysis_helpers(cached_tracking_data):
    df, _, _ = cached_tracking_data
    (_, first), (_, second) = numeric_pair(df, min_valid=5)

    _, filtered_first = filter_data("Gauss", first, sig=2)
    _, filtered_second = filter_data("Gauss", second, sig=2)

    assert filtered_first.shape == first.shape
    assert filtered_second.shape == second.shape

    start, end = data_aquisition_overlap(first, second)
    assert 0 <= start <= end <= len(first)

    overlap_first, overlap_second = data_aquisition_overlap_non_nans(first, second)
    assert len(overlap_first) == len(overlap_second)
    assert not np.isnan(overlap_first).any()
    assert not np.isnan(overlap_second).any()

    if end - start < 3:
        pytest.skip("Cached numeric pair does not have enough overlap for cross-correlation")

    result = cross_corr(first, second, filtered_first, filtered_second)
    assert result is not None
    corr, lags = result
    assert len(corr) == len(lags)
    assert np.isfinite(corr).all()


def test_cached_columns_pass_event_analysis_helpers(cached_tracking_data):
    df, metadata, _ = cached_tracking_data
    event_column, events, default = event_series(df, metadata, min_events=1)
    response_column, response = numeric_series(
        df,
        min_valid=5,
        exclude={event_column},
    )

    weighted_average = event_weighted_average(events, response)
    assert weighted_average.shape == events.shape

    valid_change_events = []
    window = 2
    for index, value in enumerate(events):
        if np.isnan(value) or value == default:
            continue
        before = response[index - window : index]
        after = response[index : index + window]
        if np.isfinite(before).any() and np.isfinite(after).any():
            valid_change_events.append(index)

    if not valid_change_events:
        pytest.skip(
            f"Cached event column {event_column!r} and response column {response_column!r} "
            "do not have valid before/after windows"
        )

    pairs, stat, pvalue = event_triggered_change(
        events,
        response,
        w=window,
        default=default,
    )
    assert pairs
    assert np.isfinite(stat)
    assert np.isfinite(pvalue)


def test_cached_blood_tests_are_analysis_ready(cached_blood_tests):
    assert isinstance(cached_blood_tests, dict)
    assert cached_blood_tests
    assert "Minerals" in cached_blood_tests
    assert not cached_blood_tests["Minerals"].empty

    invalid_views = []
    for view_name, table in cached_blood_tests.items():
        assert isinstance(table, pd.DataFrame), f"{view_name!r} is not a dataframe"
        if not isinstance(table.index, pd.DatetimeIndex):
            invalid_views.append(f"{view_name}: non-date index")
        elif not table.index.is_monotonic_increasing:
            invalid_views.append(f"{view_name}: unsorted index")

    assert not invalid_views, "Blood-test cache has invalid views: " + ", ".join(
        invalid_views
    )


def test_cached_relationship_metadata_references_known_variables(
    cached_tracking_data, monkeypatch
):
    require_cache_files(RELATIONSHIP_METADATA_FILE)
    _, metadata, _ = cached_tracking_data
    monkeypatch.setattr(RelationshipMetadata, "save", lambda self: None)

    relationships = RelationshipMetadata(metadata, initialize=False)

    known_variables = set(metadata.index)
    variable1 = set(relationships.rm.index.get_level_values("Variable1"))
    variable2 = set(relationships.rm.index.get_level_values("Variable2"))
    assert variable1 <= known_variables
    assert variable2 <= known_variables

    first_pair = [relationships.rm.index[0]]
    assert len(relationships.is_on_ignore_list(first_pair)) == 1
    assert len(relationships.is_on_black_list(first_pair)) == 1
