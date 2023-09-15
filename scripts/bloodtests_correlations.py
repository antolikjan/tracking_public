from cmath import isnan
from queue import Empty
from bokeh.models import Column, Row, Range1d, Div, LinearAxis, RangeTool, Spacer, Label, Span, FactorRange, LabelSet, Select, Slider, RadioButtonGroup
from bokeh.transform import factor_cmap
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource
import numpy, scipy, pandas
from scripts.ui_framework.analysis_panel import AnalysisPanel
from scripts.data import event_weighted_average, event_triggered_change, convert_to_dataframe



class BloodTestsCorrelationsPanel(AnalysisPanel):
    def __init__(self, data, views, categories, metadata, title):
        AnalysisPanel.__init__(self,data,categories,metadata,title)
        ### WIDGETS
        self.register_widget(Select(title="Category",  options=list(categories.keys()), value = 'Fitbit'),'select_category',['value'])
        self.register_widget(Select(title = 'Name', value = 'DistanceFitbit', options = list(categories['Fitbit'])),'select_variable1',['value'])

        self.register_widget(Select(title="View",  options=list(views.keys()), value = 'WBC Rest'),'select_view',['value'])
        self.register_widget(Select(title = 'Biomarker Name', options = list(views['WBC Rest']), value='Leukocites (G/L)'),'select_variable2',['value'])

        self.register_widget(Select(title="Weighted average",  options=['None','Gauss','PastGauss','FutureGauss'], value = 'None'),"select_filter1",['value'])




        self.bloodtest_dates = views['WBC Rest'].index

        # Populating segmented data
        segmented_data = self.segment_dates('DistanceFitbit')
        segmented_data.sort_index(inplace=True)

        self.new_data = {}
        self.new_data['DistanceFitbit'] = segmented_data


        self.data_sources['raw_data'] = ColumnDataSource(data={'x_values' : self.bloodtest_dates,'y_values1' : self.new_data['DistanceFitbit']["segmented"],'y_values2' : views['WBC Rest']['Leukocites (G/L)'] })

        

        # PLOT 1
        range1_start = self.new_data['DistanceFitbit']['segmented'].min() - 0.1 * (self.new_data['DistanceFitbit']['segmented'].max() - self.new_data['DistanceFitbit']['segmented'].min())
        range1_end = self.new_data['DistanceFitbit']['segmented'].max() + 0.1 * (self.new_data['DistanceFitbit']['segmented'].max() - self.new_data['DistanceFitbit']['segmented'].min())
        range2_start = views['WBC Rest']['Leukocites (G/L)'].min()-0.1*(views['WBC Rest']['Leukocites (G/L)'].max()-views['WBC Rest']['Leukocites (G/L)'].min())
        range2_end = views['WBC Rest']['Leukocites (G/L)'].max()+0.1*(views['WBC Rest']['Leukocites (G/L)'].max()-views['WBC Rest']['Leukocites (G/L)'].min())


        p1 = figure(width=300, height=320, sizing_mode="stretch_both", x_axis_type='datetime',
            y_range=(range1_start, range1_end), x_axis_location="above", tools="xpan",
            x_range=(self.new_data['DistanceFitbit'].index[1].timestamp()*1000,
                    self.new_data['DistanceFitbit'].index[-1].timestamp()*1000))

        p1.extra_y_ranges = {"right" : Range1d(start=range2_start,end=range2_end)}
        p1.add_layout(LinearAxis(y_range_name="right"), 'right')
        self.plots['circles1'] = p1.circle(x='x_values',y='y_values1',source=self.data_sources['raw_data'],size=10,color="navy",alpha=0.5,legend_label='A')
        self.plots['circles2'] = p1.circle(x='x_values',y='y_values2',source=self.data_sources['raw_data'],size=10,color="green",alpha=0.5,y_range_name='right',legend_label='B')
        self.plots['filtered_line1'] = p1.line(x='x_values',y='y_values_post_processed1',source=self.data_sources['raw_data'],color="navy",alpha=1.0,visible=False, width = 2)
        self.plots['filtered_line2'] = p1.line(x='x_values',y='y_values_post_processed2',source=self.data_sources['raw_data'],color="green",alpha=1.0,y_range_name='right',visible=False, width = 2)   
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
        widgets_var1 = Column(Div(text="""<b>Variable 1</b>"""),self.ui_elements["select_category"], self.ui_elements["select_variable1"],sizing_mode="fixed", width=120,height=500)
        widgets_var2 = Column(Div(text="""<b>Variable 2</b>"""),self.ui_elements["select_view"], self.ui_elements["select_variable2"],sizing_mode="fixed", width=120,height=500)  
        w1 = Row(widgets_var1,widgets_var2,width=240)
        # w2 = Column(w1,Div(text="""<hr width=240px>"""),self.ui_elements["shift_button_group"],width=240)
        return w1


    def compose_plots(self):
        return Row(self.plots['time_series'])



    def segment_dates(self, column_to_align):
        segmented = []
        new_entry_sum = 0
        num_of_summands = 0
        date_index = 0

        current_bloodtest_date = self.bloodtest_dates[date_index]

        for i in range(len(self.raw_data.index)):
            date = self.raw_data.index[i]
            if pandas.isna(current_bloodtest_date) or date <= current_bloodtest_date: 
                if not pandas.isna(self.raw_data[column_to_align][i]):
                    num_of_summands +=1
                    new_entry_sum += self.raw_data[column_to_align][i]
            else:
                new_entry = new_entry_sum / num_of_summands if num_of_summands != 0 else 0

                segmented.append(new_entry)

                date_index += 1
                if date_index == len(self.bloodtest_dates):
                    break

                current_bloodtest_date = self.bloodtest_dates[date_index]

                if not pandas.isna(self.raw_data[column_to_align][i]):
                    new_entry_sum = self.raw_data[column_to_align][i]
                    num_of_summands = 1
                else: 
                    new_entry_sum = 0
                    num_of_summands = 0

        return pandas.DataFrame(segmented, columns=["segmented"], index=self.bloodtest_dates)

