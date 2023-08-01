from bokeh.models import Column, Row, Range1d, Div, Spacer, Label, Slope, RangeTool, Panel, LinearAxis, Toggle, FactorRange, DataRange1d, Whisker, HoverTool
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource
from scripts.data import cross_corr, both_valid, data_aquisition_overlap, data_aquisition_overlap_non_nans
import numpy, scipy
from scripts.ui_framework.paired_analysis import PairedAnalysis
import scipy.stats

class ComparisonPanel(PairedAnalysis):

      def __init__(self,data,categories,metadata,title):
            PairedAnalysis.__init__(self,data,categories,metadata,title)
            self.bar_plot_x_axis_flag = False


            ##### DATA
            self.data_sources['source_corr'] = ColumnDataSource(data={'x_values' : data['RHR'],'y_values' : data['Steps']})
            self.data_sources['source_corr_mean'] = ColumnDataSource(data={'x_values' : [],'y_values' : [], 'sem-' : [], 'sem+' : []})
            self.data_sources['source_cross_corr'] = ColumnDataSource(data={'x_values' : [data['RHR']*0],'cross_corr' : [data['RHR']*0]})
            self.data_sources['source_bar_plot'] = ColumnDataSource(data={'x' : ['1','2','3'] ,'mean' : [4,5,6],'sem-' : [7,8,9],'sem+' : [7,8,9]})
            self.data_sources['source_bar_plot_p_values'] = ColumnDataSource(data={'x' : ['bogus']})

            ##### PLOTS
            range1_start = data['Steps'].min()-0.1*(data['Steps'].max()-data['Steps'].min())
            range1_end = data['Steps'].max()+0.1*(data['Steps'].max()-data['Steps'].min())
            range2_start = data['RHR'].min()-0.1*(data['RHR'].max()-data['RHR'].min())
            range2_end = data['RHR'].max()+0.1*(data['RHR'].max()-data['RHR'].min())

            ##### WIDGETS
            self.register_widget(Toggle(label="Show stats",button_type="success"),'show_stats_button',['active'])

            # FIGURE 1
            p1 = figure(plot_width=300,plot_height=320,sizing_mode="stretch_both",x_axis_type='datetime',y_range=(range1_start,range1_end),x_axis_location="above",tools="xpan",x_range=(data.index[1].timestamp()*1000,data.index[-1].timestamp()*1000))
            p1.extra_y_ranges = {"right" : Range1d(start=range2_start,end=range2_end)}
            p1.add_layout(LinearAxis(y_range_name="right"), 'right')
            self.plots['circles1'] = p1.circle(x='x_values',y='y_values1',source=self.data_sources['raw_data'],size=10,color="navy",alpha=0.5,legend_label='A')
            self.plots['circles2'] = p1.circle(x='x_values',y='y_values2',source=self.data_sources['raw_data'],size=10,color="green",alpha=0.5,y_range_name='right',legend_label='B')
            self.plots['filtered_line1'] = p1.line(x='x_values',y='y_values_post_processed1',source=self.data_sources['raw_data'],color="navy",alpha=1.0,visible=False, width = 2)
            self.plots['filtered_line2'] = p1.line(x='x_values',y='y_values_post_processed2',source=self.data_sources['raw_data'],color="green",alpha=1.0,y_range_name='right',visible=False, width = 2)   
            p1.yaxis[0].major_label_text_color = "navy"
            p1.yaxis[1].major_label_text_color = "green"
            p1.yaxis[0].axis_label = "Steps"
            p1.yaxis[1].axis_label = "RHR"
            p1.toolbar_location = None
            self.plots['time_series'] = p1

            rt = RangeTool(x_range=p1.x_range)
            rt.overlay.fill_color = "navy"
            rt.overlay.fill_alpha = 0.2

            self.register_widget(rt.x_range, 'range_tool_x_range', ['start','end'])
            

            # FIGURE 2
            select = figure(plot_height=40, plot_width=300, y_range=p1.y_range,
                      x_axis_type="datetime", y_axis_type=None,
                      tools="", toolbar_location=None, background_fill_color="#efefef",sizing_mode="stretch_width",x_range=(data.index[1].timestamp()*1000,data.index[-1].timestamp()*1000))
            select.line(x='x_values', y='y_values1', source=self.data_sources['raw_data'],color="black",line_width=2)
            select.ygrid.grid_line_color = None
            select.add_tools(rt)
            select.toolbar.active_multi = rt
            self.plots['select'] = select

            # FIGURE 3
            pf1 = figure(plot_width=300,plot_height=60,sizing_mode="stretch_width",x_axis_type='datetime')
            self.plots['filter_line1'] = pf1.circle(x='x_values',y='filter1',source=self.data_sources['raw_data'],color="navy",alpha=1.0,visible=False)

            pf1.yaxis.ticker=[]
            pf1.toolbar.logo = None
            pf1.toolbar_location = None
            pf1.xaxis.ticker.desired_num_ticks=30
            pf1.xgrid.visible = False
            pf1.xaxis.ticker=[]
            self.plots['filtered_plot1'] = pf1

            # FIGURE 4
            pf2 = figure(plot_width=300,plot_height=60,sizing_mode="stretch_width",x_axis_type='datetime')
            self.plots['filter_line2'] = pf2.circle(x='x_values',y='filter2',source=self.data_sources['raw_data'],color="green",alpha=1.0,visible=False)
            pf2.yaxis.ticker=[]
            pf2.toolbar.logo = None
            pf2.toolbar_location = None
            pf2.xaxis.ticker.desired_num_ticks=30
            pf2.xgrid.visible = False
            pf2.xaxis.ticker=[]
            self.plots['filtered_plot2'] = pf2

            # FIGURE 5
            p3 = figure(plot_width=300,plot_height=300,sizing_mode="stretch_both",title='')
            p3.circle(x='x_values',y='y_values',source=self.data_sources['source_corr'],size=5,color="black",alpha=1.0)
            p3.line(x='x_values',y='y_values',source=self.data_sources['source_corr_mean'],line_width=4,color="black",alpha=0.5)
            p3.varea(x='x_values',y1='sem-',y2='sem+',source=self.data_sources['source_corr_mean'],color="black",alpha=0.1)
            p3.xaxis.axis_label = "Steps"
            p3.yaxis.axis_label = "RHR"
            p3.toolbar_location = None
            p3_slope = Slope(gradient=0, y_intercept=0, line_color='orange', line_dash='dashed', line_width=3.5)
            p3.add_layout(p3_slope) 
            self.plots['correlations'] = p3
            self.plots['correlations_slope'] = p3_slope

            p4 = figure(plot_width=300,plot_height=300,sizing_mode="stretch_both",title='Cross-correlation')
            self.plots['cc_line'] = p4.line(x='x_values',y='cross_corr',source=self.data_sources['source_cross_corr'],color="black",alpha=1.0,visible=False)
            p4.yaxis.axis_label = "corr. coef."
            p4.xaxis.axis_label = "# days"
            p4.toolbar_location = None
            self.plots['cross_correlations'] = p4

            hover = HoverTool(tooltips="<p style='font-weight:bold'>p-value vs. others:</p><div>@pval</div>")
            bp = figure(height=300, width=300,sizing_mode="stretch_both",toolbar_location=None, x_range=FactorRange(*['1','2','3']), tools=[hover])
            bp.vbar(x='x', top='mean', width=0.3, source=self.data_sources['source_bar_plot'])
            bp.add_layout(Whisker(source=self.data_sources['source_bar_plot'], base="x", upper="sem-", lower="sem+", level="overlay"))

            self.plots['bar_plot'] = bp

      def compose_widgets(self):
          w = super().compose_widgets()
          w2 = Column(w,Div(text="""<hr width=240px>"""),self.ui_elements["show_stats_button"],width=240)
          return w2

      def compose_plots(self):
          return Column(self.plots['time_series'],self.plots['select'],Row(Spacer(width=50),self.plots['filtered_plot1'],self.plots['filtered_plot2'],Spacer(width=50),sizing_mode="stretch_width"),Row(self.plots['correlations'],self.plots['bar_plot'],self.plots['cross_correlations'],sizing_mode="stretch_both"),sizing_mode="stretch_both")

      def update_data(self):
          super().update_data()

          selected_range = numpy.logical_and(self.raw_data.index.asi8 >= self.ui_elements['range_tool_x_range'].start*1000000,self.raw_data.index.asi8 <= self.ui_elements['range_tool_x_range'].end*1000000) 
          d1,d2 = both_valid(self.data_sources['raw_data'].data['y_values_post_processed1'][selected_range],self.data_sources['raw_data'].data['y_values_post_processed2'][selected_range])

          self.data_sources['source_corr'].data = {'x_values' : d1 , 'y_values' : d2}

          m, bins, _ = scipy.stats.binned_statistic(d1.tolist(), d2.tolist(), statistic='mean', bins=min(20,len(set(d1))))
          std, bins, _ = scipy.stats.binned_statistic(d1.tolist(), d2.tolist(), statistic='std', bins=min(20,len(set(d1))))
          count, bins, _ = scipy.stats.binned_statistic(d1.tolist(), d2.tolist(), statistic='count', bins=min(20,len(set(d1))))

          sem = std/numpy.sqrt(len(count)-1)
          x = bins[:-1] + (bins[1:] - bins[:-1])/2.0

          self.data_sources['source_corr_mean'].data = {'x_values' : x , 'y_values' : m, 'sem+' : m+sem, 'sem-' : m-sem}

          start, end = data_aquisition_overlap(self.data_sources['raw_data'].data['y_values1'],self.data_sources['raw_data'].data['y_values2'])
          selected_range = numpy.logical_and(self.raw_data.index.asi8[start:end] >= self.ui_elements['range_tool_x_range'].start*1000000,self.raw_data.index.asi8[start:end] <= self.ui_elements['range_tool_x_range'].end*1000000) 
      
          if numpy.all(numpy.logical_not(numpy.isnan(self.data_sources['raw_data'].data['y_values_post_processed1'][start:end][selected_range]))) and numpy.all(numpy.logical_not(numpy.isnan(self.data_sources['raw_data'].data['y_values_post_processed2'][start:end][selected_range]))):

             res = cross_corr(self.data_sources['raw_data'].data['y_values1'][start:end][selected_range],self.data_sources['raw_data'].data['y_values2'][start:end][selected_range],self.data_sources['raw_data'].data['y_values_post_processed1'][start:end][selected_range],self.data_sources['raw_data'].data['y_values_post_processed2'][start:end][selected_range])    

             if res != None:
                 cc,x = res     
                 assert len(x) == len(cc) , "The length of cross correlated values and x point has to be the same. X:(%d) , CC(%d)" % (len(x),len(cc))
                 self.data_sources['source_cross_corr'].data = {'x_values' : x , 'cross_corr' : cc}
                 self.plots['cc_line'].visible=True       
             else:
                 self.plots['cc_line'].visible=False


          # update bar plot data if relevant
          y1,y2 = data_aquisition_overlap_non_nans(self.data_sources['source_corr'].data['x_values'],self.data_sources['source_corr'].data['y_values'])

          if len(set(y1)) < 11 or len(set(y2)) < 11:
             self.bar_plot_flag = True      
             self.bar_plot_x_axis_flag = False
             if len(set(y1)) > len(set(y2)):
                self.bar_plot_x_axis_flag = True
                y1,y2 = y2,y1
             factors= [str(x) for x in sorted(set(y1))]
             mean = numpy.array([numpy.mean(y2[y1==z]) for z in sorted(set(y1))])
             sem =  numpy.array([numpy.std(y2[y1==z], ddof=1) / numpy.sqrt(numpy.size(y2[y1==z])) for z in sorted(set(y1))])    
             # calculate student t-test for each pair of variables
             p_values = []             
             for x in sorted(set(y1)):
                 p = ''
                 for y in sorted(set(y1)):
                        if x != y and len(y2[y1==x]) > 2 and len(y2[y1==y]):
                          a = scipy.stats.ttest_ind(y2[y1==x],y2[y1==y]).pvalue
                          if not numpy.isnan(a):
                            if a > 0.01:
                               p += '<p> <span style="font-weight:bold"> %s </span> : <span style="color:red">%gf</span> </p>' % (y,a)
                            else:
                               p += '<p> <span style="font-weight:bold"> %s </span> : <span style="color:green">%g</span> </p>' % (y,a)
                 p_values.append(p)

             self.data_sources['source_bar_plot'].data = {'x' : factors,'mean' : mean ,'sem-' : mean-sem, 'sem+' : mean+sem,'pval' : p_values}
             self.plots['bar_plot'].x_range.factors = factors

          else:
             self.bar_plot_flag = False

      def update_plots(self):
          super().update_plots()

          if self.bar_plot_flag:
             self.plots['correlations'].visible = False
             self.plots['bar_plot'].visible = True
          else:
             self.plots['correlations'].visible = True
             self.plots['bar_plot'].visible = False

          if numpy.nanmax(self.data_sources['raw_data'].data['y_values2']) != numpy.nanmin(self.data_sources['raw_data'].data['y_values2']):
              self.plots['time_series'].extra_y_ranges['right'].start=numpy.nanmin(self.data_sources['raw_data'].data['y_values2'])-0.1*(numpy.nanmax(self.data_sources['raw_data'].data['y_values2'])-numpy.nanmin(self.data_sources['raw_data'].data['y_values2']))
              self.plots['time_series'].extra_y_ranges['right'].end=numpy.nanmax(self.data_sources['raw_data'].data['y_values2'])+0.1*(numpy.nanmax(self.data_sources['raw_data'].data['y_values2'])-numpy.nanmin(self.data_sources['raw_data'].data['y_values2']))
          else:
              self.plots['time_series'].extra_y_ranges['right'].start = 0.9 * numpy.nanmax(self.data_sources['raw_data'].data['y_values2'])
              self.plots['time_series'].extra_y_ranges['right'].end = 1.1 * numpy.nanmax(self.data_sources['raw_data'].data['y_values2'])

          self.plots['time_series'].yaxis[0].axis_label = self.ui_elements["select_variable1"].value
          self.plots['time_series'].yaxis[1].axis_label = self.ui_elements["select_variable2"].value

          if numpy.nanmax(self.data_sources['raw_data'].data['y_values1']) != numpy.nanmin(self.data_sources['raw_data'].data['y_values1']):    
              self.plots['time_series'].y_range.start=numpy.nanmin(self.data_sources['raw_data'].data['y_values1'])-0.1*(numpy.nanmax(self.data_sources['raw_data'].data['y_values1'])-numpy.nanmin(self.data_sources['raw_data'].data['y_values1']))
              self.plots['time_series'].y_range.end=numpy.nanmax(self.data_sources['raw_data'].data['y_values1'])+0.1*(numpy.nanmax(self.data_sources['raw_data'].data['y_values1'])-numpy.nanmin(self.data_sources['raw_data'].data['y_values1']))     
          else:
              self.plots['time_series'].y_range.start = 0.9 * numpy.nanmax(self.data_sources['raw_data'].data['y_values1'])
              self.plots['time_series'].y_range.end = 1.1 * numpy.nanmax(self.data_sources['raw_data'].data['y_values1'])

          self.plots['correlations'].xaxis.axis_label = self.ui_elements["select_variable1"].value
          self.plots['correlations'].yaxis.axis_label = self.ui_elements["select_variable2"].value

          if not self.bar_plot_x_axis_flag:
            self.plots['bar_plot'].yaxis.axis_label = self.ui_elements["select_variable2"].value
            self.plots['bar_plot'].xaxis.axis_label = self.ui_elements["select_variable1"].value
          else:
            self.plots['bar_plot'].yaxis.axis_label = self.ui_elements["select_variable1"].value
            self.plots['bar_plot'].xaxis.axis_label = self.ui_elements["select_variable2"].value

          self.plots['circles2'].visible = self.ui_elements["select_category2"].value != 'None'

          a = self.data_sources['raw_data'].data['y_values1']
          mean1 = numpy.nanmean(a)
          sem1 = numpy.nanstd(a, ddof=1) / numpy.sqrt(numpy.size(a[~numpy.isnan(a)]))

          a = self.data_sources['raw_data'].data['y_values2']
          mean2 = numpy.nanmean(a)
          sem2 = numpy.nanstd(a, ddof=1) / numpy.sqrt(numpy.size(a[~numpy.isnan(a)]))

          self.plots['time_series'].legend.items[0].label['value']='Mean: ' + "{0:.6g}".format(mean1) + '±' + "{0:.6g}".format(sem1)
          self.plots['time_series'].legend.items[1].label['value']='Mean: ' + "{0:.6g}".format(mean2) + '±' + "{0:.6g}".format(sem2)

          # Forcing legend re-render :-(
          a=self.plots['time_series'].legend.items
          self.plots['time_series'].legend.items=[]
          self.plots['time_series'].legend.items=a


          self.plots['time_series'].legend.visible=self.ui_elements["show_stats_button"].active

          # we will not report correlations if they are not calculated from at least 10 data points
          x,y = data_aquisition_overlap_non_nans(self.data_sources['source_corr'].data['x_values'],self.data_sources['source_corr'].data['y_values'])
          if len(x) > 10:
            res = scipy.stats.linregress(x,y) 
            if not numpy.isnan(res.slope):
              self.plots['correlations_slope'].gradient = res.slope
              self.plots['correlations_slope'].y_intercept = res.intercept
              self.plots['correlations'].title.text = 'R=' +str(res.rvalue) + ';              (p=' + "{0:.6g}".format(res.pvalue) + '; N=' + "{0:.6g}".format(len(self.data_sources['source_corr'].data['x_values'])) + ')'
              self.plots['correlations_slope'].visible = True
            else:
              self.plots['correlations_slope'].visible = False
              self.plots['correlations'].title.text = 'R: N/A      p_value: N/A'

          else:
            self.plots['correlations_slope'].visible = False
            self.plots['correlations'].title.text = 'R: N/A      p_value: N/A'

          ## CROSS-CORR
          if self.ui_elements["select_filter1"].value == 'None':
             self.plots['filtered_line1'].visible=False
             self.plots['filter_line1'].visible=False     
             self.plots['cc_line'].visible=False    
          else:
             self.plots['filtered_line1'].visible=True
             self.plots['filter_line1'].visible=True    

          if self.ui_elements["select_filter2"].value == 'None' or self.ui_elements["select_category2"].value == 'None':
             self.plots['filtered_line2'].visible=False
             self.plots['filter_line2'].visible=False     
             self.plots['cc_line'].visible=False    
          else:
             self.plots['filtered_line2'].visible=True
             self.plots['filter_line2'].visible=True    
