from pathlib import Path

import pandas as pd
import pytest
from bokeh.models import Button, ColumnDataSource, DataTable, Select, TabPanel, Tabs

import scripts.correlations as correlations
import scripts.data as data
import scripts.relationships as relationships_view
from scripts.blood_tests import BloodTests
from scripts.bloodtests_correlations import BloodTestsCorrelationsPanel
from scripts.comparison import ComparisonPanel
from scripts.create_app import create_app
from scripts.event_based import EventBasedAnalysisPanel
from scripts.relationship_metadata import RelationshipMetadata
from scripts.ui_framework.analysis_panel import AnalysisPanel


ROOT = Path(__file__).resolve().parents[1]
CACHE_FILE = ROOT / "locals" / "cache.pickle"
BLOOD_TEST_CACHE_FILE = ROOT / "locals" / "cache_bt.pickle"
RELATIONSHIP_METADATA_FILE = ROOT / "relationship_metadata"


class RelationshipRecorder:
    def __init__(self):
        self.rm = pd.DataFrame(
            {
                "Var1": ["A", "B", "C"],
                "Var2": ["B", "C", "D"],
                "IgnoreList": [True, False, True],
                "BlackList": [False, True, True],
            }
        )
        self.ignorelist_removed = []
        self.blacklist_removed = []

    def remove_from_ignorelist(self, name1, name2):
        self.ignorelist_removed.append((name1, name2))

    def remove_from_blacklist(self, name1, name2):
        self.blacklist_removed.append((name1, name2))

    def is_on_ignore_list(self, pairs):
        return [tuple(pair) in {("A", "B"), ("C", "D")} for pair in pairs]

    def is_on_black_list(self, pairs):
        return [tuple(pair) in {("B", "C"), ("C", "D")} for pair in pairs]


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


@pytest.fixture
def cached_relationships(cached_tracking_data, monkeypatch):
    require_cache_files(RELATIONSHIP_METADATA_FILE)
    _, metadata, _ = cached_tracking_data
    monkeypatch.setattr(RelationshipMetadata, "save", lambda self: None)
    return RelationshipMetadata(metadata, initialize=False)


def assert_panel(panel, title):
    assert isinstance(panel, TabPanel)
    assert panel.title == title
    assert panel.child is not None


def test_analysis_panel_register_widget_tracks_widget_and_callback():
    panel = AnalysisPanel(data=None, categories={}, metadata=None, title="Test")
    widget = Select(title="Category", options=["A"], value="A")

    panel.register_widget(widget, "category", ["value"])

    assert panel.ui_elements["category"] is widget


def test_app_shell_constructs_expected_tabs(
    cached_tracking_data, cached_relationships, cached_blood_tests
):
    df, metadata, categories = cached_tracking_data

    app = create_app(df, metadata, categories, cached_relationships, cached_blood_tests)

    assert isinstance(app, Tabs)
    assert [tab.title for tab in app.tabs] == [
        "Comparison",
        "Event Based Analysis",
        "Correlations",
        "Relationships",
        "BloodTests",
    ]


def test_relationships_panel_constructs(cached_relationships):
    panel = relationships_view.panel(cached_relationships)

    assert_panel(panel, "Relationships")
    controls, data_table = panel.child.children

    assert isinstance(data_table, DataTable)
    assert [column.field for column in data_table.columns] == [
        "Var1",
        "Var2",
        "IgnoreList",
        "BlackList",
    ]
    assert [button.label for button in controls.children] == [
        "Show Ignored",
        "Show Blacklisted",
        "Remove from Ignored",
        "Remove from Blacklist",
    ]
    assert all(isinstance(button, Button) for button in controls.children)


def test_relationship_filters_update_table_source():
    relationships = RelationshipRecorder()
    source = ColumnDataSource(relationships.rm)

    relationships_view.filter_ignored(source, relationships)

    assert list(source.data["Var1"]) == ["A", "C"]
    assert list(source.data["Var2"]) == ["B", "D"]

    relationships_view.filter_blacklisted(source, relationships)

    assert list(source.data["Var1"]) == ["B", "C"]
    assert list(source.data["Var2"]) == ["C", "D"]


def test_relationship_remove_actions_use_selected_rows():
    relationships = RelationshipRecorder()
    source = ColumnDataSource(relationships.rm)
    source.selected.indices = [0, 2]

    relationships_view.remove_from_ignorelist(source, relationships)
    relationships_view.remove_from_blacklist(source, relationships)

    assert relationships.ignorelist_removed == [("A", "B"), ("C", "D")]
    assert relationships.blacklist_removed == [("A", "B"), ("C", "D")]


def test_comparison_panel_constructs(cached_tracking_data):
    df, metadata, categories = cached_tracking_data

    panel = ComparisonPanel(df, categories, metadata, "Comparison").compose_panel()

    assert_panel(panel, "Comparison")


def test_comparison_panel_updates_filtered_and_bar_views(cached_tracking_data):
    df, metadata, categories = cached_tracking_data
    comparison_panel = ComparisonPanel(df, categories, metadata, "Comparison")
    comparison_panel.compose_panel()

    comparison_panel.ui_elements["select_filter1"].value = "Gauss"
    comparison_panel.ui_elements["select_filter2"].value = "Gauss"
    comparison_panel.ui_elements["show_stats_button"].active = True
    comparison_panel.ui_elements["show_bars_button"].active = True

    comparison_panel.update("value", None, None)

    assert comparison_panel.plots["time_series"].legend.visible
    assert comparison_panel.plots["filtered_line1"].visible
    assert comparison_panel.plots["filtered_line2"].visible
    assert len(comparison_panel.data_sources["source_corr"].data["x_values"]) > 0


def test_event_based_panel_constructs(cached_tracking_data):
    df, metadata, categories = cached_tracking_data

    panel = EventBasedAnalysisPanel(
        df, categories, metadata, "Event Based Analysis"
    ).compose_panel()

    assert_panel(panel, "Event Based Analysis")


def test_event_based_panel_updates_reference_lines(cached_tracking_data):
    df, metadata, categories = cached_tracking_data
    event_panel = EventBasedAnalysisPanel(
        df, categories, metadata, "Event Based Analysis"
    )
    event_panel.compose_panel()

    half_length = event_panel.data_sources["source_event_triggered_variables"].data[
        "half_length"
    ][0]
    var2_mean = event_panel.data_sources["source_event_triggered_variables"].data[
        "var2_mean"
    ][0]

    assert event_panel.plots["vline"].location == half_length
    assert event_panel.plots["hline"].location == var2_mean


def test_correlations_panel_constructs(cached_tracking_data, cached_relationships):
    df, metadata, categories = cached_tracking_data
    comparison_panel = ComparisonPanel(df, categories, metadata, "Comparison")

    panel = correlations.panel(
        df, categories, metadata, cached_relationships, comparison_panel
    )

    assert_panel(panel, "Correlations")


def test_correlations_panel_exposes_table_and_controls(
    cached_tracking_data, cached_relationships
):
    df, metadata, categories = cached_tracking_data
    comparison_panel = ComparisonPanel(df, categories, metadata, "Comparison")

    panel = correlations.panel(
        df, categories, metadata, cached_relationships, comparison_panel
    )

    controls = panel.child.children[0]
    data_table = correlations.ui["dt"]

    assert isinstance(data_table, DataTable)
    assert [column.field for column in data_table.columns] == [
        "Variable 1",
        "Variable 2",
        "R",
        "p-value",
        "shift",
        "r_no_shift",
        "p_no_shift",
        "r_no_v1_to_v2",
        "p_no_v1_to_v2",
        "r_no_v2_to_v1",
        "p_no_v2_to_v1",
        "Accumulation analysis P",
        "Accumulation analysis R",
        "Accumulation analysis Sigma",
        "Accumulation analysis Dir",
    ]
    assert [button.label for button in controls.children if isinstance(button, Button)] == [
        "Recalculate",
        "Switch to inspection",
        "Add to ignore list",
        "Add to black list",
    ]


def test_correlations_table_filter_updates_source(cached_tracking_data):
    df, metadata, categories = cached_tracking_data
    comparison_panel = ComparisonPanel(df, categories, metadata, "Comparison")
    relationships = RelationshipRecorder()
    panel = correlations.panel(df, categories, metadata, relationships, comparison_panel)
    source = correlations.ui["dt"].source

    correlations.val1[:] = ["A", "B", "C"]
    correlations.val2[:] = ["B", "C", "D"]
    correlations.rs[:] = [0.5, 0.7, 0.9]
    correlations.pvals[:] = [0.001, 0.2, 0.01]
    correlations.shift[:] = ["==", "Var1 -> Var2", "Var2 -> Var1"]
    correlations.rs_v1_pr_v2[:] = [0.4, 0.6, 0.8]
    correlations.rs_v2_pr_v1[:] = [0.3, 0.5, 0.7]
    correlations.rs_nosh[:] = [0.2, 0.4, 0.6]
    correlations.pvals_v1_pr_v2[:] = [0.002, 0.3, 0.02]
    correlations.pvals_v2_pr_v1[:] = [0.003, 0.4, 0.03]
    correlations.pvals_nosh[:] = [0.004, 0.5, 0.04]
    correlations.acc_p[:] = [0.005, 0.6, 0.05]
    correlations.acc_r[:] = [0.1, 0.2, 0.3]
    correlations.acc_sigma[:] = [2, 4, 8]
    correlations.acc_dir[:] = ["Var1 -> Var2", "Var2 -> Var1", "Var1 -> Var2"]

    correlations.ui["hide_list_choice"].active = 0
    correlations.ui["show_which"].active = 0
    correlations.ui["max_p"].value = 0.05

    correlations.set_table(None, None, None, source, relationships)

    assert_panel(panel, "Correlations")
    assert list(source.data["Variable 1"]) == ["A", "C"]
    assert list(source.data["Variable 2"]) == ["B", "D"]
    assert list(source.data["p-value"]) == [0.001, 0.01]


def test_blood_tests_panel_constructs(cached_blood_tests, cached_tracking_data):
    _, metadata, categories = cached_tracking_data

    panel = BloodTests(
        cached_blood_tests, categories, metadata, "BloodTests"
    ).compose_panel()

    assert_panel(panel, "BloodTests")


def test_blood_tests_panel_updates_selected_view(cached_blood_tests, cached_tracking_data):
    _, metadata, categories = cached_tracking_data
    blood_tests_panel = BloodTests(
        cached_blood_tests, categories, metadata, "BloodTests"
    )
    blood_tests_panel.compose_panel()

    selected_view = next(
        view for view in cached_blood_tests.keys() if view != blood_tests_panel.table
    )
    blood_tests_panel.ui_elements["views"].value = selected_view

    blood_tests_panel.update("value", None, selected_view)

    data_table = blood_tests_panel.plot_layout.children[0]
    assert isinstance(data_table, DataTable)
    assert blood_tests_panel.table == selected_view
    assert data_table.source is blood_tests_panel.data_sources[selected_view]
    assert set(cached_blood_tests[selected_view].columns).issubset(data_table.source.data)


def test_blood_tests_correlations_panel_constructs(
    cached_blood_tests, cached_tracking_data
):
    df, metadata, categories = cached_tracking_data

    panel = BloodTestsCorrelationsPanel(
        df, cached_blood_tests, categories, metadata, "BloodTests Correlations"
    ).compose_panel()

    assert_panel(panel, "BloodTests Correlations")


def test_blood_tests_correlations_panel_updates_sources(
    cached_blood_tests, cached_tracking_data
):
    df, metadata, categories = cached_tracking_data
    panel = BloodTestsCorrelationsPanel(
        df, cached_blood_tests, categories, metadata, "BloodTests Correlations"
    )
    panel.compose_panel()

    assert len(panel.data_sources["raw_data"].data["x_values"]) > 0
    assert len(panel.data_sources["source_corr"].data["x_values"]) > 0
    assert panel.ui_elements["select_variable2"].value in cached_blood_tests[
        panel.ui_elements["select_view"].value
    ].columns
