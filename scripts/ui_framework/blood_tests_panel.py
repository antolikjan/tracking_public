# from tkinter.tix import Select
from re import S
from bokeh.models import Panel, DataTable, Select
from bokeh.models import Row, Div, Spacer, Panel, Column

from bokeh.models import ColumnDataSource
from scripts.data import filter_data

class BloodTestPanel():
    def __init__(self, data):
        self.views = data.keys()
        self.raw_data = data
        # self.metadata = metadata
        self.ui_elements = {}
        self.tables = {}
        self.table = 'WBC Rest'

        self.register_widget(Select(title="List of Views", options=list(self.views), value='WBC Rest'), 'views',  ['value'])


    def compose_tables(self):
        pass

    def compose_widgets(self):
        pass


    def update_widgets(self):
        pass

    def update_tables(self):
        self.table = self.ui_elements['views'].value
        print(self.table)
        pass

    def compose_panel(self):
        layout = Row(self.compose_widgets(), Spacer(width=30), self.compose_tables(), sizing_mode="stretch_both")
        
        panel = Panel(child=layout, title="BloodTests")

        self.update_widgets()        
        self.update_tables()

        return panel


    def update(self,attr,old,new):
        print('Update: ')
        print(attr)
        print(old)
        print(new)
        print('-----------------')
        self.update_widgets()        
        self.update_tables()
        print('Finished')

    def register_widget(self,widget,widget_name,actions_to_respond_to):
        """
        Parameters:
        widget (object): the widget to register
        widget_name (str): the name under which to register it
        actions_to_respond_to (list): the list of actions which need to trigger update
        """
        assert widget_name not in self.ui_elements, "UI element %s has already been registered" % (widget_name)              
        self.ui_elements[widget_name] = widget
        for action in actions_to_respond_to:
            self.ui_elements[widget_name].on_change(action, self.update)



