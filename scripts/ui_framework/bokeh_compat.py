try:
    from bokeh.models import TabPanel as BokehTabPanel
except ImportError:
    from bokeh.models import Panel as BokehTabPanel


def tab_panel(child, title):
    return BokehTabPanel(child=child, title=title)
