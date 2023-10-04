from bokeh.models import Column, Row, Range1d, Div, Spacer, Label, Span, FactorRange, LabelSet
from bokeh.transform import factor_cmap
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource
import numpy, scipy
from scripts.ui_framework.paired_analysis import PairedAnalysis
from scripts.data import event_weighted_average, event_triggered_change



class EventBasedAnalysisPanel(PairedAnalysis):

      def __init__(self,data,categories,metadata,title):
          PairedAnalysis.__init__(self,data,categories,metadata,title)

          self.factors = [   ("1 day", "before"), ("1 day", "after"),
                        ("3 days", "before"), ("3 days", "after"),
                        ("7 days", "before"), ("7 days", "after"),
                        ("31 days", "before"), ("31 days", "after")
                    ]

          # DATA
          self.data_sources['source_event_triggered'] = ColumnDataSource(data={'x_values' : [],'event_triggered' : []})
          self.data_sources['source_event_triggered_variables'] = ColumnDataSource(data={'half_length' : [],'var2_mean' : []})


          self.data_sources['source_event_changed_mean'] = ColumnDataSource(data={'windows' : [],'y' : []})
          self.data_sources['source_event_changed_labels'] = ColumnDataSource(data={'x' : [], 'p-values' : [], 'color' : []})
          self.data_sources['source_event_changed'] = ColumnDataSource(data={'windows_before' : [],'windows_after' : [],'before' : [],'after' : []})
          self.data_sources['source_event_changed_lines'] = ColumnDataSource(data={'x':[],'y':[]})


          # PLOTS
          plot = figure(height=350, width=900,x_axis_type='datetime',sizing_mode="stretch_both")

          plot.line('x_values','event_triggered', source=self.data_sources['source_event_triggered'], line_width=3, line_alpha=0.6)

          vline = Span(location = 0, location_units='data',dimension = 'height', line_color = 'red', line_width = 3,line_alpha=0.2)
          hline = Span(location = 0,  location_units='data', dimension = 'width', line_color = 'red', line_width = 3,line_alpha=0.2)
          vline.level = 'underlay'
          hline.level = 'underlay'

          plot.add_layout(vline)
          plot.add_layout(hline)
          self.plots['eta'] = plot
          self.plots['vline'] = vline
          self.plots['hline'] = vline

          plot = figure(x_range=FactorRange(*self.factors), height=350, width=900,sizing_mode="stretch_both",toolbar_location=None, tools="")

          plot.vbar(x='windows', top='y', width=0.8, source=self.data_sources['source_event_changed_mean'],color='#000000',line_color='white',
                       fill_color=factor_cmap('windows', palette=['#000000',"#E69F01"], factors=['before','after'], start=1, end=2))

          labels = LabelSet(x='x', y=0, text='p-values',text_color='color',
                           source=self.data_sources['source_event_changed_labels'], render_mode='canvas',text_align='center',text_font_style='bold')

          plot.add_layout(labels)

          plot.circle(x='windows_before',y='before',source=self.data_sources['source_event_changed'],radius=0.1,fill_alpha=0)
          plot.circle(x='windows_after',y='after',source=self.data_sources['source_event_changed'],radius=0.1,fill_alpha=0)

          plot.multi_line(xs='x',ys='y',source=self.data_sources['source_event_changed_lines'])
          self.plots['etc'] = plot
          self.plots['labels'] = labels




      def compose_plots(self):
          return Column(self.plots['eta'],self.plots['etc'],sizing_mode="stretch_both")

      def update_data(self):
          super().update_data()

          var1 = self.ui_elements["select_variable1"].value
          var2 = self.ui_elements["select_variable2"].value

          a = self.raw_data[var1].to_numpy()
          b = self.raw_data[var2].to_numpy()

          # EVENT TRIGGERED AVERAGE
          d = event_weighted_average(a,b)
          half_length =  int(numpy.floor(len(a)/2))
          self.data_sources['source_event_triggered'].data = {'x_values' : range(2*half_length+1),'event_triggered' : d}
          self.data_sources['source_event_triggered_variables'].data={'half_length' : [half_length],'var2_mean' : [numpy.nanmean(b)]}

          # EVENT TRIGGERED CHANGE

          res_1, stat_1, pvalue_1 = event_triggered_change(a,b,1)
          res_3, stat_3, pvalue_3 = event_triggered_change(a,b,3)
          res_7, stat_7, pvalue_7 = event_triggered_change(a,b,7)
          res_31, stat_31, pvalue_31 = event_triggered_change(a,b,31)

          self.data_sources['source_event_changed_mean'].data={
                      'windows' : self.factors,
                      'y' : [numpy.nanmean(list(zip(*res_1))[0]),numpy.nanmean(list(zip(*res_1))[1]),
                             numpy.nanmean(list(zip(*res_3))[0]),numpy.nanmean(list(zip(*res_3))[1]),
                             numpy.nanmean(list(zip(*res_7))[0]),numpy.nanmean(list(zip(*res_7))[1]),
                             numpy.nanmean(list(zip(*res_31))[0]),numpy.nanmean(list(zip(*res_31))[1])
                            ],
                    }

          self.data_sources['source_event_changed_labels'].data={
                      'x' : ["1 day","3 days","7 days","31 days"],
                      'p-values' : ["p={:.3f}".format(pvalue_1),"p={:.3f}".format(pvalue_3),"p={:.3f}".format(pvalue_7),"p={:.3f}".format(pvalue_31)],
                      'color' : ["#CC0000" if pvalue_1<0.05 else "#000000", "#CC0000" if pvalue_3<0.05 else "#000000","#CC0000" if pvalue_7<0.05 else "#000000","#CC0000" if pvalue_31<0.05 else "#000000" ]
                
                    }


          self.data_sources['source_event_changed'].data={
                      'windows_before' : [("1 day", "before")]*len(res_1)+ [("3 days", "before")]*len(res_3) +[("7 days", "before")]*len(res_7) +[("31 days", "before")]*len(res_31),
                      'windows_after' : [("1 day", "after")]*len(res_1)+ [("3 days", "after")]*len(res_3) +[("7 days", "after")]*len(res_7)+[("31 days", "after")]*len(res_31),  
                      'before' : numpy.concatenate((list(zip(*res_1))[0],list(zip(*res_3))[0],list(zip(*res_7))[0],list(zip(*res_31))[0])),
                      'after' :  numpy.concatenate((list(zip(*res_1))[1],list(zip(*res_3))[1],list(zip(*res_7))[1],list(zip(*res_31))[1]))
                    }

          self.data_sources['source_event_changed_lines'].data={
                      'x' : [[("1 day", "before"),("1 day", "after")]]*len(res_1)+[[("3 days", "before"),("3 days", "after")]]*len(res_3)+[[("7 days", "before"),("7 days", "after")]]*len(res_7)+[[("31 days", "before"),("31 days", "after")]]*len(res_31),
                      'y' : list(zip(self.data_sources['source_event_changed'].data['before'],self.data_sources['source_event_changed'].data['after']))
                }

      def update_plots(self):
          super().update_plots()

          half_length = self.data_sources['source_event_triggered_variables'].data['half_length'][0]
          var2_mean = self.data_sources['source_event_triggered_variables'].data['var2_mean'][0]
          print(var2_mean)

          self.plots['eta'].yaxis.axis_label = self.ui_elements["select_variable2"].value
          self.plots['eta'].xaxis.ticker = [int(numpy.floor(half_length/2)),half_length,int(numpy.floor(1.5*half_length))]
          self.plots['eta'].xaxis.major_label_overrides = {int(numpy.floor(half_length/2)) : str(-numpy.floor(half_length/2))+' days', half_length : str(0) , int(numpy.floor(1.5*half_length)) : str(numpy.floor(half_length/2)) +' days'}

          self.plots['hline'].location = var2_mean
          self.plots['vline'].location = half_length

          upper_limit = numpy.max([numpy.nanmax(self.data_sources['source_event_changed'].data['before']),numpy.nanmax(self.data_sources['source_event_changed'].data['after'])])
          lower_limit = numpy.min([numpy.nanmin(self.data_sources['source_event_changed'].data['before']),numpy.nanmin(self.data_sources['source_event_changed'].data['after'])])

          self.plots['etc'].x_range.range_padding = 0.5
          self.plots['etc'].y_range.start = 0.9*lower_limit
          self.plots['etc'].y_range.end = upper_limit+(upper_limit-lower_limit)*0.2
          self.plots['labels'].y = upper_limit+(upper_limit-lower_limit)*0.05
