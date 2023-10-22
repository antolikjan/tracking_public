import pandas as pd
from bokeh.models import ColumnDataSource, DataTable, TableColumn, HTMLTemplateFormatter, DateFormatter, Select, Column, Row, Div
from scripts.ui_framework.analysis_panel import AnalysisPanel



class BloodTests(AnalysisPanel):
    def __init__(self, data, categories, metadata, title):

        """
        Initialize the BloodTests analysis panel.

        Args:
            data (dict): Data for the analysis panel.
            categories (list): List of categories.
            metadata (pandas.DataFrame): Metadata information.
            title (str): Title of the panel.
        """

        AnalysisPanel.__init__(self,data, categories, metadata, title)

        # Get the views of the bloodtest record
        self.views = data.keys()

        # Create a dropdown widget to select different views
        self.register_widget(Select(title="List of Views", options=list(self.views), value='WBC Rest'), 'views',  ['value'])

        
        self.table = 'WBC Rest'   # Initial (default) view
        # Create a data source for the initial view
        self.data_sources[self.table] = self.raw_data[self.table]
        # Create columns for the DataTable widget based on the selected view
        self.columns = self.create_columns(self.raw_data[self.table])
        
        # Create a DataTable widget with the selected data source and columns
        self.plots[self.table] = DataTable(source=ColumnDataSource(data=self.data_sources[self.table]), columns=self.columns, width=1400, height=1000)

        # Create a layout for the DataTable
        self.plot_layout = Column(self.plots[self.table])
        
    def compose_widgets(self):
        """
        Compose the layout of widgets for the panel
        """
        # dropdown of views
        dropdown = Column(Div(text=""" """),self.ui_elements["views"], sizing_mode="fixed", width=120,height=500)  
        widget = Row(dropdown, width=240)
        return widget

    def compose_plots(self):
        """
        Compose the layout of plots for the panel
        """

        return self.plot_layout

    def create_columns(self, data):
        """
        Create DataTable columns based on the provided data.

        Args:
            data (pandas.DataFrame): The data from which columns are generated.

        Returns:
            list: A list of DataTable columns.
        """

        columns = []

        # Add the "Date" column as the first TableColumn
        columns.append(TableColumn(field="index", title="Date", formatter=DateFormatter()))

        no_data_for_column = False

        for col in data.columns:
            column_with_data = data[col]

            color_map = {}

            # Iterate through the entries in the current column
            for entry in column_with_data:
                # Skip the entries that are NaN or [object] values
                if pd.isna(entry) or not (isinstance(entry, float) or isinstance(entry, int)):
                    continue
                
                # Determine the cell color using the color_mapper function
                cell_color = color_mapper(self.metadata, entry, col)
                
                # Check if the cell_color is 'NA', indicating no data
                if cell_color == 'NA':
                    no_data_for_column = True
                        # Add a column with a cell template for no data
                    columns.append(TableColumn(field=col, title=col, formatter=HTMLTemplateFormatter(template = '<div style="background-color: "#FFFFFF" ;"> </div>')))
                    break

                if cell_color in color_map:
                    color_map[cell_color].add(entry)
                else:
                    color_map[cell_color] = {entry}

            if no_data_for_column:
                no_data_for_column = False
                continue

            # Create a cell template for the DataTable
            # modifying only the entries that have more than 4 digits after the decimal point
            template_js = '<% var clr; var formatted_value = value; if (typeof value === "number" && !Number.isInteger(value) && value.toString().includes(".")) { var decimalPartLength = value.toString().split(".")[1].length; if (decimalPartLength > 4) { formatted_value = Number(value).toFixed(4); } }'
            template_if_line = 'if (value >= {} && value <= {}) clr = "{}"; '

            for color, value_list in color_map.items():
                template_js += template_if_line.format(min(value_list), max(value_list), color)
            # NaN entries should not be colored
            template_js += '%> <div style="background-color: <%- clr %>;"> <% if (isNaN(formatted_value)) { %> <% formatted_value = "" %> <% } %> <%- formatted_value %> </div>'

            # Combine all the javascript templates to make a cell formater
            cell_formatter = HTMLTemplateFormatter(template=template_js)

            # Add the column with cell formatting to the list of columns
            columns.append(TableColumn(field=col, title=col, formatter=cell_formatter))

        return columns


    def update_widgets(self):
        """
        Update widget options based on user selections
        """
        self.table = self.ui_elements['views'].value

    def update_data(self):
        """
        Update data for analysis based on changes in widgets.
        """

        self.table = self.ui_elements['views'].value
        new_data = self.raw_data[self.table]

        # Check if the selected view is already in data_sources. If not, add it.
        if self.table not in self.data_sources:
            self.data_sources[self.table] = new_data

        # Update the data of the DataTable widget with the new data
        self.data_sources[self.table].data = new_data

    def update_plots(self):
        """
        Update the DataTable widget displayed in the analysis panel.

        This method is called when there are changes in the selected view using the 'views' widget. 
        It updates the DataTable widget with the data associated with the selected view.
        """

        self.table = self.ui_elements['views'].value
        # Create new columns for the DataTable based on the data from the selected view
        self.columns = self.create_columns(self.raw_data[self.table])

        # Create a new DataTable widget with the updated data and columns
        self.plots[self.table] = DataTable(source=ColumnDataSource(data=self.data_sources[self.table]), 
                                            columns=self.columns, 
                                            width=1400, 
                                            height=1000)
        # Update the layout object to display the new DataTable
        self.plot_layout.children = [self.plots[self.table]]



def compare(x, opt_min, opt_max, norm_min, norm_max):
    """
    Compare a value 'x' to specified ranges and classify it.

    This function compares the value 'x' to specified optimal and normal ranges and classifies it into one of the following categories:
    1 - Within the optimal range.
    2 - Within the normal range but outside the optimal range.
    3 - Outside both the optimal and normal ranges.


    Returns:
    int: An integer representing the category to which 'x' belongs.
    """
    if opt_min<=x<=opt_max:
        return 1
    elif norm_min<=x<=norm_max:
        return 2
    else:
        return 3


def classify_range(metadata, marker, col):

    """
    Classify a marker value based on provided metadata and defined ranges.

    This function takes a marker value, metadata, and a column name and classifies the marker value into different
    categories based on the defined optimal and normal ranges in the metadata.

    Args:
    metadata (pandas.DataFrame): Metadata information.
    marker (str or float): The value to be classified.
    col (str): The name of the column in the metadata corresponding to the marker.

    Returns:
    str: The classification of the marker value into one of the following categories:
        - "NaN" if marker is a NaN or "NaN" string.
        - "NA" if there is no relevant metadata information.
        - 1 if the marker falls within the normal range.
        - 2 if the marker falls within the optimal range.
        - 3 if the marker is outside both the optimal and normal ranges.
    """
    
    if marker == "NaN" or pd.isna(marker):
        return "NaN"

    # Convert marker (non-NaN) to a floating-point number
    marker = float(marker)
    try: 
        # Extract optimal and normal range values from the metadata
        norm_min = pd.to_numeric(metadata.loc[col, 'Normal value min'], errors='coerce')
        norm_max = pd.to_numeric(metadata.loc[col, 'Normal value max'], errors='coerce')

        opt_min = pd.to_numeric(metadata.loc[col, 'Optimal value min'], errors='coerce')
        opt_max = pd.to_numeric(metadata.loc[col, 'Optimal value max'], errors='coerce')
    

    except:
        # Handle errors in metadata retrieval
        print(f'There is no data for the marker "{col}" in metadata')
        return "NA"


    # Check if any of the range indicators is not present
    if pd.isna(norm_min) or pd.isna(norm_max) or pd.isna(opt_min) or pd.isna(opt_max):  
        # Classify based on available range indicators
        if not pd.isna(opt_min):
            # Classify based on the optimal range
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
            # Handle cases where opt_min is NaN
            if not pd.isna(opt_max):
                # Handle cases where opt_max is not NaN
                if not pd.isna(norm_min) and not pd.isna(norm_max):
                    return compare(marker, opt_min=norm_min, opt_max=opt_max, norm_min=norm_min, norm_max=norm_max)

                # Handle cases where norm_min is not NaN
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
    # Handle cases where all range indicators are present
    else:
        return compare(marker, opt_min, opt_max, norm_min, norm_max)
   
   

def color_mapper(metadata, col_name, cell_value):
    """
    Map a cell value to a color based on the classified range value.

    Args:
    metadata (pandas.DataFrame): Metadata information.
    col_name (str): The name of the column in the metadata corresponding to the cell value.
    cell_value (str or float): The cell value to be classified and mapped to a color.

    """

    range_value = classify_range(metadata, col_name, cell_value)
    color_code = {1: '#2fd01a',  # Green
                  2: '#f6e741',  # Yellow
                  3: '#fb3232',  # Red
                  "NA" : 'NA'}  
    return color_code.get(range_value, '#EADDCA')  # Default to light brown if not found
