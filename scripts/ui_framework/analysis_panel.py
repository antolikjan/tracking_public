from bokeh.models import Row, Div, Spacer, Panel
from scripts.data import categories, filter_data, cross_corr, both_valid, data_aquisition_overlap
from functools import partial


class AnalysisPanel():
      """
      Panel is a high level UI concept based around following assumptions:

      * There are three main elements - Widgets, Data and Plots
      * There is a bar of Widget elements on the left that are all created inserted in the *ui_elements* dictionary in the constructor 
        and composed into a layout by the *compose_widgets* function.
      * All the plots are on the right. They are also created and interpreted in the *plots* dictionary in the constructor
        and composed into a layout by the *compose_plots* function.
      * There is data that are plotted - these are in the *data_sources* dictionary. Data are plotted in the plots. 
      * Changes to the ui_elements cause changes to other ui elements (the *update_widgets* function).
      * Changes to the ui_elements cause changes to data (the *update_data* function).
      * Whenever data is changed all the plots are updated (the *update_plots* function).
      * The most reusable and transparent design has minimal content in the *update_widgets* and *update_plots* and most functionality in *update_data*
      """

      def __init__(self,data,categories,metadata,title):
          self.raw_data = data
          self.categories = categories
          self.metadata = metadata
          self.data_sources = {}
          self.ui_elements = {}
          self.plots = {}
          self.title = title

      def update_widgets(self):
          """
          This function updates other widgets in response to change in a widget.
          """
          pass


      def update_data(self):
          """
          This function updates all the data in *data_sources*. It is triggered after any change to ui. It is expected to be overridden.
          """
          pass

      def update_plots(self):
          """
          This function updates all the plots. It is triggered after any change to data. It is expected to be overridden.
          """
          pass

      def compose_widgets(self):
          """
          This function is expected to compose the bar of widgets. 

          It should return a layout.
          """
          pass

      def compose_plots(self):
          """
          This function is expected to compose all the plots that will sit on the right. 

          It should return a layout.
          """        
          pass

      def compose_panel(self):
          """
          This function takes the layouts created by *compose_ui* and *compose_plots* and turns them into panel which is returned.
          """
          layout = Row(self.compose_widgets(),Spacer(width=20),self.compose_plots(),sizing_mode="stretch_both")
            
          panel = Panel(child=layout, title=self.title)

          self.update_widgets()        
          self.update_data()        
          self.update_plots()

          return panel


      def update(self,attr,old,new):
          print('Update: ')
          print(attr)
          print(old)
          print(new)
          print('-----------------')
          self.update_widgets()        
          self.update_data()        
          self.update_plots()
          print('Finished')

      def register_widget(self,widget,widget_name,actions_to_respond_to):
          """
          This is how one registers widget in the UI.

          Parameters:
          widget (object): the widget to register
          widget_name (str): the name under which to register it
          actions_to_respond_to (list): the list of actions which need to trigger update
          """
          assert widget_name not in self.ui_elements, "UI element %s has already been registered" % (widget_name)              
          self.ui_elements[widget_name] = widget
          for action in actions_to_respond_to:
              self.ui_elements[widget_name].on_change(action, self.update)
              



