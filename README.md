# Tracking dashboard

Personal Bokeh dashboard for local health-tracking analysis.

## Environment

Use the existing virtual environment:

```bash
source ~/venvs/tracking/bin/activate
```

If activation is inconvenient, run commands through the venv Python directly:

```bash
~/venvs/tracking/bin/python -m pytest
```

## Dependencies

Install the current runtime and test dependencies into the existing venv:

```bash
python -m pip install bokeh==3.9.0 numpy scipy pandas==2.2.2 pyairtable pytest pytest-playwright
python -m playwright install chromium
```

## Local configuration

Create a private local Airtable config:

```bash
cd locals
cp config_example.py config.py
```

Edit `locals/config.py` with the Airtable API key, base ID, and table names for your data. The config file is a private local artifact and is ignored by git.

## Running the app

From the repository root:

```bash
python -m bokeh serve --show main.py
```

Without `--show`, the server can be started for manual validation:

```bash
python -m bokeh serve main.py
```

## Local cache regeneration

The automated tests use local pickle cache files and do not require Airtable credentials. To regenerate the cache manually, configure `locals/config.py` with Airtable credentials, then run the app or call the data loaders with `cache=False`. This refreshes:

- `locals/cache.pickle`
- `locals/cache_bt.pickle`

The cache files contain private health data and are ignored by git.

## Tests

Run the full test suite:

```bash
python -m pytest
```

The browser smoke test uses Playwright Chromium. If Chromium has not been installed in the venv yet, run:

```bash
python -m playwright install chromium
```

Then run either the full suite or just the browser smoke test:

```bash
python -m pytest tests/test_browser_smoke.py -q
```
