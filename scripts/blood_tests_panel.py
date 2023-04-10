from bokeh.models import Tab, Panel, DataTable
from bokeh.models import ColumnDataSource
from scripts.data import filter_data
from .analysis_panel import AnalysisPanel

class BloodTestPanel(AnalysisPanel):

      def __init__(self,data,categories,metadata,title):
          AnalysisPanel.__init__(self,data,categories,metadata,title)
          for view in self.raw_data.keys():
              self.data_sources[view] = ColumnDataSource(self.raw_data[view])

              colums = []
              for cn in list(self.raw_data[view].columns.values):
                  

                  colums.append(TableColumn(field=cn))

              self.plots.append(DataTable(source=self.data_sources[view], columns=,sizing_mode="stretch_both",height=700))
  
       def compose_plots(self):
           return Tab([Panel(dt) for dt in self.plots])

       def compose_widets(self):
           return False

