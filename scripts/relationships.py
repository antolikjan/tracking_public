from functools import partial
from bokeh.plotting import figure
from bokeh.models.widgets import Panel
from bokeh.models import ColumnDataSource, Row, Column, TableColumn, DataTable, Button
from scripts.data import both_valid
from datetime import datetime
from datetime import date

ui = {}

def filter_ignored(source,relationships):
    print('Starting filtering')
    source.data = relationships.rm[relationships.rm.IgnoreList==True]
    print('Finished filtering')
    

def filter_blacklisted(source,relationships):
    print('Starting filtering')
    source.data = relationships.rm[relationships.rm.BlackList==True]
    print('Finished filtering')

def remove_from_blacklist(source,relationships):
    for idx in source.selected.indices:
        relationships.remove_from_blacklist(source.data['Var1'][idx],source.data['Var2'][idx])    

def remove_from_ignorelist(source,relationships):
    for idx in source.selected.indices:
        relationships.remove_from_ignorelist(source.data['Var1'][idx],source.data['Var2'][idx])    


def panel(relationships):

    source = ColumnDataSource(relationships.rm)

    columns = [
        TableColumn(field="Var1"),
        TableColumn(field="Var2"),
        TableColumn(field="IgnoreList"),
        TableColumn(field="BlackList"),
    ]

    data_table = DataTable(source=source, columns=columns,sizing_mode="stretch_both",height=700)
          
    ui['button1'] = Button(label="Show Ignored", button_type="success",width=200) 
    ui['button1'].on_click(partial(filter_ignored,source=source,relationships=relationships))

    ui['button2'] = Button(label="Show Blacklisted", button_type="success",width=200) 
    ui['button2'].on_click(partial(filter_blacklisted,source=source,relationships=relationships))

    ui['button3'] = Button(label="Remove from Ignored", button_type="success",width=200) 
    ui['button3'].on_click(partial(remove_from_ignorelist,source=source,relationships=relationships))

    ui['button4'] = Button(label="Remove from Blacklist", button_type="success",width=200) 
    ui['button4'].on_click(partial(remove_from_blacklist,source=source,relationships=relationships))

 
    panel = Panel(child=Row(Column(ui['button1'],ui['button2'],ui['button3'],ui['button4']),data_table,sizing_mode="stretch_both"), title="Relationships")

    return panel
