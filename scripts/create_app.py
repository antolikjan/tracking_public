from bokeh.models import Tabs
import scripts.comparison, scripts.correlations, scripts.relationships, scripts.event_based
import scripts.blood_tests

from bokeh.models import Panel

def create_app(df,metadata,categories,relationships, bldt):
	global tabs

	cp = scripts.comparison.ComparisonPanel(df,categories,metadata,'Comparison')
	eba = scripts.event_based.EventBasedAnalysisPanel(df,categories,metadata,'Event Based Analysis')
	blt = scripts.blood_tests.BloodTests(bldt, categories, metadata, 'BloodTests')

	tabs = Tabs(tabs=[
		cp.compose_panel(),
		eba.compose_panel(),
		scripts.correlations.panel(df,categories,metadata,relationships,cp),
		scripts.relationships.panel(relationships)
		, blt.compose_panel()
		])
	return tabs
