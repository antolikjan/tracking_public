import numpy, pandas, scipy

from bokeh.models import ColumnDataSource, Column, Row, Range1d, Div, LinearAxis, RangeTool, Select, Slider, Spacer, Slope
from bokeh.plotting import figure
from scripts.ui_framework.analysis_panel import AnalysisPanel
from scripts.data import data_aquisition_overlap_non_nans

class BloodTestsCorrelationsPanel(AnalysisPanel):
    def __init__(self, data, views, categories, metadata, title):

        """
        Initialize the BloodTestsCorrelationsPanel class.

        Args:
            data: Data for analysis.
            views: Views of bloodtest records.
            categories: Categories of the data.
            metadata: Metadata for data.
            title: Title for the panel.
        """

        AnalysisPanel.__init__(self,data,categories,metadata,title)


        self.views = views
        self.bloodtest_dates = views['Minerals'].index     # dates of blood tests

        ### WIDGETS
        ## Initialize and register various widgets for user interaction.
          
          # widgets for variable 1
        self.register_widget(Select(title="Category",  options=list(categories.keys()), value = 'Fitbit'),'select_category',['value'])
        self.register_widget(Select(title = 'Name', value = 'DistanceFitbit', options = list(categories['Fitbit'])),'select_variable1',['value'])

          # widgets for variable 2
        self.register_widget(Select(title="View",  options=list(views.keys()), value = 'Minerals'),'select_view',['value'])
        self.register_widget(Select(title = 'Biomarker Name', options = list(views['Minerals']), value='P (mmol/l)'),'select_variable2',['value'])

        self.register_widget(Slider(start=10, end=300, value=30, step=1, title="Number of days to average variable 1 on"),"select_segmentation",['value'])


        # Segment and filter data for analysis
        v1_segmented, v2_filtered = self.segment_and_filter_redundant_data('DistanceFitbit', 'Minerals', 'P (mmol/l)')


        self.new_data = {}
        self.new_data['DistanceFitbit'] = v1_segmented

        # Create ColumnDataSources for the plots
        self.data_sources['raw_data'] = ColumnDataSource(data={'x_values' : self.bloodtest_dates,'y_values1' : numpy.nan_to_num(self.new_data['DistanceFitbit']["segmented"]),'y_values2' : numpy.nan_to_num(v2_filtered) })
        self.data_sources['source_corr'] = ColumnDataSource(data={'x_values' : numpy.nan_to_num(v2_filtered),'y_values' : numpy.nan_to_num(self.new_data['DistanceFitbit']["segmented"])})
        self.data_sources['source_corr_mean'] = ColumnDataSource(data={'x_values' : [],'y_values' : [], 'sem-' : [], 'sem+' : []})


        # PLOT 1 - the first plot for time series data
            # ranges of both variables
        range1_start = numpy.nanmin(self.new_data['DistanceFitbit']['segmented']) - 0.1 * (numpy.nanmax(self.new_data['DistanceFitbit']['segmented']) - numpy.nanmin(self.new_data['DistanceFitbit']['segmented']))
        range1_end = numpy.nanmax(self.new_data['DistanceFitbit']['segmented']) + 0.1 * (numpy.nanmax(self.new_data['DistanceFitbit']['segmented']) - numpy.nanmin(self.new_data['DistanceFitbit']['segmented']))
        range2_start = numpy.nanmin(v2_filtered)-0.1*(numpy.nanmax(v2_filtered)-numpy.nanmin(v2_filtered))
        range2_end = numpy.nanmax(v2_filtered)+0.1*(numpy.nanmax(v2_filtered)-numpy.nanmin(v2_filtered))


        p1 = figure(width=300, height=320, sizing_mode="stretch_both", x_axis_type='datetime',
            y_range=(range1_start, range1_end),  tools="xpan",
            x_range=(self.new_data['DistanceFitbit'].index[1].timestamp()*1000,
                    self.new_data['DistanceFitbit'].index[-1].timestamp()*1000))

        p1.extra_y_ranges = {"right" : Range1d(start=range2_start,end=range2_end)}
        p1.add_layout(LinearAxis(y_range_name="right"), 'right')
            #  circle plots on the plot
        self.plots['circles1'] = p1.circle(x='x_values',y='y_values1',source=self.data_sources['raw_data'],size=10,color="navy",alpha=0.5,legend_label='A')
        self.plots['circles2'] = p1.circle(x='x_values',y='y_values2',source=self.data_sources['raw_data'],size=10,color="green",alpha=0.5,y_range_name='right',legend_label='B')
        
            # additional features
        p1.yaxis[0].major_label_text_color = "navy"
        p1.yaxis[1].major_label_text_color = "green"
        p1.yaxis[0].axis_label = "DistanceFitbit"
        p1.yaxis[1].axis_label = "P (mmol/l)"
        p1.toolbar_location = None

            # a RangeTool for interactive range selection on the x-axis.
        rt = RangeTool(x_range=p1.x_range)
        rt.overlay.fill_color = "navy"
        rt.overlay.fill_alpha = 0.2
        
            # register the RangeTool as a widget
        self.register_widget(rt.x_range, 'range_tool_x_range', ['start','end'])

            # store the plot in the plots dictionary for later reference
        self.plots['time_series'] = p1

        

        # PLOT 2 - the second Bokeh plot for correlations between the chosen variables
        p2 = figure(width=300,height=300,sizing_mode="stretch_both",title='')
        p2.circle(x='x_values',y='y_values',source=self.data_sources['source_corr'],size=5,color="black",alpha=1.0)

            # a line connecting data points for a clearer trend
        p2.line(x='x_values',y='y_values',source=self.data_sources['source_corr_mean'],line_width=4,color="black",alpha=0.5)
            # a shaded area (varea) to represent the standard error of the mean (sem)
        p2.varea(x='x_values',y1='sem-',y2='sem+',source=self.data_sources['source_corr_mean'],color="black",alpha=0.1)

        p2.xaxis.axis_label = "DistanceFitbit"
        p2.yaxis.axis_label = "P (mmol/l)"

            # remove the toolbar from the plot, making it non-interactive
        p2.toolbar_location = None
            #  a Slope annotation for the plot to display the correlation line
        p2_slope = Slope(gradient=0, y_intercept=0, line_color='orange', line_dash='dashed', line_width=3.5)
        p2.add_layout(p2_slope) 

            # store the plot and the Slope annotation in the class for later reference
        self.plots['correlations'] = p2
        self.plots['correlations_slope'] = p2_slope 
            

    def compose_widgets(self):
        """
        Compose the layout of widgets for the panel
        """
        spacer1 = Spacer(width = 260, height=90)

         # widgets of variable 1 
        widgets_var1 = Column(Div(text="""<b>Variable 1</b>"""), self.ui_elements["select_category"], self.ui_elements["select_variable1"], sizing_mode="fixed", width=120, height=500)
         # widgets of variable 2
        widgets_var2 = Column(Div(text="""<b>Variable 2</b>"""), self.ui_elements["select_view"], self.ui_elements["select_variable2"], sizing_mode="fixed", width=120, height=500)
        spacer2 = Spacer(width=20, height=40)

         # segmentation slider bar widget
        widgets_var3 = Column(Div(text="""<b>Segmentation Range</b>"""), self.ui_elements["select_segmentation"], sizing_mode="fixed", width=260, height=500)
        spacer3 = Spacer(width=40, height=70)
        horiz_spacer = Spacer(width = 20)

        layout_top = Row(horiz_spacer, widgets_var1, spacer2, widgets_var2, width=480)
        layout_bottom = Row(horiz_spacer, widgets_var3)

        layout = Column(spacer1, layout_top, spacer3, layout_bottom)
        
        return layout



    def compose_plots(self):
        """
        Compose the layout of plots for the panel
        """
        vertical_spacer = Spacer(width = 100, height=10)
        horiz_spacer = Spacer(width = 20)
        return Row(Column(vertical_spacer, Row(horiz_spacer, self.plots['time_series'], width=1200), Row(horiz_spacer, self.plots["correlations"], width=1150),   sizing_mode='stretch_both'), sizing_mode='scale_width')



    def segment_and_filter_redundant_data(self, column_to_align, curr_view, biomarker, segmentation_period=30):
        """
        Segment and filter data for analysis. 

        Args:
            column_to_align: variable 2 name for alignment.
            curr_view: Current view of the bloodtests record.
            biomarker: variable 2 to analyze.
            segmentation_period: Segmentation period for variable 1.

        Returns:
            v1_segmented: Segmented data for variable 1.
            v2_filtered: Filtered data for variable 2.
        """

        segmented = []
        v2_filtered = self.views[curr_view][biomarker].copy()

        for i in range(len(self.bloodtest_dates)):
            date = self.bloodtest_dates[i]
            biomarker_entry = v2_filtered[i]

            # Ensure we only include dates with non-NaN data for both variables
            if pandas.isna(biomarker_entry):  # if entry of a biomarker is NaN, the corresponding 
                segmented.append(pandas.NA)   # entry in the segmented data of variable 2 is also NaN

            else:

                segment_start_date = date - pandas.Timedelta(days=segmentation_period)
                segment_end_date = date

                # Create a mask to filter data within the specified date range
                slice_range = (self.raw_data[column_to_align].index >= segment_start_date) & (self.raw_data[column_to_align].index <= segment_end_date)
                
                # Extract the relevant data of variable 2 within the date range
                slice = self.raw_data[column_to_align][slice_range]

                # Add the slice to the list of segments
                segmented.append(slice)
        

        # Calculate averages of the slices of the segmented array
        averages = []
        for j in range(len(segmented)):
            slice_df = segmented[j]
            try:
                slice_averages = slice_df.mean()
            except:     # Handle cases where the slice contains NaN values
                slice_averages = numpy.nan


            # Include only dates for which both variables have non-NaN datapoints
            if pandas.isna(slice_averages):            # if entry of the segmented data of variable 2 is NaN, 
                v2_filtered.iloc[j] = pandas.NA        # the corresponding entry of a biomarker is also NaN

            averages.append(slice_averages)
        
            # Create a DataFrame to store the segmented data
        v1_segmented = pandas.DataFrame(averages, columns=["segmented"], index=self.bloodtest_dates)
        
        # Sort the DataFrame by index (date)
        v1_segmented.sort_index(inplace=True)
        
        return v1_segmented, v2_filtered


    def update_widgets(self):
        """
        Update widget options based on user selections
        """
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
        """
        Update data for analysis based on changes in widgets.
        """

        # Update name of the bloodtest biomarker (var2)
        current_view = self.ui_elements["select_view"].value
        if current_view != None:
            var2_name = self.ui_elements["select_variable2"].value

        # Update the data of variable 1 and variable 2 
        var1_name = self.ui_elements["select_variable1"].value

        # Call the segment_and_filter_redundant_data method to obtain segmented and filtered data.
        # This method returns v1_segmented (variable 1) and var2_filtered (variable 2).
        df_var1, var2 = self.segment_and_filter_redundant_data(var1_name, current_view, var2_name, self.ui_elements["select_segmentation"].value)
        # Extract segmented data for variable 1
        var1 = df_var1["segmented"]

        # Update the data sources with the new variable data.
        self.data_sources['raw_data'].data['y_values1'] = var1
        self.data_sources['raw_data'].data['y_values2'] = var2

        # Flatten the variable 1 data into an array for analysis.
        var1_array = var1.to_numpy().flatten()

        # Check that variables are not all NaN value columns
        if not var1.isna().all() and not var2.isna().all():
            # Create a mask to filter out NaN values.
            nan_mask = ~numpy.isnan(var1_array) & ~numpy.isnan(var2)

            # Apply the mask to obtain filtered data for variable 1 and variable 2.
            var1_filtered = var1_array[nan_mask]
            var2_filtered = var2[nan_mask]

            # Calculate statistics for the correlation analysis.
            self.data_sources['source_corr'].data = {'x_values' : var1 , 'y_values' : var2}
            m, bins, _ = scipy.stats.binned_statistic(var1_filtered, var2_filtered, statistic='mean', bins=min(20,len(set(var1_filtered))))
            std, bins, _ = scipy.stats.binned_statistic(var1_filtered, var2_filtered, statistic='std', bins=min(20,len(set(var1_filtered))))
            count, bins, _ = scipy.stats.binned_statistic(var1_filtered, var2_filtered, statistic='count', bins=min(20,len(set(var1_filtered))))

            # Calculate standard error of the mean (SEM).
            sem = std/numpy.sqrt(len(count)-1)
            x = bins[:-1] + (bins[1:] - bins[:-1])/2.0

            # Update the data source for the mean and SEM values of the correlation plot.
            self.data_sources['source_corr_mean'].data = {'x_values' : x , 'y_values' : m, 'sem+' : m+sem, 'sem-' : m-sem}

    def update_plots(self):
        
        super().update_plots()

        # Check that the data is not empty
        if not self.data_sources['raw_data'].data['y_values2'].isna().all() and not self.data_sources['raw_data'].data['y_values1'].isna().all():
            if numpy.nanmax(self.data_sources['raw_data'].data['y_values2']) != numpy.nanmin(self.data_sources['raw_data'].data['y_values2']):
                # Adjust the y-axis range for variable 2 if the data is not empty.
                self.plots['time_series'].extra_y_ranges['right'].start=numpy.nanmin(self.data_sources['raw_data'].data['y_values2'])-0.1*(numpy.nanmax(self.data_sources['raw_data'].data['y_values2'])-numpy.nanmin(self.data_sources['raw_data'].data['y_values2']))
                self.plots['time_series'].extra_y_ranges['right'].end=numpy.nanmax(self.data_sources['raw_data'].data['y_values2'])+0.1*(numpy.nanmax(self.data_sources['raw_data'].data['y_values2'])-numpy.nanmin(self.data_sources['raw_data'].data['y_values2']))
            else:
                # Set default y-axis range for variable 2 if the data is empty.
                self.plots['time_series'].extra_y_ranges['right'].start = 0.9 * numpy.nanmax(self.data_sources['raw_data'].data['y_values2'])
                self.plots['time_series'].extra_y_ranges['right'].end = 1.1 * numpy.nanmax(self.data_sources['raw_data'].data['y_values2'])
            
            # Update axis labels for variable 1 and variable 2.
            self.plots['time_series'].yaxis[0].axis_label = self.ui_elements["select_variable1"].value
            self.plots['time_series'].yaxis[1].axis_label = self.ui_elements["select_variable2"].value

            if numpy.nanmax(self.data_sources['raw_data'].data['y_values1']) != numpy.nanmin(self.data_sources['raw_data'].data['y_values1']):
                # Adjust the y-axis range for variable 1 if the data is not empty.    
                self.plots['time_series'].y_range.start=numpy.nanmin(self.data_sources['raw_data'].data['y_values1'])-0.1*(numpy.nanmax(self.data_sources['raw_data'].data['y_values1'])-numpy.nanmin(self.data_sources['raw_data'].data['y_values1']))
                self.plots['time_series'].y_range.end=numpy.nanmax(self.data_sources['raw_data'].data['y_values1'])+0.1*(numpy.nanmax(self.data_sources['raw_data'].data['y_values1'])-numpy.nanmin(self.data_sources['raw_data'].data['y_values1']))     
            else:
                # Set default y-axis range for variable 1 if the data is empty.
                self.plots['time_series'].y_range.start = 0.9 * numpy.nanmax(self.data_sources['raw_data'].data['y_values1'])
                self.plots['time_series'].y_range.end = 1.1 * numpy.nanmax(self.data_sources['raw_data'].data['y_values1'])

           
        else:
            # Clear the data in the plot, effectively showing an empty plot
            self.plots['time_series'].extra_y_ranges['right'].start = 0
            self.plots['time_series'].extra_y_ranges['right'].end = 0
            self.plots['time_series'].y_range.start = 0
            self.plots['time_series'].y_range.end = 0

            # Update axis labels for variable 1 and variable 2
            self.plots['time_series'].yaxis[0].axis_label = self.ui_elements["select_variable1"].value
            self.plots['time_series'].yaxis[1].axis_label = self.ui_elements["select_variable2"].value


    # Check if correlations can be calculated from at least 10 data points
        x,y = data_aquisition_overlap_non_nans(self.data_sources['source_corr'].data['x_values'],self.data_sources['source_corr'].data['y_values'])
        if len(x) > 10:
            res = scipy.stats.linregress(x,y) 
            if not numpy.isnan(res.slope):
                # Update the slope and intercept for the correlation plot
                self.plots['correlations_slope'].gradient = res.slope
                self.plots['correlations_slope'].y_intercept = res.intercept
                # Update the title of the correlation plot with correlation coefficient and p-value information 
                self.plots['correlations'].title.text = 'R=' +str(res.rvalue) + ';              (p=' + "{0:.6g}".format(res.pvalue) + '; N=' + "{0:.6g}".format(len(self.data_sources['source_corr'].data['x_values'])) + ')'
                self.plots['correlations_slope'].visible = True
            else:
                # Hide the correlation slope if the slope is NaN
                self.plots['correlations_slope'].visible = False
                self.plots['correlations'].title.text = 'R: N/A      p_value: N/A'

        else:
            # Hide the correlation slope if there are not enough data points
            self.plots['correlations_slope'].visible = False
            self.plots['correlations'].title.text = 'R: N/A      p_value: N/A'
