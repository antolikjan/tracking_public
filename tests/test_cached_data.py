from pathlib import Path

import pandas as pd
import pytest
from bokeh.models import Tabs

import scripts.data as data
from scripts.create_app import create_app
from scripts.relationship_metadata import RelationshipMetadata


ROOT = Path(__file__).resolve().parents[1]
CACHE_FILE = ROOT / "locals" / "cache.pickle"
BLOOD_TEST_CACHE_FILE = ROOT / "locals" / "cache_bt.pickle"
RELATIONSHIP_METADATA_FILE = ROOT / "relationship_metadata"


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


def test_cached_tracking_data_loads(table_names):
    require_cache_files(CACHE_FILE)

    df, metadata, categories = data.load_tables(
        table_names,
        api_key="unused",
        base_id="unused",
        cache=True,
    )

    assert isinstance(df, pd.DataFrame)
    assert isinstance(metadata, pd.DataFrame)
    assert len(df) > 0
    assert len(metadata) > 0
    assert categories


def test_cached_blood_tests_load():
    require_cache_files(BLOOD_TEST_CACHE_FILE)

    blood_tests = data.load_blood_tests(
        api_key="unused",
        base_id="unused",
        cache=True,
    )

    assert isinstance(blood_tests, dict)
    assert blood_tests
    assert all(isinstance(table, pd.DataFrame) for table in blood_tests.values())


def test_app_constructs_from_cached_data(table_names, monkeypatch):
    require_cache_files(CACHE_FILE, BLOOD_TEST_CACHE_FILE, RELATIONSHIP_METADATA_FILE)

    df, metadata, categories = data.load_tables(
        table_names,
        api_key="unused",
        base_id="unused",
        cache=True,
    )
    blood_tests = data.load_blood_tests(
        api_key="unused",
        base_id="unused",
        cache=True,
    )

    monkeypatch.setattr(RelationshipMetadata, "save", lambda self: None)
    relationships = RelationshipMetadata(metadata, initialize=False)

    app = create_app(df, metadata, categories, relationships, blood_tests)

    assert isinstance(app, Tabs)
    assert len(app.tabs) > 0
