import numpy, pandas, scipy

from bokeh.models import ColumnDataSource, Column, Row, Range1d, Div, LinearAxis, RangeTool, Select, Slider, Spacer, Slope
from bokeh.plotting import figure

from scripts.ui_framework.analysis_panel import AnalysisPanel
from scripts.data import data_aquisition_overlap_non_nans


class BloodTestsCorrelationsPanel(AnalysisPanel):
    def __init__(self, data, views, categories, metadata, title):
        AnalysisPanel.__init__(self,data,categories,metadata,title)
        ### WIDGETS
        self.register_widget(Select(title="Category",  options=list(categories.keys()), value = 'Fitbit'),'select_category',['value'])
        self.register_widget(Select(title = 'Name', value = 'DistanceFitbit', options = list(categories['Fitbit'])),'select_variable1',['value'])

        self.register_widget(Select(title="View",  options=list(views.keys()), value = 'WBC Rest'),'select_view',['value'])
        self.register_widget(Select(title = 'Biomarker Name', options = list(views['WBC Rest']), value='Leukocites (G/L)'),'select_variable2',['value'])

        self.register_widget(Slider(start=10, end=300, value=30, step=1, title="Number of days to average variable 1 on"),"select_segmentation",['value'])


        self.views = views
        self.bloodtest_dates = views['WBC Rest'].index

        v1_segmented, v2_filtered,  = self.segment_and_filter_redundant_data('DistanceFitbit', 'WBC Rest', 'Leukocites (G/L)')

        self.new_data = {}
        self.new_data['DistanceFitbit'] = v1_segmented


        self.data_sources['raw_data'] = ColumnDataSource(data={'x_values' : self.bloodtest_dates,'y_values1' : numpy.nan_to_num(self.new_data['DistanceFitbit']["segmented"]),'y_values2' : numpy.nan_to_num(v2_filtered) })
        self.data_sources['source_corr'] = ColumnDataSource(data={'x_values' : numpy.nan_to_num(v2_filtered),'y_values' : numpy.nan_to_num(self.new_data['DistanceFitbit']["segmented"])})
        self.data_sources['source_corr_mean'] = ColumnDataSource(data={'x_values' : [],'y_values' : [], 'sem-' : [], 'sem+' : []})

        # PLOT 1
        range1_start = numpy.nanmin(self.new_data['DistanceFitbit']['segmented']) - 0.1 * (numpy.nanmax(self.new_data['DistanceFitbit']['segmented']) - numpy.nanmin(self.new_data['DistanceFitbit']['segmented']))
        range1_end = numpy.nanmax(self.new_data['DistanceFitbit']['segmented']) + 0.1 * (numpy.nanmax(self.new_data['DistanceFitbit']['segmented']) - numpy.nanmin(self.new_data['DistanceFitbit']['segmented']))
        range2_start = numpy.nanmin(v2_filtered)-0.1*(numpy.nanmax(v2_filtered)-numpy.nanmin(v2_filtered))
        range2_end = numpy.nanmax(v2_filtered)+0.1*(numpy.nanmax(v2_filtered)-numpy.nanmin(v2_filtered))


        p1 = figure(width=300, height=320, sizing_mode="stretch_both", x_axis_type='datetime',
            y_range=(range1_start, range1_end), x_axis_location="above", tools="xpan",
            x_range=(self.new_data['DistanceFitbit'].index[1].timestamp()*1000,
                    self.new_data['DistanceFitbit'].index[-1].timestamp()*1000))

        p1.extra_y_ranges = {"right" : Range1d(start=range2_start,end=range2_end)}
        p1.add_layout(LinearAxis(y_range_name="right"), 'right')
        self.plots['circles1'] = p1.circle(x='x_values',y='y_values1',source=self.data_sources['raw_data'],size=10,color="navy",alpha=0.5,legend_label='A')
        self.plots['circles2'] = p1.circle(x='x_values',y='y_values2',source=self.data_sources['raw_data'],size=10,color="green",alpha=0.5,y_range_name='right',legend_label='B')
        p1.yaxis[0].major_label_text_color = "navy"
        p1.yaxis[1].major_label_text_color = "green"
        p1.yaxis[0].axis_label = "DistanceFitbit"
        p1.yaxis[1].axis_label = "Leukocites (G/L)"
        p1.toolbar_location = None
        self.plots['time_series'] = p1

        rt = RangeTool(x_range=p1.x_range)
        rt.overlay.fill_color = "navy"
        rt.overlay.fill_alpha = 0.2
        self.register_widget(rt.x_range, 'range_tool_x_range', ['start','end'])

        
        # PLOT 2
        p2 = figure(width=300,height=300,sizing_mode="stretch_both",title='')
        p2.circle(x='x_values',y='y_values',source=self.data_sources['source_corr'],size=5,color="black",alpha=1.0)
        p2.line(x='x_values',y='y_values',source=self.data_sources['source_corr_mean'],line_width=4,color="black",alpha=0.5)
        p2.varea(x='x_values',y1='sem-',y2='sem+',source=self.data_sources['source_corr_mean'],color="black",alpha=0.1)
        p2.xaxis.axis_label = "DistanceFitbit"
        p2.yaxis.axis_label = "Leukocites"
        p2.toolbar_location = None
        p2_slope = Slope(gradient=0, y_intercept=0, line_color='orange', line_dash='dashed', line_width=3.5)
        p2.add_layout(p2_slope) 
        self.plots['correlations'] = p2
        self.plots['correlations_slope'] = p2_slope 
            

    def compose_widgets(self):
        spacer1 = Spacer(width = 260, height=90)
        widgets_var1 = Column(Div(text="""<b>Variable 1</b>"""), self.ui_elements["select_category"], self.ui_elements["select_variable1"], sizing_mode="fixed", width=120, height=500)
        widgets_var2 = Column(Div(text="""<b>Variable 2</b>"""), self.ui_elements["select_view"], self.ui_elements["select_variable2"], sizing_mode="fixed", width=120, height=500)
        spacer2 = Spacer(width=20, height=40)
        widgets_var3 = Column(Div(text="""<b>Segmentation Range</b>"""), self.ui_elements["select_segmentation"], sizing_mode="fixed", width=260, height=500)
        spacer3 = Spacer(width=40, height=70)
        horiz_spacer = Spacer(width = 20)

        layout_top = Row(horiz_spacer, widgets_var1, spacer2, widgets_var2, width=480)
        layout_bottom = Row(horiz_spacer, widgets_var3)

        layout = Column(spacer1, layout_top, spacer3, layout_bottom)
        
        return layout
    


    def compose_plots(self):
        vertical_spacer = Spacer(width = 260, height=10)
        horiz_spacer = Spacer(width = 40)
        return Row(Column(vertical_spacer, Row(horiz_spacer, self.plots['time_series'], width=1200), Row(horiz_spacer, self.plots["correlations"], width=1150), sizing_mode='stretch_both'))



    def segment_and_filter_redundant_data(self, column_to_align, curr_view, biomarker, segmentation_period=30):

        segmented = []
        v2_filtered = self.views[curr_view][biomarker].copy()

        for i in range(len(self.bloodtest_dates)):
            date = self.bloodtest_dates[i]
            biomarker_entry = v2_filtered[i]

            # making sure that we only include dates for which both variables have non-NaN datapoints 
            if pandas.isna(biomarker_entry):
                segmented.append(pandas.NA)

            else:
                segment_start_date = date - pandas.Timedelta(days=segmentation_period)
                segment_end_date = date

                slice_range = (self.raw_data[column_to_align].index >= segment_start_date) & (self.raw_data[column_to_align].index <= segment_end_date)
                slice = self.raw_data[column_to_align][slice_range]

                # adding the slice to the list of segments
                segmented.append(slice)
        

        # calculating averages of the slices of the segmented array
        averages = []
        for j in range(len(segmented)):
            slice_df = segmented[j]
            try:
                slice_averages = slice_df.mean()
            except:     # slice is a (collection of) NaN value(s)
                slice_averages = numpy.nan

            # including only dates for which both variables have non-NaN datapoints 
            if pandas.isna(slice_averages):
                v2_filtered.iloc[j] = pandas.NA

            averages.append(slice_averages)
        
        v1_segmented = pandas.DataFrame(averages, columns=["segmented"], index=self.bloodtest_dates)
        v1_segmented.sort_index(inplace=True)

        

        return v1_segmented, v2_filtered


    def update_widgets(self):

        self.ui_elements["select_variable1"].options = list(self.categories[self.ui_elements["select_category"].value])

        if self.ui_elements["select_view"].value != 'None':
            self.ui_elements["select_variable2"].options = list(self.views[self.ui_elements["select_view"].value])
        else:
            self.ui_elements["select_variable2"].options = ['None']

        if self.ui_elements["select_variable1"].value not in self.categories[self.ui_elements["select_category"].value]:
            self.ui_elements["select_variable1"].value = self.categories[self.ui_elements["select_category"].value][0]

        if self.ui_elements["select_view"].value != 'None':
            if self.ui_elements["select_variable2"].value not in self.views[self.ui_elements["select_view"].value]:
                self.ui_elements["select_variable2"].value = self.views[self.ui_elements["select_view"].value].columns[0]
            
            
    def update_data(self):
        ## Update name of the bloodtest biomarker (var2)
        current_view = self.ui_elements["select_view"].value
        if current_view != None:
            var2_name = self.ui_elements["select_variable2"].value

        ## Update the data of variable 1 and variable 2 
        var1_name = self.ui_elements["select_variable1"].value
        df_var1, var2 = self.segment_and_filter_redundant_data(var1_name, current_view, var2_name, self.ui_elements["select_segmentation"].value)
        var1 = df_var1["segmented"]

        self.data_sources['raw_data'].data['y_values1'] = var1
        self.data_sources['raw_data'].data['y_values2'] = var2


        var1_array = var1.to_numpy().flatten()

        # Check that variables are not all NaN value columns
        if not var1.isna().all() and not var2.isna().all():

            nan_mask = ~numpy.isnan(var1_array) & ~numpy.isnan(var2) # a mask to filter out NaN values
            var1_filtered = var1_array[nan_mask]
            var2_filtered = var2[nan_mask]

            self.data_sources['source_corr'].data = {'x_values' : var1 , 'y_values' : var2}
            m, bins, _ = scipy.stats.binned_statistic(var1_filtered, var2_filtered, statistic='mean', bins=min(20,len(set(var1_filtered))))
            std, bins, _ = scipy.stats.binned_statistic(var1_filtered, var2_filtered, statistic='std', bins=min(20,len(set(var1_filtered))))
            count, bins, _ = scipy.stats.binned_statistic(var1_filtered, var2_filtered, statistic='count', bins=min(20,len(set(var1_filtered))))

            sem = std/numpy.sqrt(len(count)-1)
            x = bins[:-1] + (bins[1:] - bins[:-1])/2.0

            self.data_sources['source_corr_mean'].data = {'x_values' : x , 'y_values' : m, 'sem+' : m+sem, 'sem-' : m-sem}

    def update_plots(self):
        super().update_plots()

        # Check that the data is not empty
        if not self.data_sources['raw_data'].data['y_values2'].isna().all() and not self.data_sources['raw_data'].data['y_values1'].isna().all():
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

           
        else:
            # Clear the data in the plot, effectively showing an empty plot
            self.plots['time_series'].extra_y_ranges['right'].start = 0
            self.plots['time_series'].extra_y_ranges['right'].end = 0
            self.plots['time_series'].y_range.start = 0
            self.plots['time_series'].y_range.end = 0

            self.plots['time_series'].yaxis[0].axis_label = self.ui_elements["select_variable1"].value
            self.plots['time_series'].yaxis[1].axis_label = self.ui_elements["select_variable2"].value


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
