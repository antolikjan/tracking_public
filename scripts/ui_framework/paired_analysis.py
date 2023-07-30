from bokeh.models import Select, Column, Row, LinearAxis, Slider, CheckboxGroup, Div, Spacer, Label, Slope, RadioButtonGroup
from bokeh.models import ColumnDataSource
from scripts.data import filter_data
from .analysis_panel import AnalysisPanel

class PairedAnalysis(AnalysisPanel):

      def __init__(self,data,categories,metadata,title):
          AnalysisPanel.__init__(self,data,categories,metadata,title)

          ### WIDGETS
          self.register_widget(Select(title="Category",  options=list(categories.keys()), value = 'Fitbit'),'select_category1',['value'])
          self.register_widget(Select(title = 'Name', value = 'DistanceFitbit', options = list(categories['Fitbit'])),'select_variable1',['value'])

          self.register_widget(Select(title="Category",  options=['None']+list(categories.keys()), value = 'Fitbit'),'select_category2',['value'])
          self.register_widget(Select(title = 'Name', value = 'RHR', options = list(categories['Fitbit'])),'select_variable2',['value'])

          self.register_widget(Select(title="Weighted average",  options=['None','Gauss','PastGauss','FutureGauss'], value = 'None'),"select_filter1",['value'])
          self.register_widget(Select(title="Weighted average",  options=['None','Gauss','PastGauss','FutureGauss'], value = 'None'),"select_filter2",['value'])

          self.register_widget(Slider(start=0.2, end=10, value=0.2, step=0.2, title="Sigma"),"select_sigma1",['value'])
          self.register_widget(Slider(start=0.2, end=10, value=0.2, step=0.2, title="Sigma"),"select_sigma2",['value'])

          self.register_widget(RadioButtonGroup(labels=["Var2 -> Var1","no shift","Var1 -> Var2"], active=1),'shift_button_group',['active'])

          ### DATA
          self.data_sources['raw_data'] = ColumnDataSource(data={'x_values' : data.index,'y_values1' : data['DistanceFitbit'],'y_values2' : data['RHR'],'y_values_filtered' : data['DistanceFitbit'],'y_values_filtered' : data['RHR'],'filter1' : data['RHR']*0,'filter2' : data['RHR']*0})

      def compose_widgets(self):
          widgets_var1 = Column(Div(text="""<b>Varibale 1</b>"""),self.ui_elements["select_category1"], self.ui_elements["select_variable1"],self.ui_elements["select_filter1"],self.ui_elements["select_sigma1"],sizing_mode="fixed", width=120,height=500)
          widgets_var2 = Column(Div(text="""<b>Varibale 2</b>"""),self.ui_elements["select_category2"], self.ui_elements["select_variable2"],self.ui_elements["select_filter2"],self.ui_elements["select_sigma2"],sizing_mode="fixed", width=120,height=500)  
          w1 = Row(widgets_var1,widgets_var2,width=240)
          w2 = Column(w1,Div(text="""<hr width=240px>"""),self.ui_elements["shift_button_group"],width=240)
          return w2

      def update_widgets(self):
          self.ui_elements["select_variable1"].options = list(self.categories[self.ui_elements["select_category1"].value])

          if self.ui_elements["select_category2"].value != 'None':
            self.ui_elements["select_variable2"].options = list(self.categories[self.ui_elements["select_category2"].value])
          else:
            self.ui_elements["select_variable2"].options = ['None']

          if self.ui_elements["select_variable1"].value not in self.categories[self.ui_elements["select_category1"].value]:
             self.ui_elements["select_variable1"].value = self.categories[self.ui_elements["select_category1"].value][0]

          if self.ui_elements["select_category2"].value != 'None':
            if self.ui_elements["select_variable2"].value not in self.categories[self.ui_elements["select_category2"].value]:
               self.ui_elements["select_variable2"].value = self.categories[self.ui_elements["select_category2"].value][0]

      def update_data(self):

          d1 = self.raw_data[self.ui_elements["select_variable1"].value].copy()
          if self.ui_elements["select_category2"].value != None:
             d2 = self.raw_data[self.ui_elements["select_variable2"].value].copy()
          
          if self.ui_elements['shift_button_group'].active == 0:
             d1[0:-1] = d1[1:]
             d1[-1] = float('NaN')

          if self.ui_elements['shift_button_group'].active == 2:
             d2[0:-1] = d2[1:]
             d2[-1] = float('NaN')

          self.data_sources['raw_data'].data['y_values1'] = d1
          self.data_sources['raw_data'].data['y_values2'] = d2

          if self.ui_elements["select_filter1"].value == 'None':
             self.data_sources['raw_data'].data['y_values_post_processed1'] = self.data_sources['raw_data'].data['y_values1']
             self.data_sources['raw_data'].data['filter1'] *=0
          else:
             filtr,result1 = filter_data(self.ui_elements["select_filter1"].value,self.data_sources['raw_data'].data['y_values1'],self.ui_elements["select_sigma1"].value)
             self.data_sources['raw_data'].data['y_values_post_processed1'] = result1
             self.data_sources['raw_data'].data['filter1'] = filtr/filtr.max()

          if self.ui_elements["select_filter2"].value == 'None':
             self.data_sources['raw_data'].data['y_values_post_processed2'] = self.data_sources['raw_data'].data['y_values2']
             self.data_sources['raw_data'].data['filter2'] *=0
          else:
             filtr,result2 = filter_data(self.ui_elements["select_filter2"].value,self.data_sources['raw_data'].data['y_values2'],self.ui_elements["select_sigma2"].value)
             self.data_sources['raw_data'].data['y_values_post_processed2'] = result2
             self.data_sources['raw_data'].data['filter2'] = filtr/filtr.max()

