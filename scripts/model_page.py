from functools import partial
from bokeh.models import Panel,ColumnDataSource, Row, Column, TableColumn, DataTable, Button, Div
from datetime import datetime
from datetime import date
import time


from model.model_code import *
from model.pretrainedweightsalphas import *

toTrain = False #when set to False --> it wont be traingn the model. Set to False for debugging reasons with weights and alphas stored in variables

class ModelPage():
    def __init__(self, data, metadata):
        self.data = data
        self.metadata = metadata
        self.ui_elements = {}

    def compose_panel(self):
        print("COMPOSE PANEL CALLED")
        self.ui_elements['button1'] = Button(label="Start Model", button_type="success", width=200)
        self.ui_elements['button1'].on_click(partial(self.model_started, data=self.data, metadata=self.metadata))

        #when run from here it displays correctly, but when from the model the view is not restarted
        # factors = ["foo 123", "bar:0.2", "baz-10"]
        # x = ["foo 123", "foo 123", "foo 123", "bar:0.2", "bar:0.2", "bar:0.2", "baz-10",  "baz-10",  "baz-10"]
        # y = ["foo 123", "bar:0.2", "baz-10",  "foo 123", "bar:0.2", "baz-10",  "foo 123", "bar:0.2", "baz-10"]
        # colors = [
        #     "#0B486B", "#79BD9A", "#CFF09E",
        #     "#79BD9A", "#0B486B", "#79BD9A",
        #     "#CFF09E", "#79BD9A", "#0B486B"
        # ]

        # p = figure(title="Categorical Heatmap", tools="hover", toolbar_location=None,
        #         x_range=factors, y_range=factors)

        # p.rect(x, y, color=colors, width=1, height=1)
        # self.ui_elements["figure"] = p


        # Create a list to hold all the elements
        elements = []
        # Iterate through ui_elements and add each element to the list
        print(f"FROM MODELVIEW")
        for element_name, element in self.ui_elements.items():
            print(element_name)
            elements.append(element)

        # Create a column layout with all elements
        layout = Column(*elements)

        panel = Panel(child=Row(layout), title="Model Page")
        return panel
    
    # def compose_panel2(self,uilist):
    #     elements = []
    #     # Iterate through ui_elements and add each element to the list
    #     print(f"FROM MODELVIEW2")
    #     for element_name, element in uilist.items():
    #         elements.append(element)
    #     layout = Column(*elements)

    #     panel = Panel(child=Row(layout), title="Model Page")
    #     return panel


    def model_started(self,data, metadata):
        print('Model Called')
        if toTrain:
            print("Training started...")
            column_names, weights, alphas = run_model(data, metadata)
        else:
            weights = weights_result
            alphas = alphas_result
            column_names = columns
        
        numpy.set_printoptions(threshold=10_000)
        torch.set_printoptions(threshold=10_000)

        print("---")
        weigths_converted_to_array=weights.detach().numpy()
        #print(f"Weights: {weigths_converted_to_array}")
        #print(type(weigths_converted_to_array))
        weigths_converted_to_array_absolute = numpy.absolute(weigths_converted_to_array)

        print("---")
        alphas_result_converted_to_array=alphas.detach().numpy()
        #print(f"Alphas: {alphas_result_converted_to_array}")
        #print(type(alphas_result_converted_to_array))
        alphas_converted_to_array_absolute= numpy.absolute(alphas_result_converted_to_array)

        print("---")
        column_names_converted_tolist= column_names.tolist()
        #print(column_names_converted_tolist)
        #print(type(column_names_converted_tolist))
