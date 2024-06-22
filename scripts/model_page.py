from functools import partial
from bokeh.models import Panel,ColumnDataSource, Row, Column, TableColumn, DataTable, Button, Div
from datetime import datetime
from datetime import date
import time

#NOTE: the ui is currently implemented as adding elements to a dict.
#in future i should reimplement this, adhering to the software design of previous UI pages

ui = {}

def model_started(data,metadata):
    print('Starting Model')

def compose_panel(data,metadata):
    
    ui['button1'] = Button(label="Start Model", button_type="success",width=200) 
    ui['button1'].on_click(partial(model_started,data=data,metadata=metadata))
 
    panel = Panel(child=Row(Column(ui['button1'])), title="Model Page")
    return panel

