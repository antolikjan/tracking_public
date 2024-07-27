from functools import partial
from bokeh.models import Panel, Column, Row, Button, Div, ColumnDataSource, LinearColorMapper, ColorBar, Range1d, RangeTool, Spacer, Select
from bokeh.io import curdoc
from bokeh.plotting import figure
from bokeh.transform import linear_cmap
from bokeh.layouts import row, column
import numpy as np
import torch
import time

from model.model_code import *
from model.pretrainedweightsalphas import *

toTrain = False  # When set to False --> it won't be training the model. Set to False for debugging reasons with weights and alphas stored in variables

class ModelPage:
    def __init__(self, data, metadata, categories):
        self.data = data
        self.metadata = metadata
        self.categories = categories
        self.ui_elements = {}
        self.dynamic_col = Column()
        self.weight_on_select, self.weight_on_tap, self.alpha_on_select, self.alpha_on_tap = self.create_bar_plots()
        self.current_bar_plot_select = None
        self.current_alpha_bar_plot_select = None

        self.current_bar_plot_tap = None
        self.current_alpha_bar_plot_tap=None
        self.create_ui_elements()

    def create_ui_elements(self):
        # Create "Select Category" and "Select Name" widgets
        self.ui_elements['select_category'] = Select(title="Category", options=list(self.categories.keys()), value='Fitbit')
        self.ui_elements['select_name'] = Select(title='Name', value='DistanceFitbit', options=list(self.categories['Fitbit']))

        # Update "Name" options based on selected "Category"
        self.ui_elements['select_category'].on_change('value', self.update_name_options)

        # Create "Show Bar Plot" button
        self.ui_elements['show_bar_plot'] = Button(label="Show Bar Plot", button_type="success", width=200)
        self.ui_elements['show_bar_plot'].on_click(self.show_bar_plot)

        self.ui_elements['button1'] = Button(label="Start Model", button_type="success", width=200)
        self.ui_elements['button1'].on_click(partial(self.model_started, data=self.data, metadata=self.metadata))
        self.dynamic_col.children.append(self.ui_elements['button1'])

        self.loader = Div(text="", width=200, height=30)
        self.dynamic_col.children.append(self.loader)

    def update_name_options(self, attr, old, new):
        self.ui_elements['select_name'].options = list(self.categories[new])

    def show_bar_plot(self):
        selected_name = self.ui_elements['select_name'].value
        if selected_name in self.weight_on_select:
            bar_plot = self.weight_on_select[selected_name]
            alpha_bar_plot=self.alpha_on_select[selected_name]

            # Safely remove the current bar plot if it exists in any row
            if self.current_bar_plot_select:
                for child in self.dynamic_col.children:
                    if isinstance(child, Row):
                        if self.current_bar_plot_select in child.children:
                            child.children.remove(self.current_bar_plot_select)
                        if self.current_alpha_bar_plot_select in child.children:
                            child.children.remove(self.current_alpha_bar_plot_select)
            # self.current_bar_plot_select = None
            # self.current_alpha_bar_plot_select = None

            self.current_bar_plot_select = bar_plot
            self.current_alpha_bar_plot_select = alpha_bar_plot
            self.dynamic_col.children.append(row(bar_plot, alpha_bar_plot))

    def create_bar_plots(self):
        # Convert weights to numpy array and take absolute values
        weights_converted_to_array = weights_result.detach().numpy()
        weights_converted_to_array_absolute = np.absolute(weights_converted_to_array)

        alphas_result_converted_to_array = alphas_result.detach().numpy()
        alphas_converted_to_array_absolute = np.absolute(alphas_result_converted_to_array)

        weight_on_select = {}
        weight_on_tap = {}
        alpha_on_select = {}
        alpha_on_tap = {}
        for idx, column_name in enumerate(columns):
            # Extract weights for the current column
            weights_column = weights_converted_to_array_absolute[:, idx]

            # Sort weights and columns together
            sorted_indices = np.argsort(weights_column)[::-1]
            sorted_weights = weights_column[sorted_indices]
            sorted_columns = [columns[i] for i in sorted_indices]

            # Define the colorscale for the heatmap
            colors_reversed = ['#F9F871', '#A2F07F', '#49D869', '#1EA087', '#277F8E', '#365A8C', '#46327E', '#440154']
            mapper = linear_cmap(field_name='top', palette=colors_reversed, low=sorted_weights.min(), high=sorted_weights.max())

            # Create the figure
            p = figure(x_range=sorted_columns, title=f"{column_name} influenced by...", plot_width=675, plot_height=600, tools="hover,save,reset")

            # Plot the bar plot
            p.vbar(x=sorted_columns, top=sorted_weights, width=0.8, fill_color=mapper)
            p.xaxis.major_label_orientation = np.pi / 2
            p.y_range.start = 0

            # Add color bar
            color_bar = ColorBar(color_mapper=mapper['transform'], width=8, location=(0, 0))
            p.add_layout(color_bar, 'right')

            # Add hover tool
            p.hover.tooltips = [("Column", "@x"), ("Value", "@top")]

            # Create spacers for centering
            spacer_left = Spacer(width=0)

            # Create a centered layout for the plot
            layout = row(spacer_left, p)

            weight_on_select[column_name] = layout

            ##ALPHAS
            print(sorted_columns)
            #sorted_columns = list(self.alpha_on_tap[column_name[0]+"on_tap"]) #dummy default --> doesnt work it was previouslu columnnames[0] or somethiong like that therefore "Sys_Diaon_tap"
            print(f"initial print of sorted columns: {sorted_columns}")
            alphas_barplot = figure(x_range=sorted_columns, height=600, width=675, title="Alphas", tools="hover")
            alphas_barplot.vbar(x=sorted_columns, top=[alphas_converted_to_array_absolute[sorted_columns.index(col)] for col in sorted_columns], width=0.8)

            alphas_barplot.hover.tooltips = [("Column", "@x"), ("Value", "@top")]

            alphas_barplot.xgrid.grid_line_color = None
            alphas_barplot.xaxis.major_label_orientation = np.pi / 2
            alphas_barplot.y_range.start = 0
            ###

            layput_alpha = alphas_barplot
            

            alpha_on_select[column_name] = layput_alpha

            custom_column_name = column_name + "on_tap"
            weight_on_tap[custom_column_name] = layout

            alpha_on_tap[custom_column_name] = layput_alpha

        return weight_on_select, weight_on_tap, alpha_on_select, alpha_on_tap

    def compose_panel(self):
        panel = Panel(child=self.dynamic_col, title="Model Page")
        return panel

    def model_started(self, data, metadata):
        print('Model Called')
        self.loader.text = "Model is starting..."  # Show loading message
        curdoc().add_next_tick_callback(partial(self.run_model_callback, data, metadata))

    def run_model_callback(self, data, metadata):
        if toTrain:
            print("Training started...")
            column_names, weights, alphas = run_model(data, metadata)
        else:
            weights = weights_result
            alphas = alphas_result
            column_names = columns
            time.sleep(3)

        self.loader.text = "Done!"

        np.set_printoptions(threshold=10_000)
        torch.set_printoptions(threshold=10_000)

        weights_converted_to_array = weights.detach().numpy()
        weights_converted_to_array_absolute = np.absolute(weights_converted_to_array)

        column_names_converted_to_list = column_names.tolist()

        column_names = column_names_converted_to_list  # List of column names
        weights_matrix = weights_converted_to_array_absolute  # ALERT: THIS IS THE WEIGHT MATRIX CONVERTED TO ABSOLUTE VALUES

        # Create a list of row names (assuming row names are the same as column names)
        row_names = column_names

        # Prepare data for Bokeh ColumnDataSource
        data = {'y': np.repeat(range(len(column_names)), len(row_names)),
                'x': np.tile(range(len(row_names)), len(column_names)),
                'values': weights_matrix.flatten(),
                'x_labels': np.tile(row_names, len(row_names)),
                'y_labels': np.repeat(column_names, len(column_names))
                }

        source = ColumnDataSource(data)
        detailed_source = ColumnDataSource(data.copy())  # Separate source for the detailed view

        # Define the colorscale for the heatmap
        colors_reversed = ['#F9F871', '#A2F07F', '#49D869', '#1EA087', '#277F8E', '#365A8C', '#46327E', '#440154']

        mapper = linear_cmap(field_name='values', palette=colors_reversed, low=weights_matrix.min(), high=weights_matrix.max())

        # Create the main heatmap figure with Range1d for x_range and y_range
        row_names_list = row_names.tolist() if hasattr(row_names, 'tolist') else list(row_names)
        column_names_list = column_names.tolist() if hasattr(column_names, 'tolist') else list(column_names)

        p = figure(title="Neural Network Weights Heatmap", 
                   x_range=row_names_list, 
                   y_range=column_names_list, 
                   plot_width=800, 
                   plot_height=600, 
                   tools="hover,save,reset", 
                   toolbar_location='above')

        # Plot the heatmap
        r = p.rect(x='x', y='y', width=0.8, height=0.9, source=source, fill_color=mapper, line_color=None)

        # Add color bar
        color_bar = ColorBar(color_mapper=mapper['transform'], width=8, location=(0, 0))
        p.add_layout(color_bar, 'right')

        p.xaxis.major_label_orientation = np.pi / 4

        # Add hover tool
        p.hover.tooltips = [("Row, Column", "@y_labels, @x_labels"), ("Value", "@values")]

        # Create a detailed view figure
        detailed_view = figure(title="Detailed View", plot_width=600, plot_height=600,
                               x_range=Range1d(0, 15), y_range=Range1d(0, 15),
                               tools="hover,save,reset,tap", toolbar_location='above')

        r_detailed = detailed_view.rect(x='x', y='y', width=0.8, height=0.9, source=detailed_source, fill_color=mapper, line_color=None)

        # Disable selection visual effects
        r.selection_glyph = None
        r.nonselection_glyph = None
        r_detailed.selection_glyph = None
        r_detailed.nonselection_glyph = None

        # Add a RangeTool to the main heatmap
        range_tool = RangeTool(x_range=detailed_view.x_range, y_range=detailed_view.y_range)
        range_tool.overlay.fill_color = "navy"
        range_tool.overlay.fill_alpha = 0.2

        p.add_tools(range_tool)
        p.toolbar.active_multi = range_tool

        # Callback to update the detailed view based on selected range
        def update_detailed_view(attr, old, new):
            min_x = int(round(detailed_view.x_range.start))
            max_x = int(round(detailed_view.x_range.end))
            min_y = int(round(detailed_view.y_range.start))
            max_y = int(round(detailed_view.y_range.end))

            # Ensure indices are within valid range
            min_x = max(min_x, 0)
            max_x = min(max_x, len(row_names))
            min_y = max(min_y, 0)
            max_y = min(max_y, len(column_names))

            # Filter the data for the detailed view
            detailed_data = {
                'x': np.tile(range(min_x, max_x), max_y - min_y),
                'y': np.repeat(range(min_y, max_y), max_x - min_x),
                'values': weights_matrix[min_y:max_y, min_x:max_x].flatten(),
                'x_labels': np.tile(row_names[min_x:max_x], max_y - min_y),
                'y_labels': np.repeat(column_names[min_y:max_y], max_x - min_x)
            }
            detailed_source.data = detailed_data

        # Attach the callback to the range changes
        detailed_view.x_range.on_change('start', update_detailed_view)
        detailed_view.x_range.on_change('end', update_detailed_view)
        detailed_view.y_range.on_change('start', update_detailed_view)
        detailed_view.y_range.on_change('end', update_detailed_view)

        detailed_view.hover.tooltips = [
            ("Row Label", "@y_labels"),
            ("Column Label", "@x_labels"),
            ("Value", "@values")
        ]

        # TapTool callback
        def on_tap(event):
            indices = detailed_source.selected.indices
            if indices:
                index = indices[0]
                column_name = detailed_source.data['x_labels'][index] + "on_tap"
                print(f"Clicked cell - Row: {detailed_source.data['y_labels'][index]}, Column: {column_name}")

                print("Children before removal:", len(self.dynamic_col.children))
                # Safely remove the current bar plots if they exist
                if self.current_bar_plot_tap:
                    # Iterate through children to safely remove existing plots
                    for child in self.dynamic_col.children:
                        if isinstance(child, Row):
                            # Check if the current bar plots are in the child
                            if self.current_bar_plot_tap in child.children:
                                child.children.remove(self.current_bar_plot_tap)
                            if self.current_alpha_bar_plot_tap in child.children:
                                child.children.remove(self.current_alpha_bar_plot_tap)

                # Clear references to ensure they aren't reused
                self.current_bar_plot_tap = None
                self.current_alpha_bar_plot_tap = None
                #self.current_alpha_bar_plot_select = None
                # Removal logic here
                print("Children after removal:", len(self.dynamic_col.children))

                # Check if the column is in weight_on_tap
                if column_name in self.weight_on_tap:
                    self.current_bar_plot_tap = self.weight_on_tap[column_name]
                    self.current_alpha_bar_plot_tap = self.alpha_on_tap[column_name]

                    # Update the layout to include the new plots in the correct location
                    self.dynamic_col.children.append(
                        row(self.current_bar_plot_tap, self.current_alpha_bar_plot_tap),  # Show detailed view and alpha plot
                    )

        # Assign the tap event handler
        detailed_view.on_event('tap', on_tap)
        
        # Use a row layout to place the heatmap and detailed view side by side
        self.dynamic_col.children.append(row(p, detailed_view))

        spacer_left = Spacer(width=100)
        #self.dynamic_col.children.append(row(spacer_left, alphas_barplot))


        ###ADD SELECTION&BUTTON UI ELEMENTS###
        self.dynamic_col.children.append(column(
            self.ui_elements['select_category'], 
            self.ui_elements['select_name'], 
            self.ui_elements['show_bar_plot']
        ))
        ###
