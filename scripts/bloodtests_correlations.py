from turtle import width
import numpy, pandas

from bokeh.models import ColumnDataSource, Column, Row, Range1d, Div, LinearAxis, RangeTool, Select, Slider, Spacer
from bokeh.plotting import figure
from scripts.ui_framework.analysis_panel import AnalysisPanel



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

        # Populating segmented data
        segmented_data = self.segment_dates('DistanceFitbit', 'WBC Rest', 'Leukocites (G/L)')
        self.new_data = {}
        self.new_data['DistanceFitbit'] = segmented_data

        # y_values1 = numpy.nan_to_num(self.data_sources['raw_data'].data['y_values1'])
        # self.plots['time_series'].y_range.start = numpy.nanmin(y_values1) - 0.1 * (numpy.nanmax(y_values1) - numpy.nanmin(y_values1))
        self.data_sources['raw_data'] = ColumnDataSource(data={'x_values' : self.bloodtest_dates,'y_values1' : numpy.nan_to_num(self.new_data['DistanceFitbit']["segmented"]),'y_values2' : numpy.nan_to_num(views['WBC Rest']['Leukocites (G/L)']) })


        # PLOT 1
        range1_start = numpy.nanmin(self.new_data['DistanceFitbit']['segmented']) - 0.1 * (numpy.nanmax(self.new_data['DistanceFitbit']['segmented']) - numpy.nanmin(self.new_data['DistanceFitbit']['segmented']))
        range1_end = numpy.nanmax(self.new_data['DistanceFitbit']['segmented']) + 0.1 * (numpy.nanmax(self.new_data['DistanceFitbit']['segmented']) - numpy.nanmin(self.new_data['DistanceFitbit']['segmented']))
        range2_start = numpy.nanmin(views['WBC Rest']['Leukocites (G/L)'])-0.1*(numpy.nanmax(views['WBC Rest']['Leukocites (G/L)'])-numpy.nanmin(views['WBC Rest']['Leukocites (G/L)']))
        range2_end = numpy.nanmax(views['WBC Rest']['Leukocites (G/L)'])+0.1*(numpy.nanmax(views['WBC Rest']['Leukocites (G/L)'])-numpy.nanmin(views['WBC Rest']['Leukocites (G/L)']))


        p1 = figure(width=300, height=320, sizing_mode="stretch_both", x_axis_type='datetime',
            y_range=(range1_start, range1_end), x_axis_location="above", tools="xpan",
            x_range=(self.new_data['DistanceFitbit'].index[1].timestamp()*1000,
                    self.new_data['DistanceFitbit'].index[-1].timestamp()*1000))

        p1.extra_y_ranges = {"right" : Range1d(start=range2_start,end=range2_end)}
        p1.add_layout(LinearAxis(y_range_name="right"), 'right')
        self.plots['circles1'] = p1.circle(x='x_values',y='y_values1',source=self.data_sources['raw_data'],size=10,color="navy",alpha=0.5,legend_label='A')
        self.plots['circles2'] = p1.circle(x='x_values',y='y_values2',source=self.data_sources['raw_data'],size=10,color="green",alpha=0.5,y_range_name='right',legend_label='B')
        # self.plots['filtered_line1'] = p1.line(x='x_values',y='y_values_post_processed1',source=self.data_sources['raw_data'],color="navy",alpha=1.0,visible=False, width = 2)
        # self.plots['filtered_line2'] = p1.line(x='x_values',y='y_values_post_processed2',source=self.data_sources['raw_data'],color="green",alpha=1.0,y_range_name='right',visible=False, width = 2)   
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
        vertical_spacer = Spacer(width = 260, height=70)
        horiz_spacer = Spacer(width = 40)
        return Row(Column(vertical_spacer, Row(horiz_spacer, self.plots['time_series'], width=1200)))


    def temp(self):
        for i in range(26):
            entry = self.views["Immunity"]["IgM (g/l)"][i]
            print(entry)

            print(f'now check if its nan: {pandas.isna(entry)}')

    def segment_dates(self, column_to_align, curr_view, biomarker, segmentation_period=30):
        segmented = []

        for i in range(len(self.bloodtest_dates)):
            date = self.bloodtest_dates[i]
            biomarker_entry = self.views[curr_view][biomarker][i]
            if pandas.isna(biomarker_entry):
                # print(f'@@@@@@@@@@@@@@@@@@@@@ {biomarker} is empty at date: {date} - {numpy.dtype(biomarker_entry)}')
                segmented.append(0)
            else:

                segment_start_date = date - pandas.Timedelta(days=segmentation_period)
                segment_end_date = date

                # filtering the given column based on the date range
                slice_range = (self.raw_data[column_to_align].index >= segment_start_date) & (self.raw_data[column_to_align].index <= segment_end_date)
                slice = self.raw_data[column_to_align][slice_range]

                # adding the slice to the list of segments
                segmented.append(slice)
        
        segmented_averages = self.average_of_segment(segmented)

        return segmented_averages

    def average_of_segment(self, segment):
        averages = []

        for slice_df in segment:
            if type(slice_df) == int and slice_df==0:
                averages.append(0)
            else:
                slice_averages = slice_df.mean()
                averages.append(slice_averages)

        result = pandas.DataFrame(averages, columns=["segmented"], index=self.bloodtest_dates)
        result.sort_index(inplace=True)

        return result


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
        ## Update the data of the bloodtest biomarker (var2)
        current_view = self.ui_elements["select_view"].value
        if current_view != None:
            var2_name = self.ui_elements["select_variable2"].value
            var2 = self.views[current_view][var2_name].copy()
        

        ## Update the data of variable 1, depending on var2 and the days (prior to the date of var2) it should be averaged over
        var1_name = self.ui_elements["select_variable1"].value
        var1 = self.segment_dates(var1_name, current_view, var2_name, self.ui_elements["select_segmentation"].value)["segmented"]


        self.data_sources['raw_data'].data['y_values1'] = var1
        self.data_sources['raw_data'].data['y_values2'] = var2


    def update_plots(self):
        super().update_plots()

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
