from datetime import datetime
from re import template
from bokeh.core.properties import Color
from turtle import color, title, width
from bokeh.models import ColumnDataSource, DataTable, TableColumn, HTMLTemplateFormatter, DateFormatter
from scripts.data import load_blood_tests
from scripts.airtable import airtable_download , convert_to_dataframe
import pandas as pd
from bokeh.models.widgets import Panel

def create_blood_tests_table(df):
    data = convert_to_dataframe(airtable_download('BloodTest', api_key='keyBQivgbhrgIZQS9', base_id='appL3Wb1C7NvHTDl1'), index_column="Date", datatime_index=True)
    data.sort_index(inplace=True)

    md = convert_to_dataframe(airtable_download('Metadata',api_key='keyBQivgbhrgIZQS9',base_id='appL3Wb1C7NvHTDl1'),index_column="Name")
    md['Start of valid records'] = pd.to_datetime(md['Start of valid records'])


    # table_data = pd.DataFrame(columns=['Date'] + list(data.columns))
    table_data = data.copy()
    table_data['Date'] = pd.to_datetime(table_data.index, unit='ms')  # Convert Unix timestamps to readable dates


    columns = [TableColumn(field='Date', title='Date', width=200, formatter=DateFormatter(format='%Y-%m-%d %H:%M:%S'))]
 
    cell_formatter = HTMLTemplateFormatter(
        template='<div class="nan-cell" style="background-color:<%= value === "NaN" ? "#F9F2D1" : "inherit" %>;"><%= value %></div>'
    )


    for col in data.columns:
        # new_col_name = col
        # new_col = update_column(col, data, md)
        # # table_data[new_col_name] = data[col].apply(lambda x: update_entry(x, md, col))
        # table_data[new_col_name] = new_col

        # columns.append(TableColumn(field=new_col_name, title=new_col_name))
        columns.append(TableColumn(field=col, title=col, formatter=cell_formatter))

    source = ColumnDataSource(table_data)
    table = DataTable(source=source, columns=columns, width=1400, height=1000)

    panel = Panel(child=table, title="Blood Tests")
    return panel


def update_column(col, data, metadata):
    new_column = []

    for entry in data[col]:
        print(f'checking the entry: {entry}')
        range_par = classify_range(metadata, entry, col)
        if range_par == 1:
            new_column.append(f'{entry} - N')
            # new_column.append("TRK")
        elif range_par == 2:
            new_column.append(f'{entry} - O')
        elif range_par == 3:
            new_column.append(f'{entry} - B')
        elif range_par == "NaN":
            new_column.append(str(entry)    )

    # return ', '.join(new_column)
    return new_column


def update_entry(entry, metadata, col):
    range_par = classify_range(metadata, entry, col)
    
    if range_par == 1:
        return f'{entry} - N'
        # return 'N'
    elif range_par == 2:
        return f'{entry} - O'
    elif range_par == 3:
        return f'{entry} - B'
    else:
        return entry

def classify_range(metadata, marker, col):

    # print(f'marker is: {marker}')
    if marker == "NaN" or pd.isna(marker):
        return "NaN"
    marker = float(marker)
    norm_min = pd.to_numeric(metadata.loc[col, 'Normal value min'], errors='coerce')
    norm_max = pd.to_numeric(metadata.loc[col, 'Normal value max'], errors='coerce')
    # print(f'normal min: {norm_min}')
    # print(f'normal max: {norm_max}')

    opt_min = pd.to_numeric(metadata.loc[col, 'Optimal value min'], errors='coerce')
    opt_max = pd.to_numeric(metadata.loc[col, 'Optimal value max'], errors='coerce')
    # print(f'optimal min: {opt_max}')
    # print(f'optimal min: {opt_min}')

    value = ''
    if pd.isna(norm_min) or pd.isna(norm_max) or pd.isna(opt_min) or pd.isna(opt_max):    # any of the range indicators is not present

        if pd.isna(opt_min) and not pd.isna(opt_max) and not pd.isna(norm_min) and not pd.isna(norm_max):  
            if norm_min <= marker <= opt_max: 
                value = 1 
            elif opt_max < marker <= norm_max:
                value = 2 
            else:
                value = 3

        if pd.isna(opt_max) and not pd.isna(opt_min) and not pd.isna(norm_min) and not pd.isna(norm_max):
            if opt_min <= marker <= norm_max:
                value = 1
            elif norm_min <= marker < opt_min:
                value = 2 
            else: 
                value = 3 


        # if any of the normal range indicators is missing:
        # if pd.isna()

    else:      #if every indicator is present, proceed 

        if opt_min <= marker <= opt_max:
            value = 1
        elif norm_min <= marker <= norm_max:
            value = 2
        else:
            value = 3

    return value

# def cell_template(val):
#     color_val = classify_range(val)
#     if color_val == 1:
#         color = 'green'
#     elif color_val == 2:
#         color = 'orange'
#     else:
#         color = 'red'
    
#     return f'<div style="background-color: {color}">{val}</div>'