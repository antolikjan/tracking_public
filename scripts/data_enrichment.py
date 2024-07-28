import numpy
import pandas as pd

def enrich_data(df,categories,metadata):
	"""
	Enrich data in DataFrame *df* with new computed columns
	"""

	# Add days of a week as number 0-6 (Mon - Sun)
	df["Week day"] = df.index.dayofweek 
	categories["Measurements"].append("Week day")
	metadata.loc["Week day"]  = {'Category' : 'Measurements','Default' : 0, 'Intervention' : 'Intervention', 'Start of valid records' : pd.to_datetime('16-2-2021')}

	# Add boolean if its weekend of non-weekend day
	df['Weekend'] = df['Week day'].apply(lambda x: 1 if x >= 5 else 0)
	categories["Measurements"].append("Weekend")
	metadata.loc["Weekend"]  = {'Category' : 'Measurements','Default' : 0, 'Intervention' : 'Intervention', 'Start of valid records' : pd.to_datetime('16-2-2021')}
