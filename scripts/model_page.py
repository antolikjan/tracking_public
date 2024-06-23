from functools import partial
from bokeh.models import Panel, Column, Button, Div, ColumnDataSource, LinearColorMapper, ColorBar, Range1d, RangeTool
from bokeh.io import curdoc
from bokeh.plotting import figure
from bokeh.transform import linear_cmap
import numpy as np
import torch
import time

# Assume the following imports are present and the model functions are defined elsewhere
from model.model_code import *
from model.pretrainedweightsalphas import *

toTrain = False  # When set to False --> it won't be training the model. Set to False for debugging reasons with weights and alphas stored in variables

class ModelPage:
    def __init__(self, data, metadata):
        self.data = data
        self.metadata = metadata
        self.ui_elements = {}
        self.dynamic_col = Column()
        self.create_ui_elements()

    def create_ui_elements(self):
        self.ui_elements['button1'] = Button(label="Start Model", button_type="success", width=200)
        self.ui_elements['button1'].on_click(partial(self.model_started, data=self.data, metadata=self.metadata))
        self.dynamic_col.children.append(self.ui_elements['button1'])

        self.loader = Div(text="", width=200, height=30)
        self.dynamic_col.children.append(self.loader)

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

        print("---")
        weights_converted_to_array = weights.detach().numpy()
        weights_converted_to_array_absolute = np.absolute(weights_converted_to_array)

        print("---")
        alphas_result_converted_to_array = alphas.detach().numpy()
        alphas_converted_to_array_absolute = np.absolute(alphas_result_converted_to_array)

        print("---")
        column_names_converted_to_list = column_names.tolist()

        column_names = column_names_converted_to_list  # List of column names
        weights_matrix = weights_converted_to_array_absolute  # ALERT: THIS IS THE WEIGHT MATRIX CONVERTED TO ABSOLUTE VALUES

        # Create a list of row names (assuming row names are the same as column names)
        row_names = column_names

        # Prepare data for Bokeh ColumnDataSource
        data = {'y': np.repeat(range(len(column_names)), len(row_names)),
                'x': np.tile(range(len(row_names)), len(column_names)),
                'values': weights_matrix.flatten()}

        source = ColumnDataSource(data)
        detailed_source = ColumnDataSource(data.copy())  # Separate source for the detailed view

        # Define the colorscale for the heatmap
        colors_reversed = ['#F9F871', '#A2F07F', '#49D869', '#1EA087', '#277F8E', '#365A8C', '#46327E', '#440154']

        mapper = linear_cmap(field_name='values', palette=colors_reversed, low=weights_matrix.min(), high=weights_matrix.max())

        # Create the main heatmap figure with Range1d for x_range and y_range
        p = figure(title="Neural Network Weights Heatmap", 
                   x_range=Range1d(0, len(row_names)), 
                   y_range=Range1d(0, len(column_names)), 
                   plot_width=1500, 
                   plot_height=1000, 
                   tools="hover,save,reset", 
                   toolbar_location='above')

        # Plot the heatmap
        p.rect(x='x', y='y', width=1, height=1, source=source, fill_color=mapper, line_color=None)

        # Add color bar
        color_bar = ColorBar(color_mapper=mapper['transform'], width=8, location=(0, 0))
        p.add_layout(color_bar, 'right')

        p.xaxis.major_label_orientation = np.pi / 4

        # Add hover tool
        p.hover.tooltips = [("Row, Column", "@y, @x"), ("Value", "@values")]

        # Create a detailed view figure
        detailed_view = figure(title="Detailed View", plot_width=600, plot_height=600)

        detailed_view.rect(x='x', y='y', width=1, height=1, source=detailed_source, fill_color=mapper, line_color=None)

        # Link the axes
        detailed_view.x_range = Range1d(0, 10)
        detailed_view.y_range = Range1d(0, 10)

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
                'values': weights_matrix[min_y:max_y, min_x:max_x].flatten()
            }

            detailed_source.data = detailed_data
            print(f"Updated detailed source: {detailed_source.data}")

        detailed_view.x_range.on_change('start', update_detailed_view)
        detailed_view.x_range.on_change('end', update_detailed_view)
        detailed_view.y_range.on_change('start', update_detailed_view)
        detailed_view.y_range.on_change('end', update_detailed_view)

        self.dynamic_col.children.append(p)
        self.dynamic_col.children.append(detailed_view)