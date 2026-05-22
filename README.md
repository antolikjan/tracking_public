# Installation instructions
* pip install bokeh==3.9.0 numpy scipy pandas==2.2.2 pyairtable pytest pytest-playwright
* python -m playwright install chromium
* cd locals
* cp config_example.py config.py
* edit config.py to contain api keys for airtable that contains your data
* run application by: `bokeh serve --show main.py`

# Local cache regeneration

The test suite uses local pickle cache files and does not require Airtable credentials. To regenerate the cache manually, configure `locals/config.py` with Airtable credentials, then run the app or call the data loaders with `cache=False`. This refreshes `locals/cache.pickle` and `locals/cache_bt.pickle`.

The local config and cache files are private local artifacts and are ignored by git.
