import numpy
import pandas as pd

def enrich_data(df,categories,metadata):
	"""
	Enrich data in DataFrame *df* with new computed columns
	"""
	for col in ['Units', 'Enum order', 'Enum index start']:
		if col not in metadata.columns:
			metadata[col] = numpy.nan

	# Add days of a week as number 0-6 (Mon - Sun)
	df["Week day"] = df.index.dayofweek 
	categories["Measurements"].append("Week day")
	metadata.loc["Week day"]  = {'Category' : 'Measurements','Default' : 0, 'Intervention' : 'Intervention', 'Start of valid records' : pd.to_datetime('16-2-2021'), 'Units' : 'enum', 'Enum order' : 'Monday;Tuesday;Wednesday;Thursday;Friday;Saturday;Sunday', 'Enum index start' : 0}

	# Add boolean if its weekend of non-weekend day
	df['Weekend'] = df['Week day'].apply(lambda x: 1 if x >= 5 else 0)
	categories["Measurements"].append("Weekend")
	metadata.loc["Weekend"]  = {'Category' : 'Measurements','Default' : 0, 'Intervention' : 'Intervention', 'Start of valid records' : pd.to_datetime('16-2-2021'), 'Units' : 'enum', 'Enum order' : 'Weekday;Weekend', 'Enum index start' : 0}

	# Add month of a year as number 1-12 (Jan - Dec)
	df["Month"] = df.index.month 
	categories["Measurements"].append("Month")
	metadata.loc["Month"]  = {'Category' : 'Measurements','Default' : 0, 'Intervention' : 'Intervention', 'Start of valid records' : pd.to_datetime('16-2-2021'), 'Units' : 'enum', 'Enum order' : 'January;February;March;April;May;June;July;August;September;October;November;December', 'Enum index start' : 1}
