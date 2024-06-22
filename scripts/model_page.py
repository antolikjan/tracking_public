from functools import partial
from bokeh.models import Panel, Column, Button, Div
from bokeh.io import curdoc
import numpy
import torch
import time

from model.model_code import *
from model.pretrainedweightsalphas import *

toTrain = False # When set to False --> it won't be training the model. Set to False for debugging reasons with weights and alphas stored in variables

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

        numpy.set_printoptions(threshold=10_000)
        torch.set_printoptions(threshold=10_000)

        print("---")
        weights_converted_to_array = weights.detach().numpy()
        weights_converted_to_array_absolute = numpy.absolute(weights_converted_to_array)

        print("---")
        alphas_result_converted_to_array = alphas.detach().numpy()
        alphas_converted_to_array_absolute = numpy.absolute(alphas_result_converted_to_array)

        print("---")
        column_names_converted_to_list = column_names.tolist()
