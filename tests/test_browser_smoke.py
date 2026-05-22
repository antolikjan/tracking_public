from pathlib import Path
from threading import Thread

import pytest
from bokeh.application import Application
from bokeh.application.handlers import FunctionHandler
from bokeh.server.server import Server
from tornado.ioloop import IOLoop

import scripts.data as data
from scripts.create_app import create_app
from scripts.relationship_metadata import RelationshipMetadata


ROOT = Path(__file__).resolve().parents[1]
CACHE_FILE = ROOT / "locals" / "cache.pickle"
BLOOD_TEST_CACHE_FILE = ROOT / "locals" / "cache_bt.pickle"
RELATIONSHIP_METADATA_FILE = ROOT / "relationship_metadata"
BROWSER_TIMEOUT_MS = 90_000


def require_cache_files(*paths):
    missing = [str(path.relative_to(ROOT)) for path in paths if not path.exists()]
    assert not missing, "Missing local cache file(s): " + ", ".join(missing)


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


def start_cached_bokeh_server(table_names):
    io_loop = IOLoop()

    def build_document(doc):
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

        relationships = RelationshipMetadata(metadata, initialize=False)
        doc.add_root(create_app(df, metadata, categories, relationships, blood_tests))

    server = Server(
        {"/": Application(FunctionHandler(build_document))},
        io_loop=io_loop,
        port=0,
        allow_websocket_origin=["localhost:0"],
    )
    server.start()
    port = server.port

    server._tornado._websocket_origins = {f"localhost:{port}"}

    thread = Thread(target=io_loop.start, daemon=True)
    thread.start()
    return server, io_loop, thread


def stop_bokeh_server(server, io_loop, thread):
    io_loop.add_callback(server.unlisten)
    io_loop.add_callback(io_loop.stop)
    thread.join(timeout=5)


def test_bokeh_app_loads_in_browser(table_names, monkeypatch):
    require_cache_files(CACHE_FILE, BLOOD_TEST_CACHE_FILE, RELATIONSHIP_METADATA_FILE)
    monkeypatch.setattr(RelationshipMetadata, "save", lambda self: None)

    from playwright.sync_api import sync_playwright

    server, io_loop, thread = start_cached_bokeh_server(table_names)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            try:
                page = browser.new_page()
                page.set_default_timeout(BROWSER_TIMEOUT_MS)
                console_errors = []
                page.on(
                    "console",
                    lambda msg: console_errors.append(msg.text)
                    if msg.type == "error"
                    else None,
                )

                page.goto(
                    f"http://localhost:{server.port}/",
                    wait_until="domcontentloaded",
                    timeout=BROWSER_TIMEOUT_MS,
                )
                page.wait_for_function(
                    "() => window.Bokeh && Object.keys(window.Bokeh.index).length > 0"
                )

                expected_tabs = [
                    "Comparison",
                    "Event Based Analysis",
                    "Correlations",
                    "Relationships",
                    "BloodTests",
                ]
                for tab_title in expected_tabs:
                    page.get_by_text(tab_title, exact=True).first.wait_for()

                for tab_title in expected_tabs:
                    page.get_by_text(tab_title, exact=True).first.click()

                assert not console_errors
            finally:
                browser.close()
    finally:
        stop_bokeh_server(server, io_loop, thread)
