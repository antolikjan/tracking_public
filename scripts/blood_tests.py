import pandas as pd
from bokeh.models import ColumnDataSource, DataTable, TableColumn, HTMLTemplateFormatter, DateFormatter, Select, Column, Row, Div, CustomJS

from scripts.ui_framework.analysis_panel import AnalysisPanel


class BloodTests(AnalysisPanel):
    def __init__(self, data, categories, metadata, title):
        AnalysisPanel.__init__(self,data, categories, metadata, title)
        self.views = data.keys()

        self.register_widget(Select(title="List of Views", options=list(self.views), value='WBC Rest'), 'views',  ['value'])
        self.table = 'WBC Rest'
        self.plots[self.table] = self.compose_table(self.table)
        
      
        
    def compose_widgets(self):
        dropdown = Column(Div(text=""" """),self.ui_elements["views"], sizing_mode="fixed", width=120,height=500)  
        widg = Row(dropdown, width=240)
        return widg

    def compose_plots(self):
        return Column(self.plots[self.table])

    def compose_table(self,view):
        data = self.raw_data[view]
        

        columns = []
        for col in data.columns:
            column_with_data = data[col]

            color_map = {}
            for entry in column_with_data:
                if pd.isna(entry) or not (isinstance(entry, float) or isinstance(entry, int)):
                    continue

                cell_color = color_mapper(self.metadata, entry, col)
                if cell_color in color_map:
                    color_map[cell_color].add(entry)
                else:
                    color_map[cell_color] = set([entry])

            template_js = "<% var clr;"
            template_if_line = 'if (value >= {} && value <= {}) clr = "{}"; '

            for color, value_list in color_map.items():
                template_js += template_if_line.format(min(value_list), max(value_list), color)
            
            template_js += '%> <div style="background-color: <%- clr %>;"> <%- value%> </div>'


            cell_formatter = HTMLTemplateFormatter(template=template_js)
            columns.append(TableColumn(field=col, title=col, formatter=cell_formatter))



        source = ColumnDataSource(data=data)
        table = DataTable(source=source, columns=columns, width=1400, height=1000)

        return table


    def update_plots(self):
        self.plots.clear()
        self.plots[self.table] = self.compose_table(self.table)
        # self.plots['WBC Rest'].visible = False

        

    def update_widgets(self):
        self.table = self.ui_elements['views'].value
        

def compare(x, opt_min, opt_max, norm_min, norm_max):
    if opt_min<=x<=opt_max:
        return 1
    elif norm_min<=x<=norm_max:
        return 2
    else:
        return 3


def classify_range(metadata, marker, col):
    
    if marker == "NaN" or pd.isna(marker):
        return "NaN"

    marker = float(marker)
    norm_min = pd.to_numeric(metadata.loc[col, 'Normal value min'], errors='coerce')
    norm_max = pd.to_numeric(metadata.loc[col, 'Normal value max'], errors='coerce')

    opt_min = pd.to_numeric(metadata.loc[col, 'Optimal value min'], errors='coerce')
    opt_max = pd.to_numeric(metadata.loc[col, 'Optimal value max'], errors='coerce')
  
    
    if pd.isna(norm_min) or pd.isna(norm_max) or pd.isna(opt_min) or pd.isna(opt_max):    # any of the range indicators is not present

        # 1) optimal min. is not a NaN value
        if not pd.isna(opt_min):
            if not pd.isna(opt_max) and not pd.isna(norm_min):
                return compare(marker, opt_min, opt_max, norm_min, norm_max=opt_max)
            elif not pd.isna(opt_max) and not pd.isna(norm_max):
                return compare(marker, opt_min, opt_max, norm_min=opt_min, norm_max=norm_max)
            elif not pd.isna(norm_min) and not pd.isna(norm_max):
                return compare(marker, opt_min, opt_max=norm_max, norm_min=norm_min, norm_max=norm_max)
            

            elif not pd.isna(opt_max) and pd.isna(norm_min) and pd.isna(norm_max):
                if opt_min<=marker<=opt_max:
                    return 1
                else:
                    return 3
            elif not pd.isna(norm_min) and pd.isna(opt_max) and pd.isna(norm_max):
                if marker<opt_min:
                    return 3
                elif marker<norm_min:
                    return 2
                else:
                    return 1
            elif not pd.isna(norm_max) and pd.isna(opt_max) and pd.isna(norm_min):    # if marker is in range (opt_min, norm_max) - then normal 
                if opt_min<=marker<=norm_max:
                    return 2
                else: 
                    return 3

            
            elif pd.isna(opt_max) and pd.isna(norm_min) and pd.isna(norm_max):
                if marker<=opt_min:
                    return 1 
                else:
                    return 3
        # opt_min is a NaN value
        else:
            # 2) opt_max is not a NaN value
            if not pd.isna(opt_max):
                if not pd.isna(norm_min) and not pd.isna(norm_max):
                    return compare(marker, opt_min=norm_min, opt_max=opt_max, norm_min=norm_min, norm_max=norm_max)
                elif not pd.isna(norm_min) and pd.isna(norm_max):
                    if norm_min<=marker<=opt_max:         # in range (norm_min, opt_max) -> normal
                        return 2
                    else:
                        return 3
                elif pd.isna(norm_min) and not pd.isna(norm_max):
                    if marker <= opt_max:
                        return 1 
                    elif marker <= norm_max:
                        return 2
                    else:
                        return 3 
                else:
                    if marker <= opt_max:
                        return 1
                    else: 
                        return 3

            else: 
                if not pd.isna(norm_min) and not pd.isna(norm_max):
                    if norm_min<=marker<=norm_max:
                        return 2
                    else:
                        return 3
                elif not pd.isna(norm_min) and pd.isna(norm_max):
                    if marker>=norm_min:
                        return 2
                    else:
                        return 3
                elif pd.isna(norm_min) and not pd.isna(norm_max):
                    if marker <= norm_max:
                        return 2
                else:
                    return 3

    else:      #if every indicator is present, proceed 
        return compare(marker, opt_min, opt_max, norm_min, norm_max)
   

def color_mapper(metadata, col_name, cell_value):
    range_value = classify_range(metadata, col_name, cell_value)
    color_code = {1: '#008000',  # Green
                  2: '#FFFF00',  # Yellow
                  3: '#FF0000'}  # Red
    return color_code.get(range_value, '#FFFFFF')  # Default to White if not found
