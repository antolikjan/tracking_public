from cmath import isnan
from bokeh.models import Column, Row, Range1d, Div, LinearAxis, RangeTool, Spacer, Label, Span, FactorRange, LabelSet, Select, Slider, RadioButtonGroup
from bokeh.transform import factor_cmap
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource
import numpy, scipy, pandas
from scripts.ui_framework.analysis_panel import AnalysisPanel
from scripts.data import event_weighted_average, event_triggered_change



class BloodTestsCorrelationsPanel(AnalysisPanel):
    def __init__(self, data, views, categories, metadata, title):
        AnalysisPanel.__init__(self,data,categories,metadata,title)
        ### WIDGETS
        self.register_widget(Select(title="Category",  options=list(categories.keys()), value = 'Fitbit'),'select_category',['value'])
        self.register_widget(Select(title = 'Name', value = 'DistanceFitbit', options = list(categories['Fitbit'])),'select_variable1',['value'])

        self.register_widget(Select(title="View",  options=list(views.keys()), value = 'WBC Rest'),'select_view',['value'])
        self.register_widget(Select(title = 'Biomarker Name', options = list(views['WBC Rest']), value='Leukocites (G/L)'),'select_variable2',['value'])


        
        self.register_widget(Select(title="Weighted average",  options=['None','Gauss','PastGauss','FutureGauss'], value = 'None'),"select_filter1",['value'])
        # self.register_widget(Select(title="Weighted average",  options=['None','Gauss','PastGauss','FutureGauss'], value = 'None'),"select_filter2",['value'])

        # self.register_widget(Slider(start=0.2, end=10, value=0.2, step=0.2, title="Sigma"),"select_sigma1",['value'])
        # self.register_widget(Slider(start=0.2, end=10, value=0.2, step=0.2, title="Sigma"),"select_sigma2",['value'])

        # self.register_widget(RadioButtonGroup(labels=["Var2 -> Var1","no shift","Var1 -> Var2"], active=1),'shift_button_group',['active'])

        self.data_sources['raw_data'] = ColumnDataSource(data={'x_values' : views['WBC Rest'].index,'y_values1' : data['DistanceFitbit'],'y_values2' : views['WBC Rest']['Leukocites (G/L)'] })
        # print(self.data_sources)


        self.curr_table = 'Fitbit'
        self.bloodtests_dates = views['WBC Rest']['Date']
        self.new_data = self.segment_dates('DistanceFitbit')


        # print(self.new_data)

        self.new_data = [i for i in self.new_data if i != 0]
        range1_start = min(self.new_data)-0.1*(max(self.new_data)-min(self.new_data))
        range1_end = max(self.new_data)+0.1*(max(self.new_data)-min(self.new_data))
        print(f"start of the range for DistanceFitbit (updated data) : {range1_start}")
        print(f"end of the range for DistanceFitbit (updated data) : {range1_end}")

        range2_start = views['WBC Rest']['Leukocites (G/L)'].min()-0.1*(views['WBC Rest']['Leukocites (G/L)'].max()-views['WBC Rest']['Leukocites (G/L)'].min())
        range2_end = views['WBC Rest']['Leukocites (G/L)'].max()+0.1*(views['WBC Rest']['Leukocites (G/L)'].max()-views['WBC Rest']['Leukocites (G/L)'].min())

        print(f"start of the range for Leukocites : {range2_start}")
        print(f"end of the range for Leukocites : {range2_end}")
            
            
        # FIGURE 1
        p1 = figure(width=300,height=320,sizing_mode="stretch_both",x_axis_type='datetime',y_range=(range1_start,range1_end),x_axis_location="above",tools="xpan",x_range=(data.index[1].timestamp()*1000,data.index[-1].timestamp()*1000))
        p1.extra_y_ranges = {"right" : Range1d(start=range2_start,end=range2_end)}
        p1.add_layout(LinearAxis(y_range_name="right"), 'right')
        self.plots['circles1'] = p1.circle(x='x_values',y='y_values1',source=self.data_sources['raw_data'],size=10,color="navy",alpha=0.5,legend_label='A')
        self.plots['circles2'] = p1.circle(x='x_values',y='y_values2',source=self.data_sources['raw_data'],size=10,color="green",alpha=0.5,y_range_name='right',legend_label='B')
        self.plots['filtered_line1'] = p1.line(x='x_values',y='y_values_post_processed1',source=self.data_sources['raw_data'],color="navy",alpha=1.0,visible=False, width = 2)
        self.plots['filtered_line2'] = p1.line(x='x_values',y='y_values_post_processed2',source=self.data_sources['raw_data'],color="green",alpha=1.0,y_range_name='right',visible=False, width = 2)   
        p1.yaxis[0].major_label_text_color = "navy"
        p1.yaxis[1].major_label_text_color = "green"
        p1.yaxis[0].axis_label = "DistanceFitbit"
        p1.yaxis[1].axis_label = "WBC Rest"
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
        # self.ui_elements["select_filter1"],

    def segment_dates(self, column_to_align):

        segmented = []
        new_entry_sum = 0
        num_of_summands = 0
        date_index = 0
        current_segment_date = pandas.to_datetime(self.bloodtests_dates[date_index])
        dates = self.raw_data.index 


        # print(f'current date from bloodtests is : {current_segment_date}')
        for i in range(len(dates)):

        # for i in range(70):
            date = dates[i]
            # print(f'comparing the dates: {date} and {current_segment_date}')
            if date <= current_segment_date: 
                # print(f'{date} is before {current_segment_date} so we now check the entry for this date in the datatable')
                if not isnan(self.raw_data[column_to_align][i]):
                    # print(f'=== the entry is not empty: {self.raw_data[column_to_align][i]}, so now we increase the number of summands and the sum itself')
                    # print(f'=== number of summands before was: {num_of_summands} and the sum was: {new_entry_sum}')
                    num_of_summands +=1
                    new_entry_sum += self.raw_data[column_to_align][i]
                    # print(f'=== now the number of summands is: {num_of_summands} and the sum is: {new_entry_sum}')

                # else:
                    # print(f'~~~ the entry is "NaN" so we do not include it')
            else:
                # print(f'~~~ {date} is after {current_segment_date} so we have to add the data gathered up until now to the array')

                if num_of_summands != 0:
                    new_entry = new_entry_sum/num_of_summands
                    # print(f'  * * appending {new_entry} to the list')
                else: 
                    # print('  * * number of summands was 0, so we add "NaN" to the array')
                    new_entry=0
                segmented.append(new_entry)
                
                # print(f'~~~ now updating the sum and the number of summands')

                date_index+=1
                if date_index == 26:
                    break
                current_segment_date = pandas.to_datetime(self.bloodtests_dates[date_index])
                # print(f' * updated date from bloodtests is: {current_segment_date}')
                # print(f' * and the the date from datatable is: {date}')

                if not isnan(self.raw_data[column_to_align][i]):
                    new_entry_sum = self.raw_data[column_to_align][i]
                    num_of_summands = 1

                else: 
                    # print(f'the entry at the new date {date} is empty so we are setting the sum to 0')
                    new_entry_sum = 0
                    num_of_summands = 0
        

        return segmented 




        