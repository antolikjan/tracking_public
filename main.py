from bokeh.io import curdoc
from scripts.data import load_tables, load_blood_tests
from scripts.create_app import create_app
from scripts.relationship_metadata import RelationshipMetadata
import locals.config as cf

cache=False

blood_tests = load_blood_tests(api_key=cf.config['airtable_api_key'],base_id=cf.config['airtable_base_id'],cache=cache)

df,metadata,categories = load_tables(cf.config['tables_to_load'],api_key=cf.config['airtable_api_key'],base_id=cf.config['airtable_base_id'],cache=cache)

rm = RelationshipMetadata(metadata,initialize=True)

curdoc().add_root(create_app(df,metadata,categories,rm, blood_tests))