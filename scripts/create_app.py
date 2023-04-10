from bokeh.models.widgets import Tabs
import scripts.comparison, scripts.correlations, scripts.relationships, scripts.event_based

def create_app(df,metadata,categories,relationships):
	global tabs

	cp = scripts.comparison.ComparisonPanel(df,categories,metadata,'Comparison')
	eba = scripts.event_based.EventBasedAnalysisPanel(df,categories,metadata,'Event Based Analysis')

	tabs = Tabs(tabs=[cp.compose_panel(),eba.compose_panel(),scripts.correlations.panel(df,categories,metadata,relationships,cp),scripts.relationships.panel(relationships)])
	return tabs

