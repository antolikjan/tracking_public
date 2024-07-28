from bokeh.models import Tabs
import scripts.comparison, scripts.correlations, scripts.relationships, scripts.event_based, scripts.bloodtests_correlations
import scripts.blood_tests

from bokeh.models import Panel

def create_app(df,metadata,categories,relationships, bldt):
	global tabs

	cp = scripts.comparison.ComparisonPanel(df,categories,metadata,'Comparison')
	eba = scripts.event_based.EventBasedAnalysisPanel(df,categories,metadata,'Event Based Analysis')
	blt = scripts.blood_tests.BloodTests(bldt, categories, metadata, 'BloodTests')
#	crl_bt = scripts.bloodtests_correlations.BloodTestsCorrelationsPanel(df, bldt, categories, metadata, 'BloodTests Correlations')

	tabs = Tabs(tabs=[
		cp.compose_panel(),
		eba.compose_panel(),
		scripts.correlations.panel(df,categories,metadata,relationships,cp),
		scripts.relationships.panel(relationships), 
		blt.compose_panel(),
#		crl_bt.compose_panel()
		])
	return tabs
