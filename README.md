# Installation instructions
* pip install bokeh==2.4.3 numpy==1.26.4 scipy==1.7.3 pandas==2.2.2 pyairtable
* cd locals
* cp config_example.py config.py
* edit config.py to contain api keys for airtable that contains your data
* run application by: `bokeh serve --show main.py`
