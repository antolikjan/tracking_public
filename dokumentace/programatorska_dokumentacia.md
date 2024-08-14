# Technical documentation - Quantified Self

**Autor:** Oszkár Urbán
**Semester:** Summer semester 2023/2024


## Motivation & Technical details

Quantified Self is a scientific platform that visualizes the findings of self-recorded biomedical data. This documentation focuses on "Model Page" which goal is
- visualize the weights and alphas from the underlying multivariable linear regression model in order to find out which parameter is predicted by which peremter.
- the parameters are the underlying various biomedical markers that have been self-recorded

- the platform is built using the Bokeh visualization library
- the underlying model code is written in Pyton using PyTorch

# Selected intristing parts of code
## 1. UI & Layout

The UI elements and layout are managed by the `create_ui_elements` and `setup_layout` methods:

- **UI Elements**: Dropdowns, buttons, and loaders are created using Bokeh widgets (`Select`, `Button`, `Div`). Notable elements include:
  - `to_train`: Select widget to choose between training the model or using cached data.
  - `number_of_bars_to_show`: Select widget to determine the number of bars shown in bar plots.
  - `select_category` and `select_name`: For selecting model categories and names.
  - `show_bar_plot`: Button to trigger bar plot visualization.
  
- **Layout**: The `setup_layout` method organizes these elements into a vertical column (`self.dynamic_col`), dividing the page into logical rows (e.g., `heatmaps_row`, `select_row`) for easy access and modification.

## 2. Gathering Data from the Model

Data gathering occurs within the `run_model_callback` method:

- **Model Invocation**: If training is required (`toTrain` flag), the model is executed using `run_model()`. Otherwise, cached results (`weights_result`, `alphas_result`) are used.
- **Data Processing**: The resulting weights and alphas are converted into numpy arrays and used to populate a `ColumnDataSource` for visualization.

## 3. `on_tap` Detailed View

The `on_tap` method manages user interactions with the heatmap:

- **Event Handling**: When a cell in the heatmap is clicked, `on_tap` identifies the clicked index and corresponding model data (weight and alpha values).
- **Dynamic Updates**: The method dynamically updates the detailed view with bar plots corresponding to the selected cell, modifying the `tap_row` layout.

## 4. Detailed View Hover Over Heatmap

Hover functionality is implemented in the `run_model_callback` method:

- **Detailed View**: A separate detailed view figure (`detailed_view`) is synchronized with the heatmap, allowing zoomed inspection of specific areas. The hover tooltips are customized for enhanced clarity.
- **Heatmap Plot**: A heatmap is created using Bokeh's `rect` glyph. Hover tools are added to display row, column, and value details when the mouse hovers over specific cells.

## 5. Weights Bar Plot with Corresponding Alphas

Bar plots representing weights and corresponding alphas are generated in the `create_bar_plots` method:

- **Weights Plot**: Each category's weights are sorted and plotted as vertical bars using Bokeh's `vbar`.
- **Alphas Plot**: Corresponding alpha values are plotted in a similar manner.
- **Color Mapping**: The plots utilize a color mapper (`linear_cmap`) to visually differentiate value magnitudes, and color bars are added for reference.

By organizing these components, `ModelPage` provides an interactive interface for visualizing and analyzing model outputs.
