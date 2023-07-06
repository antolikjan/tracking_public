from bokeh.io import curdoc
from scripts.data import load_tables, load_blood_tests
from scripts.create_app import create_app
from scripts.relationship_metadata import RelationshipMetadata
import locals.config as cf

cache=False

df,metadata,categories = load_tables(cf.config['tables_to_load'],api_key=cf.config['airtable_api_key'],base_id=cf.config['airtable_base_id'],cache=cache)

rm = RelationshipMetadata(metadata,initialize=False)

curdoc().add_root(create_app(df,metadata,categories,rm))


# view_names = ['WBC Rest','WBC Differential','Immunity','Minerals','Kidney Function','Liver Function','Pancreas','Proteins','Glucose','Lipids','Thyroid','Hormones','Vitamins','Prostate','BiologicalAgeScores','Cardio']
# blt = load_blood_tests(view_names, api_key='keyBQivgbhrgIZQS9', base_id='appL3Wb1C7NvHTDl1', cache=cache)
# blood_tests = load_blood_tests(view_names, api_key='keyBQivgbhrgIZQS9', base_id='appL3Wb1C7NvHTDl1', cache=cache)

#blood_tests = load_blood_tests(['WBC Rest','WBC Differential','Immunity','Minerals','Kidney Function','Liver Function','Pancreas','Proteins','Glucose','Lipids','Thyroid','Hormones','Vitamins','Prostate','BiologicalAgeScores','Cardio'],cache=cache)