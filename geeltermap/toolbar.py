"""Module for dealing with the toolbar.
"""
import os
import deims
import ee
import pandas as pd
import ipyevents
import ipyleaflet
import ipywidgets as widgets
from ipyfilechooser import FileChooser
from IPython.core.display import display
from ndvi2gif import NdviSeasonality
from datetime import datetime

from .common import *

eLTER_SITES = {}
downloads_images = {}

def tool_template(m=None):

    widget_width = "250px"
    padding = "0px 0px 0px 5px"  # upper, right, bottom, left

    toolbar_button = widgets.ToggleButton(
        value=False,
        tooltip="Toolbar",
        icon="gear",
        layout=widgets.Layout(width="28px", height="28px", padding="0px 0px 0px 4px"),
    )

    close_button = widgets.ToggleButton(
        value=False,
        tooltip="Close the tool",
        icon="times",
        button_style="primary",
        layout=widgets.Layout(height="28px", width="28px", padding="0px 0px 0px 4px"),
    )

    checkbox = widgets.Checkbox(
        description="Checkbox",
        indent=False,
        layout=widgets.Layout(padding=padding, width=widget_width),
    )

    dropdown = widgets.Dropdown(
        options=["Option 1", "Option 2", "Option 3"],
        value=None,
        description="Dropdown:",
        layout=widgets.Layout(width=widget_width, padding=padding),
        style={"description_width": "initial"},
    )

    int_slider = widgets.IntSlider(
        min=1,
        max=100,
        description="Int Slider: ",
        readout=False,
        continuous_update=True,
        layout=widgets.Layout(width="220px", padding=padding),
        style={"description_width": "initial"},
    )

    int_slider_label = widgets.Label()
    widgets.jslink((int_slider, "value"), (int_slider_label, "value"))

    float_slider = widgets.FloatSlider(
        min=1,
        max=100,
        description="Float Slider: ",
        readout=False,
        continuous_update=True,
        layout=widgets.Layout(width="220px", padding=padding),
        style={"description_width": "initial"},
    )

    float_slider_label = widgets.Label()
    widgets.jslink((float_slider, "value"), (float_slider_label, "value"))

    color = widgets.ColorPicker(
        concise=False,
        description="Color:",
        value="white",
        style={"description_width": "initial"},
        layout=widgets.Layout(width=widget_width, padding=padding),
    )

    text = widgets.Text(
        value="",
        description="Textbox:",
        placeholder="Placeholder",
        style={"description_width": "initial"},
        layout=widgets.Layout(width=widget_width, padding=padding),
    )

    textarea = widgets.Textarea(
        placeholder="Placeholder",
        layout=widgets.Layout(width=widget_width),
    )

    buttons = widgets.ToggleButtons(
        value=None,
        options=["Apply", "Reset", "Close"],
        tooltips=["Apply", "Reset", "Close"],
        button_style="primary",
    )
    buttons.style.button_width = "80px"

    output = widgets.Output(layout=widgets.Layout(width=widget_width, padding=padding))

    toolbar_widget = widgets.VBox()
    toolbar_widget.children = [toolbar_button]
    toolbar_header = widgets.HBox()
    toolbar_header.children = [close_button, toolbar_button]
    toolbar_footer = widgets.VBox()
    toolbar_footer.children = [
        checkbox,
        widgets.HBox([int_slider, int_slider_label]),
        widgets.HBox([float_slider, float_slider_label]),
        dropdown,
        text,
        color,
        textarea,
        buttons,
        output,
    ]

    toolbar_event = ipyevents.Event(
        source=toolbar_widget, watched_events=["mouseenter", "mouseleave"]
    )

    def handle_toolbar_event(event):

        if event["type"] == "mouseenter":
            toolbar_widget.children = [toolbar_header, toolbar_footer]
        elif event["type"] == "mouseleave":
            if not toolbar_button.value:
                toolbar_widget.children = [toolbar_button]
                toolbar_button.value = False
                close_button.value = False

    toolbar_event.on_dom_event(handle_toolbar_event)

    def toolbar_btn_click(change):
        if change["new"]:
            close_button.value = False
            toolbar_widget.children = [toolbar_header, toolbar_footer]
        else:
            if not close_button.value:
                toolbar_widget.children = [toolbar_button]

    toolbar_button.observe(toolbar_btn_click, "value")

    def close_btn_click(change):
        if change["new"]:
            toolbar_button.value = False
            if m is not None:
                m.toolbar_reset()
                if m.tool_control is not None and m.tool_control in m.controls:
                    m.remove_control(m.tool_control)
                    m.tool_control = None
            toolbar_widget.close()

    close_button.observe(close_btn_click, "value")

    def button_clicked(change):
        if change["new"] == "Apply":
            with output:
                output.clear_output()
                print("Running ...")
        elif change["new"] == "Reset":
            textarea.value = ""
            output.clear_output()
        elif change["new"] == "Close":
            if m is not None:
                m.toolbar_reset()
                if m.tool_control is not None and m.tool_control in m.controls:
                    m.remove_control(m.tool_control)
                    m.tool_control = None
            toolbar_widget.close()

        buttons.value = None

    buttons.observe(button_clicked, "value")

    toolbar_button.value = True
    if m is not None:
        toolbar_control = ipyleaflet.WidgetControl(
            widget=toolbar_widget, position="topright"
        )

        if toolbar_control not in m.controls:
            m.add_control(toolbar_control)
            m.tool_control = toolbar_control
    else:
        return toolbar_widget


def open_data_widget(m):
    """A widget for opening local vector/raster data.

    Args:
        m (object): geemap.Map
    """
    from .colormaps import list_colormaps

    padding = "0px 0px 0px 5px"
    style = {"description_width": "initial"}

    tool_output = widgets.Output()
    tool_output_ctrl = ipyleaflet.WidgetControl(widget=tool_output, position="topright")

    if m.tool_output_ctrl is not None and m.tool_output_ctrl in m.controls:
        m.remove_control(m.tool_output_ctrl)

    file_type = widgets.ToggleButtons(
        options=["Shapefile", "GeoJSON", "CSV", "Vector", "Raster"],
        tooltips=[
            "Open a shapefile",
            "Open a GeoJSON file",
            "Open a vector dataset",
            "Create points from CSV",
            "Open a vector dataset",
            "Open a raster dataset",
        ],
    )
    file_type.style.button_width = "88px"

    filepath = widgets.Text(
        value="",
        description="File path or http URL:",
        tooltip="Enter a file path or http URL to vector data",
        style=style,
        layout=widgets.Layout(width="454px", padding=padding),
    )
    http_widget = widgets.HBox()

    file_chooser = FileChooser(
        os.getcwd(), sandbox_path=m.sandbox_path, layout=widgets.Layout(width="454px")
    )
    file_chooser.filter_pattern = "*.shp"
    file_chooser.use_dir_icons = True

    style = {"description_width": "initial"}
    layer_name = widgets.Text(
        value="Shapefile",
        description="Enter a layer name:",
        tooltip="Enter a layer name for the selected file",
        style=style,
        layout=widgets.Layout(width="454px", padding="0px 0px 0px 5px"),
    )

    longitude = widgets.Dropdown(
        options=[],
        value=None,
        description="Longitude:",
        layout=widgets.Layout(width="149px", padding="0px 0px 0px 5px"),
        style={"description_width": "initial"},
    )

    latitude = widgets.Dropdown(
        options=[],
        value=None,
        description="Latitude:",
        layout=widgets.Layout(width="149px", padding="0px 0px 0px 5px"),
        style={"description_width": "initial"},
    )

    label = widgets.Dropdown(
        options=[],
        value=None,
        description="Label:",
        layout=widgets.Layout(width="149px", padding="0px 0px 0px 5px"),
        style={"description_width": "initial"},
    )

    csv_widget = widgets.HBox()

    convert_bool = widgets.Checkbox(
        description="Convert to ee.FeatureCollection?",
        indent=False,
        layout=widgets.Layout(padding="0px 0px 0px 5px"),
    )
    convert_hbox = widgets.HBox([convert_bool])

    ok_cancel = widgets.ToggleButtons(
        value=None,
        options=["Apply", "Reset", "Close"],
        tooltips=["Apply", "Reset", "Close"],
        button_style="primary",
    )
    # ok_cancel.style.button_width = "133px"

    bands = widgets.Text(
        value=None,
        description="Band:",
        tooltip="Enter a list of band indices",
        style=style,
        layout=widgets.Layout(width="150px", padding=padding),
    )

    vmin = widgets.Text(
        value=None,
        description="vmin:",
        tooltip="Minimum value of the raster to visualize",
        style=style,
        layout=widgets.Layout(width="148px"),
    )

    vmax = widgets.Text(
        value=None,
        description="vmax:",
        tooltip="Maximum value of the raster to visualize",
        style=style,
        layout=widgets.Layout(width="148px"),
    )

    nodata = widgets.Text(
        value=None,
        description="Nodata:",
        tooltip="Nodata the raster to visualize",
        style=style,
        layout=widgets.Layout(width="150px", padding=padding),
    )

    palette = widgets.Dropdown(
        options=[],
        value=None,
        description="palette:",
        layout=widgets.Layout(width="300px"),
        style=style,
    )

    raster_options = widgets.VBox()

    main_widget = widgets.VBox(
        [
            file_type,
            file_chooser,
            http_widget,
            csv_widget,
            layer_name,
            convert_hbox,
            raster_options,
            ok_cancel,
        ]
    )

    tool_output.clear_output()
    with tool_output:
        display(main_widget)

    def bands_changed(change):
        if change["new"] and "," in change["owner"].value:
            palette.value = None
            palette.disabled = True
        else:
            palette.disabled = False

    bands.observe(bands_changed, "value")

    def chooser_callback(chooser):

        filepath.value = file_chooser.selected

        if file_type.value == "CSV":
            import pandas as pd

            df = pd.read_csv(filepath.value)
            col_names = df.columns.values.tolist()
            longitude.options = col_names
            latitude.options = col_names
            label.options = col_names

            if "longitude" in col_names:
                longitude.value = "longitude"
            if "latitude" in col_names:
                latitude.value = "latitude"
            if "name" in col_names:
                label.value = "name"

    file_chooser.register_callback(chooser_callback)

    def file_type_changed(change):
        ok_cancel.value = None
        file_chooser.default_path = os.getcwd()
        file_chooser.reset()
        layer_name.value = file_type.value
        csv_widget.children = []
        filepath.value = ""

        if change["new"] == "Shapefile":
            file_chooser.filter_pattern = "*.shp"
            raster_options.children = []
            convert_hbox.children = [convert_bool]
            http_widget.children = []
        elif change["new"] == "GeoJSON":
            file_chooser.filter_pattern = "*.geojson"
            raster_options.children = []
            convert_hbox.children = [convert_bool]
            http_widget.children = [filepath]
        elif change["new"] == "Vector":
            file_chooser.filter_pattern = "*.*"
            raster_options.children = []
            convert_hbox.children = [convert_bool]
            http_widget.children = [filepath]
        elif change["new"] == "CSV":
            file_chooser.filter_pattern = ["*.csv", "*.CSV"]
            csv_widget.children = [longitude, latitude, label]
            raster_options.children = []
            convert_hbox.children = [convert_bool]
            http_widget.children = [filepath]
        elif change["new"] == "Raster":
            file_chooser.filter_pattern = ["*.tif", "*.img"]
            palette.options = list_colormaps(add_extra=True)
            palette.value = None
            raster_options.children = [
                widgets.HBox([bands, vmin, vmax]),
                widgets.HBox([nodata, palette]),
            ]
            convert_hbox.children = []
            http_widget.children = [filepath]

    def ok_cancel_clicked(change):
        if change["new"] == "Apply":
            m.default_style = {"cursor": "wait"}
            file_path = filepath.value

            if file_path is not None:
                ext = os.path.splitext(file_path)[1]
                with tool_output:
                    if ext.lower() == ".shp":
                        if convert_bool.value:
                            ee_object = shp_to_ee(file_path)
                            m.addLayer(ee_object, {}, layer_name.value)
                        else:
                            m.add_shapefile(
                                file_path, style={}, layer_name=layer_name.value
                            )
                    elif ext.lower() == ".geojson":
                        if convert_bool.value:
                            ee_object = geojson_to_ee(file_path)
                            m.addLayer(ee_object, {}, layer_name.value)
                        else:
                            m.add_geojson(
                                file_path, style={}, layer_name=layer_name.value
                            )

                    elif ext.lower() == ".csv":
                        if convert_bool.value:
                            ee_object = csv_to_ee(
                                file_path, latitude.value, longitude.value
                            )
                            m.addLayer(ee_object, {}, layer_name.value)
                        else:
                            m.add_xy_data(
                                file_path,
                                x=longitude.value,
                                y=latitude.value,
                                label=label.value,
                                layer_name=layer_name.value,
                            )

                    elif ext.lower() in [".tif", "img"] and file_type.value == "Raster":
                        band = None
                        vis_min = None
                        vis_max = None
                        vis_nodata = None

                        try:
                            if len(bands.value) > 0:
                                band = bands.value.split(",")
                            if len(vmin.value) > 0:
                                vis_min = float(vmin.value)
                            if len(vmax.value) > 0:
                                vis_max = float(vmax.value)
                            if len(nodata.value) > 0:
                                vis_nodata = float(nodata.value)
                        except Exception as _:
                            pass

                        m.add_local_tile(
                            file_path,
                            layer_name=layer_name.value,
                            band=band,
                            palette=palette.value,
                            vmin=vis_min,
                            vmax=vis_max,
                            nodata=vis_nodata,
                        )
                    else:
                        m.add_vector(file_path, style={}, layer_name=layer_name.value)
            else:
                print("Please select a file to open.")

            m.toolbar_reset()
            m.default_style = {"cursor": "default"}

        elif change["new"] == "Reset":
            file_chooser.reset()
            tool_output.clear_output()
            with tool_output:
                display(main_widget)
            m.toolbar_reset()
        elif change["new"] == "Close":
            if m.tool_output_ctrl is not None and m.tool_output_ctrl in m.controls:
                m.remove_control(m.tool_output_ctrl)
                m.tool_output_ctrl = None
                m.toolbar_reset()

        ok_cancel.value = None

    file_type.observe(file_type_changed, names="value")
    ok_cancel.observe(ok_cancel_clicked, names="value")
    # file_chooser.register_callback(chooser_callback)

    m.add_control(tool_output_ctrl)
    m.tool_output_ctrl = tool_output_ctrl


def get_tools_dict():

    import pandas as pd
    import pkg_resources

    pkg_dir = os.path.dirname(pkg_resources.resource_filename("geemap", "geemap.py"))
    toolbox_csv = os.path.join(pkg_dir, "data/template/toolbox.csv")

    df = pd.read_csv(toolbox_csv).set_index("index")
    tools_dict = df.to_dict("index")

    return tools_dict


def tool_gui(tool_dict, max_width="420px", max_height="600px"):
    """Create a GUI for a tool based on the tool dictionary.

    Args:
        tool_dict (dict): The dictionary containing the tool info.
        max_width (str, optional): The max width of the tool dialog.
        max_height (str, optional): The max height of the tool dialog.

    Returns:
        object: An ipywidget object representing the tool interface.
    """
    tool_widget = widgets.VBox(
        layout=widgets.Layout(max_width=max_width, max_height=max_height)
    )
    children = []
    args = {}
    required_inputs = []
    style = {"description_width": "initial"}
    max_width = str(int(max_width.replace("px", "")) - 10) + "px"

    header_width = str(int(max_width.replace("px", "")) - 104) + "px"
    header = widgets.Label(
        value=f'Current Tool: {tool_dict["label"]}',
        style=style,
        layout=widgets.Layout(width=header_width),
    )
    code_btn = widgets.Button(
        description="View Code", layout=widgets.Layout(width="100px")
    )

    children.append(widgets.HBox([header, code_btn]))

    desc = widgets.Textarea(
        value=f'Description: {tool_dict["description"]}',
        layout=widgets.Layout(width="410px", max_width=max_width),
        disabled=True,
    )
    children.append(desc)

    run_btn = widgets.Button(description="Run", layout=widgets.Layout(width="100px"))
    cancel_btn = widgets.Button(
        description="Cancel", layout=widgets.Layout(width="100px")
    )
    help_btn = widgets.Button(description="Help", layout=widgets.Layout(width="100px"))
    import_btn = widgets.Button(
        description="Import",
        tooltip="Import the script to a new cell",
        layout=widgets.Layout(width="98px"),
    )
    tool_output = widgets.Output(layout=widgets.Layout(max_height="200px"))
    children.append(widgets.HBox([run_btn, cancel_btn, help_btn, import_btn]))
    children.append(tool_output)
    tool_widget.children = children

    def run_button_clicked(b):
        tool_output.clear_output()

        required_params = required_inputs.copy()
        args2 = []
        for arg in args:

            line = ""
            if isinstance(args[arg], FileChooser):
                if arg in required_params and args[arg].selected is None:
                    with tool_output:
                        print(f"Please provide inputs for required parameters.")
                        break
                elif arg in required_params:
                    required_params.remove(arg)
                if arg == "i":
                    line = f"-{arg}={args[arg].selected}"
                else:
                    line = f"--{arg}={args[arg].selected}"
            elif isinstance(args[arg], widgets.Text):
                if arg in required_params and len(args[arg].value) == 0:
                    with tool_output:
                        print(f"Please provide inputs for required parameters.")
                        break
                elif arg in required_params:
                    required_params.remove(arg)
                if args[arg].value is not None and len(args[arg].value) > 0:
                    line = f"--{arg}={args[arg].value}"
            elif isinstance(args[arg], widgets.Checkbox):
                line = f"--{arg}={args[arg].value}"
            args2.append(line)

        if len(required_params) == 0:
            with tool_output:
                # wbt.run_tool(tool_dict["name"], args2)
                pass

    def help_button_clicked(b):
        import webbrowser

        tool_output.clear_output()
        with tool_output:
            html = widgets.HTML(
                value=f'<a href={tool_dict["link"]} target="_blank">{tool_dict["link"]}</a>'
            )
            display(html)
        webbrowser.open_new_tab(tool_dict["link"])

    def code_button_clicked(b):
        import webbrowser

        with tool_output:
            html = widgets.HTML(
                value=f'<a href={tool_dict["link"]} target="_blank">{tool_dict["link"]}</a>'
            )
            display(html)
        webbrowser.open_new_tab(tool_dict["link"])

    def cancel_btn_clicked(b):
        tool_output.clear_output()

    def import_button_clicked(b):
        tool_output.clear_output()

        content = []

        create_code_cell("\n".join(content))

    import_btn.on_click(import_button_clicked)
    run_btn.on_click(run_button_clicked)
    help_btn.on_click(help_button_clicked)
    code_btn.on_click(code_button_clicked)
    cancel_btn.on_click(cancel_btn_clicked)

    return tool_widget


def build_toolbox(tools_dict, max_width="1080px", max_height="600px"):
    """Build the GEE toolbox.

    Args:
        tools_dict (dict): A dictionary containing information for all tools.
        max_width (str, optional): The maximum width of the widget.
        max_height (str, optional): The maximum height of the widget.

    Returns:
        object: An ipywidget representing the toolbox.
    """
    left_widget = widgets.VBox(layout=widgets.Layout(min_width="175px"))
    center_widget = widgets.VBox(
        layout=widgets.Layout(min_width="200px", max_width="200px")
    )
    right_widget = widgets.Output(
        layout=widgets.Layout(width="630px", max_height=max_height)
    )
    full_widget = widgets.HBox(
        [left_widget, center_widget, right_widget],
        layout=widgets.Layout(max_width=max_width, max_height=max_height),
    )

    search_widget = widgets.Text(
        placeholder="Search tools ...", layout=widgets.Layout(width="170px")
    )
    label_widget = widgets.Label(layout=widgets.Layout(width="170px"))
    label_widget.value = f"{len(tools_dict)} Available Tools"
    close_btn = widgets.Button(
        description="Close Toolbox", icon="close", layout=widgets.Layout(width="170px")
    )

    categories = {}
    categories["All Tools"] = []
    for key in tools_dict.keys():
        category = tools_dict[key]["category"]
        if category not in categories.keys():
            categories[category] = []
        categories[category].append(tools_dict[key]["name"])
        categories["All Tools"].append(tools_dict[key]["name"])

    options = list(categories.keys())
    all_tools = categories["All Tools"]
    all_tools.sort()
    category_widget = widgets.Select(
        options=options, layout=widgets.Layout(width="170px", height="165px")
    )
    tools_widget = widgets.Select(
        options=[], layout=widgets.Layout(width="195px", height="400px")
    )

    def category_selected(change):
        if change["new"]:
            selected = change["owner"].value
            options = categories[selected]
            options.sort()
            tools_widget.options = options
            label_widget.value = f"{len(options)} Available Tools"

    category_widget.observe(category_selected, "value")

    def tool_selected(change):
        if change["new"]:
            selected = change["owner"].value
            tool_dict = tools_dict[selected]
            with right_widget:
                right_widget.clear_output()
                display(tool_gui(tool_dict, max_height=max_height))

    tools_widget.observe(tool_selected, "value")

    def search_changed(change):
        if change["new"]:
            keyword = change["owner"].value
            if len(keyword) > 0:
                selected_tools = []
                for tool in all_tools:
                    if keyword.lower() in tool.lower():
                        selected_tools.append(tool)
                if len(selected_tools) > 0:
                    tools_widget.options = selected_tools
                label_widget.value = f"{len(selected_tools)} Available Tools"
        else:
            tools_widget.options = all_tools
            label_widget.value = f"{len(tools_dict)} Available Tools"

    search_widget.observe(search_changed, "value")

    def close_btn_clicked(b):
        full_widget.close()

    close_btn.on_click(close_btn_clicked)

    category_widget.value = list(categories.keys())[0]
    tools_widget.options = all_tools
    left_widget.children = [category_widget, search_widget, label_widget, close_btn]
    center_widget.children = [tools_widget]

    return full_widget


def plotly_toolbar(
    canvas,
):
    """Creates the main toolbar and adds it to the map.

    Args:
        m (plotlymap.Map): The plotly Map object.
    """
    m = canvas.map
    map_min_width = canvas.map_min_width
    map_max_width = canvas.map_max_width
    map_refresh = canvas.map_refresh
    map_widget = canvas.map_widget

    if not map_refresh:
        width = int(map_min_width.replace("%", ""))
        if width > 90:
            map_min_width = "90%"

    tools = {
        "map": {
            "name": "basemap",
            "tooltip": "Change basemap",
        },
        "search": {
            "name": "search_xyz",
            "tooltip": "Search XYZ tile services",
        },
        "gears": {
            "name": "whitebox",
            "tooltip": "WhiteboxTools for local geoprocessing",
        },
        "folder-open": {
            "name": "vector",
            "tooltip": "Open local vector/raster data",
        },
        "picture-o": {
            "name": "raster",
            "tooltip": "Open COG/STAC dataset",
        },
        "question": {
            "name": "help",
            "tooltip": "Get help",
        },
    }

    icons = list(tools.keys())
    tooltips = [item["tooltip"] for item in list(tools.values())]

    icon_width = "32px"
    icon_height = "32px"
    n_cols = 3
    n_rows = math.ceil(len(icons) / n_cols)

    toolbar_grid = widgets.GridBox(
        children=[
            widgets.ToggleButton(
                layout=widgets.Layout(
                    width="auto", height="auto", padding="0px 0px 0px 4px"
                ),
                button_style="primary",
                icon=icons[i],
                tooltip=tooltips[i],
            )
            for i in range(len(icons))
        ],
        layout=widgets.Layout(
            width="115px",
            grid_template_columns=(icon_width + " ") * n_cols,
            grid_template_rows=(icon_height + " ") * n_rows,
            grid_gap="1px 1px",
            padding="5px",
        ),
    )
    canvas.toolbar = toolbar_grid

    def tool_callback(change):

        if change["new"]:
            current_tool = change["owner"]
            for tool in toolbar_grid.children:
                if tool is not current_tool:
                    tool.value = False
            tool = change["owner"]
            tool_name = tools[tool.icon]["name"]
            canvas.container_widget.children = []

            if tool_name == "basemap":
                plotly_basemap_gui(canvas)
            elif tool_name == "search_xyz":
                plotly_search_basemaps(canvas)
            elif tool_name == "whitebox":
                plotly_whitebox_gui(canvas)
            elif tool_name == "vector":
                plotly_tool_template(canvas)
            elif tool_name == "raster":
                plotly_tool_template(canvas)
            elif tool_name == "help":
                import webbrowser

                webbrowser.open_new_tab("https://geemap.org")
                tool.value = False
        else:
            canvas.container_widget.children = []
            map_widget.layout.width = map_max_width

    for tool in toolbar_grid.children:
        tool.observe(tool_callback, "value")

    toolbar_button = widgets.ToggleButton(
        value=False,
        tooltip="Toolbar",
        icon="wrench",
        layout=widgets.Layout(width="28px", height="28px", padding="0px 0px 0px 4px"),
    )
    canvas.toolbar_button = toolbar_button

    layers_button = widgets.ToggleButton(
        value=False,
        tooltip="Layers",
        icon="server",
        layout=widgets.Layout(height="28px", width="72px"),
    )
    canvas.layers_button = layers_button

    toolbar_widget = widgets.VBox(layout=widgets.Layout(overflow="hidden"))
    toolbar_widget.children = [toolbar_button]
    toolbar_header = widgets.HBox(layout=widgets.Layout(overflow="hidden"))
    toolbar_header.children = [layers_button, toolbar_button]
    toolbar_footer = widgets.VBox(layout=widgets.Layout(overflow="hidden"))
    toolbar_footer.children = [toolbar_grid]

    toolbar_event = ipyevents.Event(
        source=toolbar_widget, watched_events=["mouseenter", "mouseleave"]
    )

    def handle_toolbar_event(event):

        if event["type"] == "mouseenter":
            toolbar_widget.children = [toolbar_header, toolbar_footer]
            # map_widget.layout.width = "85%"
        elif event["type"] == "mouseleave":
            if not toolbar_button.value:
                toolbar_widget.children = [toolbar_button]
                toolbar_button.value = False
                layers_button.value = False
                # map_widget.layout.width = map_max_width

    toolbar_event.on_dom_event(handle_toolbar_event)

    def toolbar_btn_click(change):
        if change["new"]:
            map_widget.layout.width = map_min_width
            if map_refresh:
                with map_widget:
                    map_widget.clear_output()
                    display(m)
            layers_button.value = False
            toolbar_widget.children = [toolbar_header, toolbar_footer]
        else:
            canvas.toolbar_reset()
            map_widget.layout.width = map_max_width
            if not layers_button.value:
                toolbar_widget.children = [toolbar_button]
            if map_refresh:
                with map_widget:
                    map_widget.clear_output()
                    display(m)

    toolbar_button.observe(toolbar_btn_click, "value")

    def layers_btn_click(change):
        if change["new"]:

            layer_names = list(m.get_layers().keys())
            layers_hbox = []
            all_layers_chk = widgets.Checkbox(
                value=True,
                description="All layers on/off",
                indent=False,
                layout=widgets.Layout(height="18px", padding="0px 8px 25px 8px"),
            )
            all_layers_chk.layout.width = "30ex"
            layers_hbox.append(all_layers_chk)

            layer_chk_dict = {}

            for name in layer_names:
                if name in m.get_tile_layers():
                    index = m.find_layer_index(name)
                    layer = m.layout.mapbox.layers[index]
                elif name in m.get_data_layers():
                    index = m.find_layer_index(name)
                    layer = m.data[index]

                layer_chk = widgets.Checkbox(
                    value=layer.visible,
                    description=name,
                    indent=False,
                    layout=widgets.Layout(height="18px"),
                )
                layer_chk.layout.width = "25ex"
                layer_chk_dict[name] = layer_chk

                if hasattr(layer, "opacity"):
                    opacity = layer.opacity
                elif hasattr(layer, "marker"):
                    opacity = layer.marker.opacity
                else:
                    opacity = 1.0

                layer_opacity = widgets.FloatSlider(
                    value=opacity,
                    description_tooltip=name,
                    min=0,
                    max=1,
                    step=0.01,
                    readout=False,
                    layout=widgets.Layout(width="80px"),
                )

                layer_settings = widgets.ToggleButton(
                    icon="gear",
                    tooltip=name,
                    layout=widgets.Layout(
                        width="25px", height="25px", padding="0px 0px 0px 5px"
                    ),
                )

                def layer_chk_change(change):

                    if change["new"]:
                        m.set_layer_visibility(change["owner"].description, True)
                    else:
                        m.set_layer_visibility(change["owner"].description, False)

                layer_chk.observe(layer_chk_change, "value")

                def layer_opacity_change(change):
                    if change["new"]:
                        m.set_layer_opacity(
                            change["owner"].description_tooltip, change["new"]
                        )

                layer_opacity.observe(layer_opacity_change, "value")

                hbox = widgets.HBox(
                    [layer_chk, layer_settings, layer_opacity],
                    layout=widgets.Layout(padding="0px 8px 0px 8px"),
                )
                layers_hbox.append(hbox)

            def all_layers_chk_changed(change):
                if change["new"]:
                    for name in layer_names:
                        m.set_layer_visibility(name, True)
                        layer_chk_dict[name].value = True
                else:
                    for name in layer_names:
                        m.set_layer_visibility(name, False)
                        layer_chk_dict[name].value = False

            all_layers_chk.observe(all_layers_chk_changed, "value")

            toolbar_footer.children = layers_hbox
            toolbar_button.value = False
        else:
            toolbar_footer.children = [toolbar_grid]

    layers_button.observe(layers_btn_click, "value")

    return toolbar_widget


def plotly_tool_template(canvas):

    container_widget = canvas.container_widget
    map_widget = canvas.map_widget
    map_width = "70%"
    map_widget.layout.width = map_width

    widget_width = "250px"
    padding = "0px 0px 0px 5px"  # upper, right, bottom, left
    # style = {"description_width": "initial"}

    toolbar_button = widgets.ToggleButton(
        value=False,
        tooltip="Toolbar",
        icon="gears",
        layout=widgets.Layout(width="28px", height="28px", padding="0px 0px 0px 4px"),
    )

    close_button = widgets.ToggleButton(
        value=False,
        tooltip="Close the tool",
        icon="times",
        button_style="primary",
        layout=widgets.Layout(height="28px", width="28px", padding="0px 0px 0px 4px"),
    )
    output = widgets.Output(layout=widgets.Layout(width=widget_width, padding=padding))
    with output:
        print("To be implemented")

    toolbar_widget = widgets.VBox()
    toolbar_widget.children = [toolbar_button]
    toolbar_header = widgets.HBox()
    toolbar_header.children = [close_button, toolbar_button]
    toolbar_footer = widgets.VBox()
    toolbar_footer.children = [
        output,
    ]

    toolbar_event = ipyevents.Event(
        source=toolbar_widget, watched_events=["mouseenter", "mouseleave"]
    )

    def handle_toolbar_event(event):

        if event["type"] == "mouseenter":
            toolbar_widget.children = [toolbar_header, toolbar_footer]
            map_widget.layout.width = map_width
        elif event["type"] == "mouseleave":
            if not toolbar_button.value:
                toolbar_widget.children = [toolbar_button]
                toolbar_button.value = False
                close_button.value = False
                map_widget.layout.width = canvas.map_max_width

    toolbar_event.on_dom_event(handle_toolbar_event)

    def toolbar_btn_click(change):
        if change["new"]:
            close_button.value = False
            toolbar_widget.children = [toolbar_header, toolbar_footer]
            map_widget.layout.width = map_width
        else:
            if not close_button.value:
                toolbar_widget.children = [toolbar_button]
            map_widget.layout.width = canvas.map_max_width

    toolbar_button.observe(toolbar_btn_click, "value")

    def close_btn_click(change):
        if change["new"]:
            toolbar_button.value = False
            canvas.toolbar_reset()
            toolbar_widget.close()

    close_button.observe(close_btn_click, "value")

    toolbar_button.value = True
    container_widget.children = [toolbar_widget]



def inspector_gui(m=None):
    """Generates a tool GUI template using ipywidgets.

    Args:
        m (geemap.Map, optional): The leaflet Map object. Defaults to None.

    Returns:
        ipywidgets: The tool GUI widget.
    """
    import pandas as pd

    widget_width = "250px"
    padding = "0px 5px 0px 5px"  # upper, right, bottom, left
    style = {"description_width": "initial"}

    if m is not None:

        marker_cluster = ipyleaflet.MarkerCluster(name="Inspector Markers")
        setattr(m, "pixel_values", [])
        setattr(m, "marker_cluster", marker_cluster)

        if not hasattr(m, "interact_mode"):
            setattr(m, "interact_mode", False)

        if not hasattr(m, "inspector_output"):
            inspector_output = widgets.Output(
                layout=widgets.Layout(width=widget_width, padding="0px 5px 5px 5px")
            )
            setattr(m, "inspector_output", inspector_output)

        output = m.inspector_output
        output.clear_output()

        if not hasattr(m, "inspector_add_marker"):
            inspector_add_marker = widgets.Checkbox(
                description="Add Marker at clicked location",
                value=True,
                indent=False,
                layout=widgets.Layout(padding=padding, width=widget_width),
            )
            setattr(m, "inspector_add_marker", inspector_add_marker)
        add_marker = m.inspector_add_marker

        if not hasattr(m, "inspector_bands_chk"):
            inspector_bands_chk = widgets.Checkbox(
                description="Get pixel value for visible bands only",
                indent=False,
                layout=widgets.Layout(padding=padding, width=widget_width),
            )
            setattr(m, "inspector_bands_chk", inspector_bands_chk)
        bands_chk = m.inspector_bands_chk

        if not hasattr(m, "inspector_class_label"):
            inspector_label = widgets.Text(
                value="",
                description="Class label:",
                placeholder="Add a label to the marker",
                style=style,
                layout=widgets.Layout(width=widget_width, padding=padding),
            )
            setattr(m, "inspector_class_label", inspector_label)
        label = m.inspector_class_label

        options = []
        if hasattr(m, "cog_layer_dict"):
            options = list(m.cog_layer_dict.keys())
            options.sort()
        if len(options) == 0:
            default_option = None
        else:
            default_option = options[0]
        if not hasattr(m, "inspector_dropdown"):
            inspector_dropdown = widgets.Dropdown(
                options=options,
                value=default_option,
                description="Select a layer:",
                layout=widgets.Layout(width=widget_width, padding=padding),
                style=style,
            )
            setattr(m, "inspector_dropdown", inspector_dropdown)

        dropdown = m.inspector_dropdown

    toolbar_button = widgets.ToggleButton(
        value=False,
        tooltip="Toolbar",
        icon="info-circle",
        layout=widgets.Layout(width="28px", height="28px", padding="0px 0px 0px 4px"),
    )

    close_button = widgets.ToggleButton(
        value=False,
        tooltip="Close the tool",
        icon="times",
        button_style="primary",
        layout=widgets.Layout(height="28px", width="28px", padding="0px 0px 0px 4px"),
    )

    buttons = widgets.ToggleButtons(
        value=None,
        options=["Download", "Reset", "Close"],
        tooltips=["Download", "Reset", "Close"],
        button_style="primary",
    )
    buttons.style.button_width = "80px"

    if len(options) == 0:
        with output:
            print("No COG/STAC layers available")

    toolbar_widget = widgets.VBox()
    toolbar_widget.children = [toolbar_button]
    toolbar_header = widgets.HBox()
    toolbar_header.children = [close_button, toolbar_button]
    toolbar_footer = widgets.VBox()
    toolbar_footer.children = [
        add_marker,
        label,
        dropdown,
        bands_chk,
        buttons,
        output,
    ]

    toolbar_event = ipyevents.Event(
        source=toolbar_widget, watched_events=["mouseenter", "mouseleave"]
    )

    def chk_change(change):
        if hasattr(m, "pixel_values"):
            m.pixel_values = []
        if hasattr(m, "marker_cluster"):
            m.marker_cluster.markers = []
        output.clear_output()

    bands_chk.observe(chk_change, "value")

    def handle_toolbar_event(event):

        if event["type"] == "mouseenter":
            toolbar_widget.children = [toolbar_header, toolbar_footer]
        elif event["type"] == "mouseleave":
            if not toolbar_button.value:
                toolbar_widget.children = [toolbar_button]
                toolbar_button.value = False
                close_button.value = False

    toolbar_event.on_dom_event(handle_toolbar_event)

    def toolbar_btn_click(change):
        if change["new"]:
            close_button.value = False
            toolbar_widget.children = [toolbar_header, toolbar_footer]
        else:
            if not close_button.value:
                toolbar_widget.children = [toolbar_button]

    toolbar_button.observe(toolbar_btn_click, "value")

    def close_btn_click(change):
        if change["new"]:
            toolbar_button.value = False
            if m is not None:
                if hasattr(m, "inspector_mode"):
                    delattr(m, "inspector_mode")
                m.toolbar_reset()
                if m.tool_control is not None and m.tool_control in m.controls:
                    m.remove_control(m.tool_control)
                    m.tool_control = None
                m.default_style = {"cursor": "default"}

                m.marker_cluster.markers = []
                m.pixel_values = []
                marker_cluster_layer = m.find_layer("Inspector Markers")
                if marker_cluster_layer is not None:
                    m.remove_layer(marker_cluster_layer)

                if hasattr(m, "pixel_values"):
                    delattr(m, "pixel_values")

                if hasattr(m, "marker_cluster"):
                    delattr(m, "marker_cluster")

            toolbar_widget.close()

    close_button.observe(close_btn_click, "value")

    def button_clicked(change):
        if change["new"] == "Download":
            with output:
                output.clear_output()
                if len(m.pixel_values) == 0:
                    print(
                        "No pixel values available. Click on the map to start collection data."
                    )
                else:
                    print("Downloading pixel values...")
                    df = pd.DataFrame(m.pixel_values)
                    temp_csv = temp_file_path("csv")
                    df.to_csv(temp_csv, index=False)
                    link = create_download_link(temp_csv)
                    with output:
                        output.clear_output()
                        display(link)
        elif change["new"] == "Reset":
            label.value = ""
            output.clear_output()
            if hasattr(m, "pixel_values"):
                m.pixel_values = []
            if hasattr(m, "marker_cluster"):
                m.marker_cluster.markers = []
        elif change["new"] == "Close":
            if m is not None:
                if hasattr(m, "inspector_mode"):
                    delattr(m, "inspector_mode")
                m.toolbar_reset()
                if m.tool_control is not None and m.tool_control in m.controls:
                    m.remove_control(m.tool_control)
                    m.tool_control = None
                m.default_style = {"cursor": "default"}
                m.marker_cluster.markers = []
                marker_cluster_layer = m.find_layer("Inspector Markers")
                if marker_cluster_layer is not None:
                    m.remove_layer(marker_cluster_layer)
                m.pixel_values = []

                if hasattr(m, "pixel_values"):
                    delattr(m, "pixel_values")

                if hasattr(m, "marker_cluster"):
                    delattr(m, "marker_cluster")

            toolbar_widget.close()

        buttons.value = None

    buttons.observe(button_clicked, "value")

    toolbar_button.value = True

    def handle_interaction(**kwargs):
        latlon = kwargs.get("coordinates")
        lat = round(latlon[0], 4)
        lon = round(latlon[1], 4)
        if (
            kwargs.get("type") == "click"
            and hasattr(m, "inspector_mode")
            and m.inspector_mode
        ):
            m.default_style = {"cursor": "wait"}

            with output:
                output.clear_output()
                print("Getting pixel value ...")

                layer_dict = m.cog_layer_dict[dropdown.value]

            if layer_dict["type"] == "STAC":
                if bands_chk.value:
                    assets = layer_dict["assets"]
                else:
                    assets = None

                result = stac_pixel_value(
                    lon,
                    lat,
                    layer_dict["url"],
                    layer_dict["collection"],
                    layer_dict["items"],
                    assets,
                    layer_dict["titiler_endpoint"],
                    verbose=False,
                )
                if result is not None:
                    with output:
                        output.clear_output()
                        print(f"lat/lon: {lat:.4f}, {lon:.4f}\n")
                        for key in result:
                            print(f"{key}: {result[key]}")

                        result["latitude"] = lat
                        result["longitude"] = lon
                        result["label"] = label.value
                        m.pixel_values.append(result)
                    if add_marker.value:
                        markers = list(m.marker_cluster.markers)
                        markers.append(ipyleaflet.Marker(location=latlon))
                        m.marker_cluster.markers = markers

                else:
                    with output:
                        output.clear_output()
                        print("No pixel value available")
                        bounds = m.cog_layer_dict[m.inspector_dropdown.value]["bounds"]
                        m.zoom_to_bounds(bounds)
            elif layer_dict["type"] == "COG":
                result = cog_pixel_value(lon, lat, layer_dict["url"], verbose=False)
                if result is not None:
                    with output:
                        output.clear_output()
                        print(f"lat/lon: {lat:.4f}, {lon:.4f}\n")
                        for key in result:
                            print(f"{key}: {result[key]}")

                        result["latitude"] = lat
                        result["longitude"] = lon
                        result["label"] = label.value
                        m.pixel_values.append(result)
                    if add_marker.value:
                        markers = list(m.marker_cluster.markers)
                        markers.append(ipyleaflet.Marker(location=latlon))
                        m.marker_cluster.markers = markers
                else:
                    with output:
                        output.clear_output()
                        print("No pixel value available")
                        bounds = m.cog_layer_dict[m.inspector_dropdown.value]["bounds"]
                        m.zoom_to_bounds(bounds)

            elif layer_dict["type"] == "LOCAL":
                result = local_tile_pixel_value(
                    lon, lat, layer_dict["tile_client"], verbose=False
                )
                if result is not None:
                    if m.inspector_bands_chk.value:
                        band = m.cog_layer_dict[m.inspector_dropdown.value]["band"]
                        band_names = m.cog_layer_dict[m.inspector_dropdown.value][
                            "band_names"
                        ]
                        if band is not None:
                            sel_bands = [band_names[b - 1] for b in band]
                            result = {k: v for k, v in result.items() if k in sel_bands}
                    with output:
                        output.clear_output()
                        print(f"lat/lon: {lat:.4f}, {lon:.4f}\n")
                        for key in result:
                            print(f"{key}: {result[key]}")

                        result["latitude"] = lat
                        result["longitude"] = lon
                        result["label"] = label.value
                        m.pixel_values.append(result)
                    if add_marker.value:
                        markers = list(m.marker_cluster.markers)
                        markers.append(ipyleaflet.Marker(location=latlon))
                        m.marker_cluster.markers = markers
                else:
                    with output:
                        output.clear_output()
                        print("No pixel value available")
                        bounds = m.cog_layer_dict[m.inspector_dropdown.value]["bounds"]
                        m.zoom_to_bounds(bounds)
            m.default_style = {"cursor": "crosshair"}

    if m is not None:
        if not hasattr(m, "marker_cluster"):
            setattr(m, "marker_cluster", marker_cluster)
        m.add_layer(marker_cluster)

        if not m.interact_mode:

            m.on_interaction(handle_interaction)
            m.interact_mode = True

    if m is not None:
        toolbar_control = ipyleaflet.WidgetControl(
            widget=toolbar_widget, position="topright"
        )

        if toolbar_control not in m.controls:
            m.add_control(toolbar_control)
            m.tool_control = toolbar_control

        if not hasattr(m, "inspector_mode"):
            if hasattr(m, "cog_layer_dict"):
                setattr(m, "inspector_mode", True)
            else:
                setattr(m, "inspector_mode", False)

    else:
        return toolbar_widget


##############################################################################################################
##############################################################################################################
##############################################################################################################

def PhenoApp(m=None):

    """Showing phenological metrics for eLTER sites

    Args:
        m (geemap.Map, optional staellite collection and phenometrics DOY or value): A geemap Map instance. Defaults to None.

    Returns:
        ipywidgets: The interactive GUI.
    """

    if m is not None:
        m.add_basemap("Esri.WorldImagery")

    
    #Adding eLETR shapes through deimsPY
    
    eelter_object = ee.FeatureCollection('projects/ee-digdgeografo/assets/elter_lyon')
    
    deimsDict = {'Donana': "bcbc866c-3f4f-47a8-bbbc-0a93df6de7b2",
                 'Braila_Island': "d4854af8-9d9f-42a2-af96-f1ed9cb25712",
                 'Baixo': "45722713-80e3-4387-a47b-82c97a6ef62b",
                 'River_Exe': "b8e9402a-10bc-4892-b03d-1e85fc925c99",
                 'Cairngorms': "1b94503d-285c-4028-a3db-bc78e31dea07",
                 'Veluwe': "bef0bbd2-d8a9-4672-9e5b-085d049f4879",
                 'Gran_Paradiso': "15c3e841-8494-42d2-a44e-c49a0ff25946",
                 'Schorfheide': "94c53dd1-acad-4ad8-a73b-62669ec7af2a",
                 'Neusiedler': "1230b149-9ba5-4ab8-86c9-cf93120f8ae2"}

    networks = {"Austria": "d45c2690-dbef-4dbc-a742-26ea846edf28",
            "Belgica": "735946e0-4e9e-484a-acee-85e31f4e2a2e",
            "Bulgaria": "20ad4fa2-cc07-4848-b9ed-8952c55f1a3f",
            "Denmark": "e3911e8a-ce9b-46ce-8265-c2dc9676ad03",
            "Finland": "aaae2a46-f355-41d0-8067-c2f0cd52e814",
            "France": "d8d9206f-b1bd-4f90-84b7-8c662d4235a2",
            "Germany": "e904354a-f3a0-40ce-a9b5-61741f66c824",
            "Greece": "83453a6c-792d-4549-9dbb-c17ced2e0cc3",
            "Hungary": "0615a89f-2883-47ab-8cd0-2508f413cab7",
            "Israel": "e0f680c2-22b1-4424-bf54-58aa9b7476a0",
            "Italy": "7fef6b73-e5cb-4cd2-b438-ed32eb1504b3",
            "Netherlands": "8312c2c4-a787-4986-9a3d-3f1364bab3ba",
            "Norway": "bc7c517b-3648-40cc-a04c-8c98d009c4a9",
            "Poland": "67763729-45a7-4248-a70d-622b1d0a3d41",
            "Portugal": "d8eb4823-b707-4590-94d8-d90c1d07d6f8",
            "Romania": "4260f964-0ac4-4406-8adc-5afc06e31779",
            "Slovakia": "3d6a8d72-9f86-4082-ad56-a361b4cdc8a0",
            "Slovenia": "fda2984f-9aea-4abf-9f6c-c3eca0f82eb8",
            "Spain": "2b70f1fb-f7d9-4615-a1a3-33fc6fa44600",
            "Sweden": "a50d9e39-d4b6-4d30-bba2-43580ac8c0b2",
            "Switzerland": "cedf695c-c6dc-4660-b944-3c22f12ad0d9"}

    country_sites = {}    

    for k, v in deimsDict.items():
        eLTER_SITES[k] = [deims.getSiteById(v)['title'], gdf_to_ee(deims.getSiteBoundaries(v))]
                
    
    # Shape Styling

    style = {
                    "stroke": True,
                    "color": "#09f005",
                    "weight": 3,
                    "opacity": 1,
                    "fill": False,
                    "fillColor": "blue",
                    "fillOpacity": 0,
                    "clickable": False
    }

    #m.add_ee_layer(eelter_object, style, 'eLTER sites')
    for k, v in deimsDict.items():
        m.add_elter_sites(v, style, k)
    m.centerObject(eelter_object)


    output_widget = widgets.Output(layout={'border': '1px solid black'})
    output_control = ipyleaflet.WidgetControl(widget=output_widget, position='bottomright')
    m.add_control(output_control)

    output_widget.clear_output()
    logo = widgets.HTML(
        value='<img src="https://pbs.twimg.com/profile_images/1310893180234141697/XbUuptdr_400x400.jpg" width="50px" height="50px">')
    with output_widget:
        display(logo)

    #m.add_shapefile(lter_shp, style=style, layer_name='eLTER sites')
    #m.centerObject(eelter_object, 5)

    widget_width = "350px"
    padding = "0px 0px 0px 4px"  # upper, right, bottom, left
    style = {"description_width": "initial"}

    toolbar_button = widgets.ToggleButton(
        value=False,
        tooltip="Toolbar",
        icon="leaf",
        button_style="success",
        layout=widgets.Layout(width="28px", height="28px", padding="0px 0px 0px 4px"),
    )

    close_button = widgets.ToggleButton(
        value=False,
        tooltip="Close the tool",
        icon="times",
        button_style="primary",
        layout=widgets.Layout(height="28px", width="28px", padding="0px 0px 0px 4px"),
    )

    #Here we start the changes
    network = widgets.Dropdown(
        options=[i for i in networks.keys()],
        value=None,
        description="eLTER Network:",
        layout=widgets.Layout(width=widget_width, padding=padding),
        style=style,
    )

    site = widgets.Dropdown(
        options=[],
        value=None,
        description="eLTER Site:",
        layout=widgets.Layout(width=widget_width, padding=padding),
        style=style,
    )

    collection = widgets.Dropdown(
        options=[
            "Sentinel 2 HR-VPP Phenology Products",
            "Sentinel-2AB Phenopy",
            "MODIS MCD12Q2.006",
        ],
        value="Sentinel-2AB Phenopy",
        description="Collection:",
        layout=widgets.Layout(width=widget_width, padding=padding),
        style=style,
    )

    ndvi2gif = widgets.Checkbox(
        value=True,
        description="Show Ndvi2Gif NDVI composite",
        tooltip="Show last seasons NDVI percentile 90 composite",
        style=style,
    )

    legend = widgets.Checkbox(
        value=False,
        description="Show Raster legend",
        tooltip="Show legend for the current raster",
        style=style,
    )

    start_year = widgets.IntSlider(
        description="Year:",
        value=2017,
        min=2001,
        max=2021,
        readout=False,
        style=style,
        layout=widgets.Layout(width="320px", padding=padding),
    )

    start_year_label = widgets.Label()
    widgets.jslink((start_year, "value"), (start_year_label, "value"))

    #NEED TO ADD LOS RASTERS
    phenometrics = widgets.RadioButtons(
        concise=False,
        description="Metric:",
        options=['SOS', 'MOS', 'EOS'],
        value='SOS',
        style=style,
        layout=widgets.Layout(width="50%", padding="0px 0px 0px 0px"),
        )

    phenometrics_val = widgets.RadioButtons(
        concise=False,
        description="Metric Value:",
        options=['Doy', 'Value'],
        value='Doy',
        style=style,
        layout=widgets.Layout(width="50%", padding="0px 0px 0px 0px"),
        )
    
    rdlist = widgets.Dropdown(
        options=[],
        value=None,
        description="Raster to download:",
        layout=widgets.Layout(width=widget_width, padding=padding),
        style = {'description_width': 'initial'},
    )

    scale = widgets.IntSlider(
    value=30,
    min=10,
    max=1000,
    step=10,
    description='Scale:',
    disabled=False,
    continuous_update=False,
    orientation='horizontal',
    readout=True,
    readout_format='d',
    layout=widgets.Layout(width="320px", padding=padding),
    )

    crs = widgets.Text(
    value='4326',
    style = {'description_width': 'initial'},
    description='CRS (EPSG code)',
    layout=widgets.Layout(width="250px", padding=padding),
    )   

    output_name = widgets.Text(
    value='Insert the name',
    style = {'description_width': 'initial'},
    description='Output raster',
    layout=widgets.Layout(width="250px"),
    )   

    def network_change(change):

        #country_sites = {}
        if change['new']:

            # recorro una red nacional
            country_list = deims.getListOfSites(networks[change['new']])

            for i in country_list:        
                #print(i)        
                name = deims.getSiteById(i)['title'].split(' - ')[0]
                #print(name)        
                geom = deims.getSiteBoundaries(i)['geometry']
                if len(geom) != 0:
                    country_sites[name] = gdf_to_ee(deims.getSiteBoundaries(i))
                else:
                    continue 
            
            site.options = [i for i in list(country_sites.keys())]
            # geom = eLTER_SITES[change['new']][1]
            # title = eLTER_SITES[change['new']][0]
            # m.centerObject(geom)
            
            # with output:
            #     output.clear_output()
            #     print('eLTER Title:', title)
                
    network.observe(network_change, "value")

    def site_change(change):

        #print(country_sites)
        if change['new']:
            
            geom = country_sites[change['new']]
            #title = eLTER_SITES[change['new']][0]
            m.centerObject(geom)
            if ndvi2gif.value==True:

                MyClass = NdviSeasonality(roi=geom, sat='S2', key='perc_90', periods=4,start_year=2018, end_year=2022, index='ndvi')
                median = MyClass.get_year_composite().mean()
                vizParams = {'bands': ['spring', 'autumn', 'winter'], 'min': 0.15, 'max': 0.8}
                m.addLayer(median, vizParams, 'perc_90')

            # with output:
            #     output.clear_output()
            #     print('eLTER Title:', title)
                
    site.observe(site_change, "value")


    def legend_change(c):   

        if legend.value == True and phenometrics_val.value == 'Doy':

            cur_date = datetime.date(start_year.value, 1, 1) #Today's date
            epoch_date = datetime.date(1970, 1, 1) #Jan 1 1970
            min_val = (cur_date - epoch_date).days
            max_val = min_val + 365

            legend_keys = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 
            'September', 'October', 'November', 'December']
            legend_colors = ['#54478C', '#2C699A', '#048BA8', '#EFEA5A', '#F1C453', '#F29E4C', '#d00000', 
                '#9d0208', '#B9E769', '#83E377', '#16DB93', '#0DB39E']  

            m.add_legend(labels=legend_keys, colors=legend_colors, title="Month", position='bottomleft')   

            
            with output:
                output.clear_output()
                print('Display legend')


        elif legend.value == True and phenometrics_val.value == 'Value':
    
            legend_keys = [-1, -0.7, -0.5, -0.3, 0, 0.3, 0.5, 0.7, 1]
            legend_colors = ['f5cb5c', 'fee440', '9ef01a', '70e000', '38b000', '008000', '007200', '006400', '004b23']

            m.add_legend(labels=legend_keys, colors=legend_colors, title="NDVI", position='bottomleft')
            #m.add_colorbar_branca(colors=legend_colors, vmin=-1, vmax=1, width="75px", layer_name="NDVI", position='bottomleft') 

        else:

            m.legend_widget.close()


                
    legend.observe(legend_change, "value")


    button_width = "113px"
    load_rasters = widgets.Button(
        description="Apply",
        button_style="primary",
        tooltip="Load the selected phenometrics",
        style=style,
        layout=widgets.Layout(padding="0px", width=button_width),
    )

    

    def submit_clicked(b):

        if collection.value != "MODIS MCD12Q2.006" and start_year.value < 2017:
            print("Sentinel 2 data is only available since 2017")
            return
        # if start_year.value == end_year.value:
        #     add_progress_bar = False
        # else:
        #     add_progress_bar = True

        start_date = str(start_year.value) + "-01-01"
        end_date = str(start_year.value) + "-12-31"

        cur_date = datetime.date(start_year.value, 1, 1) #Today's date
        epoch_date = datetime.date(1970, 1, 1) #Jan 1 1970
        min_val = (cur_date - epoch_date).days
        max_val = min_val + 365

        dataset = {'MODIS MCD12Q2.006': ee.ImageCollection('MODIS/006/MCD12Q2')}
        bands = {'SOS': 'Greenup_1', 'MOS': 'Peak_1', 'EOS': 'Senescence_1', 'LOS': 'EVI_Amplitude_1'}

        with output:
            print("Loading data... Please wait...")

        # nd_bands = None
        # if (first_band.value is not None) and (second_band.value is not None):
        #     nd_bands = [first_band.value, second_band.value]

        temp_output = widgets.Output()

        if m is not None and collection.value == "MODIS MCD12Q2.006":
            
            geom = country_sites[site.value]    
            dataset = dataset[collection.value].filterBounds(geom).filterDate(start_date, end_date)
            clipped = dataset.map(lambda image: image.clip(geom))
            banda = bands[phenometrics.value]
            vegetationrs = clipped.select(banda).first()

            modis_vis = {
                'min': min_val,
                'max': max_val,
                'palette': ['#54478C', '#2C699A', '#048BA8', '#EFEA5A', '#F1C453', '#F29E4C', '#d00000', 
                '#9d0208', '#B9E769', '#83E377', '#16DB93', '#0DB39E']
            }

            name = phenometrics.value + ' ' + phenometrics_val.value + ' ' + str(start_year.value)
            #print(name)

            downloads_images[name] = [vegetationrs, geom]
            #print(downloads_images)
            rdlist.options = [i for i in list(downloads_images.keys())]
            m.addLayer(vegetationrs, modis_vis, name)


        elif m is not None and collection.value != "MODIS MCD12Q2.006":
            
            if phenometrics.value == 'MOS':
                keyPhen = 'MAX'
            else:
                keyPhen = phenometrics.value

            #Aqui hay que poner el site como variable
            #Vamos a mapear el nombre de los sites a los assets de GEE
            dnames = {"Doñana Long-Term Socio-ecological Research Platform": "Donana",
                      "Braila Islands": "Braila",
                      "LTSER-Sabor": "Baixo",
                      "River Exe": "River_Exe",
                      "Cairngorms National Park LTSER": "Cairngorms",
                      "LTSER Veluwe": "Veluwe",
                      "Gran Paradiso National Park": "Gran_Paradiso",
                      "Schorfheide-Chorin": "Schorfheide",
                      "LTSER Platform Neusiedler See": "Neusiedler"}
            
            if site.value in dnames.keys():
                pheno_name = dnames[site.value]
            else:
                pheno_name = site.value
            base = 'projects/ee-digdgeografo/assets/{}_{}_{}{}'.format(pheno_name, start_year.value, keyPhen, 
                                                                       str(phenometrics_val.value)[0])
            nbase = ee.Image(base)
            geom = country_sites[site.value]    

            #print(base)
            #geom = eLTER_SITES[site.value][1]   
            #dataset = dataset[collection.value].filterBounds(geom).filterDate(start_date, end_date)
            #clipped = dataset.map(lambda image: image.clip(geom))
            #banda = bands[phenometrics.value]

            #vegetationrs = clipped.select(banda)
            if phenometrics_val.value == 'Doy':

                mini = int(str(start_year.value)[-2:] + '000')
                maxi = int(str(start_year.value)[-2:] + '000') + 365

                #print(mini, maxi)

                s2_vis_ = {
                    'min': mini,
                    'max': maxi,
                    'palette': ['#54478C', '#2C699A', '#048BA8', '#EFEA5A', '#F1C453', '#F29E4C', '#d00000', 
                    '#9d0208', '#B9E769', '#83E377', '#16DB93', '#0DB39E']
                }

                name = phenometrics.value + ' ' + phenometrics_val.value + ' ' + str(start_year.value)
                #print(name)

                downloads_images[name] = [nbase, geom]
                rdlist.options = [i for i in list(downloads_images.keys())]
                m.addLayer(nbase, s2_vis_, name)

            else:

                s2_vis = {
                    'min': 0,
                    'max': 10000,
                    'palette': ['f5cb5c', 'fee440', '9ef01a', '70e000', '38b000', '008000', '007200', '006400', '004b23']
                }

                name = phenometrics.value + ' ' + phenometrics_val.value + ' ' + str(start_year.value)
                #print(name)

                downloads_images[name] = [nbase, geom]
                rdlist.options = [i for i in list(downloads_images.keys())]
                m.addLayer(nbase, s2_vis, name)


            with output:

                output.clear_output()
                print("The raster has been added to the map.")

    load_rasters.on_click(submit_clicked)

    reset_btn = widgets.Button(
        description="Reset",
        button_style="primary",
        style=style,
        layout=widgets.Layout(padding="0px", width=button_width),
    )

    def reset_btn_click(change):
        output.clear_output()

    reset_btn.on_click(reset_btn_click)

    dwlnd_btn = widgets.Button(
        description="Download",
        button_style="primary",
        style=style,
        layout=widgets.Layout(padding="0px", width=button_width),
    )

    def dwlnd_btn_click(change):
        
        sc = scale.value
        crs_ = "EPSG:"+ crs.value
        rs = rdlist.value
        outname = output_name.value
        download_ee_image(downloads_images[rs][0], outname, scale=sc, region=downloads_images[rs][1].geometry(), crs=crs_)
        print('Downloading raster to the current folder... Por dios ya...')

    dwlnd_btn.on_click(dwlnd_btn_click)
 

    output = widgets.Output(layout=widgets.Layout(width=widget_width, padding=padding))

    tab1 = widgets.VBox(children=[crs, scale, output_name])
    rdlist.options = [i for i in list(downloads_images.keys())]
    tab2 = widgets.VBox(children=[rdlist])
    tab = widgets.Tab(children=[tab2, tab1])
    tab.set_title(1, 'Download Options')
    tab.set_title(0, 'Rasters list')

    toolbar_widget = widgets.VBox(layout=widgets.Layout(border="solid green"))
    toolbar_widget.children = [toolbar_button]
    toolbar_header = widgets.HBox()
    toolbar_header.children = [close_button, toolbar_button]
    toolbar_footer = widgets.VBox()
    toolbar_footer.children = [
        network,
        site,
        collection,
        widgets.HBox([start_year, start_year_label]),
        widgets.HBox([phenometrics, phenometrics_val]),
        ndvi2gif,
        legend,
        tab,
        widgets.HBox([load_rasters, dwlnd_btn, reset_btn]),
        output,
    ]

    toolbar_event = ipyevents.Event(
        source=toolbar_widget, watched_events=["mouseenter", "mouseleave"]
    )

    def handle_toolbar_event(event):

        if event["type"] == "mouseenter":
            toolbar_widget.children = [toolbar_header, toolbar_footer]
        elif event["type"] == "mouseleave":
            if not toolbar_button.value:
                toolbar_widget.children = [toolbar_button]
                toolbar_button.value = False
                close_button.value = False

    toolbar_event.on_dom_event(handle_toolbar_event)

    def toolbar_btn_click(change):
        if change["new"]:
            close_button.value = False
            toolbar_widget.children = [toolbar_header, toolbar_footer]
        else:
            if not close_button.value:
                toolbar_widget.children = [toolbar_button]

    toolbar_button.observe(toolbar_btn_click, "value")

    def close_btn_click(change):
        if change["new"]:
            toolbar_button.value = False
            if m is not None:
                if m.tool_control is not None and m.tool_control in m.controls:
                    m.remove_control(m.tool_control)
                    m.tool_control = None
                m.toolbar_reset()
            toolbar_widget.close()

    close_button.observe(close_btn_click, "value")

    toolbar_button.value = True
    if m is not None:
        toolbar_control = ipyleaflet.WidgetControl(
            widget=toolbar_widget, position="topright"
        )

        if toolbar_control not in m.controls:
            m.add_control(toolbar_control)
            m.tool_control = toolbar_control
    else:
        return toolbar_widget
    


##############################################################################################################
##############################################################################################################
##############################################################################################################
      
def WaterDetect(m=None):

    """Showing water extent for eLTER sites

    Args:
        m (geemap.Map, optional staellite collection and phenometrics DOY or value): A geemap Map instance. Defaults to None.

    Returns:
        ipywidgets: The interactive GUI.
    """

    if m is not None:
        m.add_basemap("Esri.WorldImagery")

    

    #############################################
    # eLTER sites stuffs
    #############################################

    #Adding eLETR shapes through deimsPY
    
    eelter_object = ee.FeatureCollection('projects/ee-digdgeografo/assets/elter_lyon')

    deimsDict = {'Donana': "bcbc866c-3f4f-47a8-bbbc-0a93df6de7b2",
                 'Braila_Island': "d4854af8-9d9f-42a2-af96-f1ed9cb25712",
                 'Baixo': "45722713-80e3-4387-a47b-82c97a6ef62b",
                 'River_Exe': "b8e9402a-10bc-4892-b03d-1e85fc925c99",
                 'Cairngorms': "1b94503d-285c-4028-a3db-bc78e31dea07",
                 'Veluwe': "bef0bbd2-d8a9-4672-9e5b-085d049f4879",
                 'Gran_Paradiso': "15c3e841-8494-42d2-a44e-c49a0ff25946",
                 'Schorfheide': "94c53dd1-acad-4ad8-a73b-62669ec7af2a",
                 'Neusiedler': "1230b149-9ba5-4ab8-86c9-cf93120f8ae2"}

    networks = {"Austria": "d45c2690-dbef-4dbc-a742-26ea846edf28",
            "Belgica": "735946e0-4e9e-484a-acee-85e31f4e2a2e",
            "Bulgaria": "20ad4fa2-cc07-4848-b9ed-8952c55f1a3f",
            "Denmark": "e3911e8a-ce9b-46ce-8265-c2dc9676ad03",
            "Finland": "aaae2a46-f355-41d0-8067-c2f0cd52e814",
            "France": "d8d9206f-b1bd-4f90-84b7-8c662d4235a2",
            "Germany": "e904354a-f3a0-40ce-a9b5-61741f66c824",
            "Greece": "83453a6c-792d-4549-9dbb-c17ced2e0cc3",
            "Hungary": "0615a89f-2883-47ab-8cd0-2508f413cab7",
            "Israel": "e0f680c2-22b1-4424-bf54-58aa9b7476a0",
            "Italy": "7fef6b73-e5cb-4cd2-b438-ed32eb1504b3",
            "Netherlands": "8312c2c4-a787-4986-9a3d-3f1364bab3ba",
            "Norway": "bc7c517b-3648-40cc-a04c-8c98d009c4a9",
            "Poland": "67763729-45a7-4248-a70d-622b1d0a3d41",
            "Portugal": "d8eb4823-b707-4590-94d8-d90c1d07d6f8",
            "Romania": "4260f964-0ac4-4406-8adc-5afc06e31779",
            "Slovakia": "3d6a8d72-9f86-4082-ad56-a361b4cdc8a0",
            "Slovenia": "fda2984f-9aea-4abf-9f6c-c3eca0f82eb8",
            "Spain": "2b70f1fb-f7d9-4615-a1a3-33fc6fa44600",
            "Sweden": "a50d9e39-d4b6-4d30-bba2-43580ac8c0b2",
            "Switzerland": "cedf695c-c6dc-4660-b944-3c22f12ad0d9"}

    country_sites = {}    

    for k, v in deimsDict.items():
        eLTER_SITES[k] = [deims.getSiteById(v)['title'], gdf_to_ee(deims.getSiteBoundaries(v))]

    # Shape Styling

    style = {
                    "stroke": True,
                    "color": "#2CEBF4",
                    "weight": 3,
                    "opacity": 0.5,
                    "fill": False,
                    "fillColor": "blue",
                    "fillOpacity": 0,
                    "clickable": False
    }

    #m.add_ee_layer(eelter_object, style, 'eLTER sites')
    for k, v in deimsDict.items():
        m.add_elter_sites(v, style, k)
    m.centerObject(eelter_object)


    #############################################
    # GEE collections stuffs
    #############################################


    LC09col = ee.ImageCollection("LANDSAT/LC09/C02/T1_L2")#.filterBounds(self.roi) 
    LC08col = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")#.filterBounds(self.roi) 
    LE07col = ee.ImageCollection("LANDSAT/LE07/C02/T1_L2")#.filterBounds(self.roi) 
    LT05col = ee.ImageCollection("LANDSAT/LT05/C02/T1_L2")#.filterBounds(self.roi) 
    LT04col = ee.ImageCollection("LANDSAT/LT04/C02/T1_L2")#.filterBounds(self.roi) 
    
    OLI = LC09col.merge(LC08col)
    ETM = LE07col.merge(LT05col).merge(LT04col)
    OLI_ = OLI.map(scale_OLI) 
    ETM_ = ETM.map(scale_ETM)
    Landsat = OLI_.merge(ETM_)
    
    # Notice that S2 is not in Surface Reflectance but in TOA, this because otherwise only
    # had data starting in 2017. Using BOA we have 2 extra years, starting at 2015
    # We use the wide 8 band instead of the 8A narrower badn, that is also more similar to landsat NIR
    # But this way we have NDVI at 10 m instead of 20. And we are using TOA instead of SR so, who cares?
    
    #"COPERNICUS/S2_SR_HARMONIZED"
    S2col = ee.ImageCollection("COPERNICUS/S2_HARMONIZED").select(['B2', 'B3', 'B4', 'B8', 'B11', 'B12'], 
                                                                        ['Blue', 'Green', 'Red', 'Nir', 'Swir1', 'Swir2'])#.filterBounds(self.roi)
    
    
    collections = {'Landsat': Landsat, 'Sentinel 2': S2col}


    #############################################
    # Widgets stuffs
    #############################################


    output_widget = widgets.Output(layout={'border': '1px solid black'})
    output_control = ipyleaflet.WidgetControl(widget=output_widget, position='bottomright')
    m.add_control(output_control)

    output_widget.clear_output()
    logo = widgets.HTML(
        value='<img src="https://pbs.twimg.com/profile_images/1310893180234141697/XbUuptdr_400x400.jpg" width="50px" height="50px">')
    with output_widget:
        display(logo)

    #m.add_shapefile(lter_shp, style=style, layer_name='eLTER sites')
    #m.centerObject(eelter_object, 5)

    widget_width = "350px"
    padding = "0px 0px 0px 4px"  # upper, right, bottom, left
    style = {"description_width": "initial"}

    toolbar_button = widgets.ToggleButton(
        value=False,
        tooltip="Toolbar",
        icon="tint",
        button_style="info",
        layout=widgets.Layout(width="28px", height="28px", padding="0px 0px 0px 4px"),
    )

    close_button = widgets.ToggleButton(
        value=False,
        tooltip="Close the tool",
        icon="times",
        button_style="primary",
        layout=widgets.Layout(height="28px", width="28px", padding="0px 0px 0px 4px"),
    )

    #Here we start the changes
    network = widgets.Dropdown(
        options=[i for i in networks.keys()],
        value=None,
        description="eLTER Network:",
        layout=widgets.Layout(width=widget_width, padding=padding),
        style=style,
    )

    site = widgets.Dropdown(
        options=[],
        value=None,
        description="eLTER Site:",
        layout=widgets.Layout(width=widget_width, padding=padding),
        style=style,
    )

    collection = widgets.Dropdown(
        options=[
            "Landsat",
            "Sentinel 2"
        ],
        value="Sentinel 2",
        description="Collection:",
        layout=widgets.Layout(width=widget_width, padding=padding),
        style=style,
    )

    start_date = widgets.DatePicker(
        description="Start date:",
        disabled=False,
        value=None,
        style=style,
        layout=widgets.Layout(width="200px", padding=padding),
    )
    end_date = widgets.DatePicker(
        description="End date:",
        disabled=False,
        value=None,
        style=style,
        layout=widgets.Layout(width="200px", padding=padding),
    )


    ndvi2gif = widgets.Checkbox(
        value=True,
        description="Show Ndvi2Gif NDWI composite",
        tooltip="Show last seasons NDWI median composite",
        style=style,
    )

    legend = widgets.Checkbox(
        value=False,
        description="Show Raster legend",
        tooltip="Show legend for the current raster",
        style=style,
    )

    mask = widgets.Checkbox(
        value=False,
        description="Apply threshold mask to the water index",
        tooltip="Apply water index mask based on the threshold value",
        style=style,
    )

    clouds = widgets.IntSlider(
        description="Clouds:",
        value=10,
        min=0,
        max=100,
        readout=False,
        style=style,
        layout=widgets.Layout(width="320px", padding=padding),
    )

    clouds_label = widgets.Label()
    widgets.jslink((clouds, "value"), (clouds_label, "value"))

    threshold = widgets.FloatSlider(
        description="Threshold:",
        value=0,
        min=-1,
        max=1,
        step=0.01,
        readout_format='.2f',
        readout=False,
        style=style,
        layout=widgets.Layout(width="320px", padding=padding),
    )

    threshold_label = widgets.Label()
    widgets.jslink((threshold, "value"), (threshold_label, "value"))

    # Indexes
    windex = widgets.Dropdown(
        options=['NDWI_McFeeters', 'NDWI_Gao', 'MNDWI', 'AWEI', 'SWIR2'],
        value='MNDWI',
        description="Water Index:",
        layout=widgets.Layout(width=widget_width, padding=padding),
        style=style,
    )

    # Stats
    compendium = widgets.Dropdown(
        options=['Max', 'Min', 'Mean', 'Median', 'Percentile 10', 'Percentile 20', 'Percentile 90', 'Percentile 95'],
        value=None, 
        description="Statistics Per Pixel:",
        layout=widgets.Layout(width=widget_width, padding=padding),
        style=style,
    )

    rdlist = widgets.Dropdown(
        options=[],
        value=None,
        description="Raster to download:",
        layout=widgets.Layout(width=widget_width, padding=padding),
        style = {'description_width': 'initial'},
    )

    scale = widgets.IntSlider(
    value=30,
    min=10,
    max=1000,
    step=10,
    description='Scale:',
    disabled=False,
    continuous_update=False,
    orientation='horizontal',
    readout=True,
    readout_format='d',
    layout=widgets.Layout(width="320px", padding=padding),
    )

    crs = widgets.Text(
    value='4326',
    style = {'description_width': 'initial'},
    description='CRS (EPSG code)',
    layout=widgets.Layout(width="250px", padding=padding),
    )   

    output_name = widgets.Text(
    value='Insert the name',
    style = {'description_width': 'initial'},
    description='Output raster',
    layout=widgets.Layout(width="250px"),
    )   


    def network_change(change):

        #country_sites = {}
        if change['new']:

            # recorro una red nacional
            country_list = deims.getListOfSites(networks[change['new']])

            for i in country_list:        
                #print(i)        
                name = deims.getSiteById(i)['title'].split(' - ')[0]
                #print(name)        
                geom = deims.getSiteBoundaries(i)['geometry']#geemap.gdf_to_ee(deims.getSiteBoundaries(i))
                if len(geom) != 0:
                    country_sites[name] = gdf_to_ee(deims.getSiteBoundaries(i))
                else:
                    continue 
            
            site.options = [i for i in list(country_sites.keys())]
            # geom = eLTER_SITES[change['new']][1]
            # title = eLTER_SITES[change['new']][0]
            # m.centerObject(geom)
            
            # with output:
            #     output.clear_output()
            #     print('eLTER Title:', title)
                
    network.observe(network_change, "value")

    def site_change(change):

        #print(country_sites)
        if change['new']:
            
            geom = country_sites[change['new']]
            #title = eLTER_SITES[change['new']][0]
            m.centerObject(geom)
            if ndvi2gif.value==True:

                MyClass = NdviSeasonality(roi=geom, sat='S2', key='perc_90', periods=4,start_year=2018, end_year=2022, index='ndvi')
                median = MyClass.get_year_composite().mean()
                vizParams = {'bands': ['spring', 'autumn', 'winter'], 'min': 0.15, 'max': 0.8}
                m.addLayer(median, vizParams, 'perc_90')

            # with output:
            #     output.clear_output()
            #     print('eLTER Title:', title)
                
    site.observe(site_change, "value")


    def legend_change(c):   


        if legend.value == True:
    
            legend_keys = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1]
            #legend_colors = ['f5cb5c', 'fee440', '9ef01a', '70e000', '38b000', '008000', '007200', '006400', '004b23']
            legend_colors = ['#FFFFFF', '#E0E4F1', '#C1C9E4', '#A1ADD6', '#8292C8', '#6377BA', '#445CAD', '#24409F', '#052591', '#031C6C', '#000B2F']
            m.add_legend(labels=legend_keys, colors=legend_colors, title=str(windex.value), position='bottomleft')

            with output:
                output.clear_output()
                print('Showing legend...')

        else:
            m.legend_widget.close()


    legend.observe(legend_change, "value")


    button_width = "113px"
    load_rasters = widgets.Button(
        description="Apply",
        button_style="primary",
        tooltip="Load the flood mask product",
        style=style,
        layout=widgets.Layout(padding="0px", width=button_width),
    )

    

    def submit_clicked(b):

        #####################################################################
        #functions to compute water indexes
        #####################################################################

        def get_ndvi(image):

            '''Here we apply the NDVI calculation'''   

            return image.normalizedDifference(['Nir', 'Red']).rename('NDVI')
        
        def get_bsi(image):

            '''Here we apply the BSI calculation'''
            # Compute the SAVI using an expression.
            return image.expression(
                ('((SWIR2 + RED)-(NIR + BLUE)) / ((SWIR2 + RED)+(NIR + BLUE))'), {
                'NIR': image.select('Nir'),
                'BLUE': image.select('Blue'),
                'RED': image.select('Red'),
                'SWIR1':image.select('Swir1'),
                'SWIR2':image.select('Swir2')}).rename(['BSI'])

        
        def get_mndwi(image):

            '''Here we apply the NDVI calculation'''   

            return image.normalizedDifference(['Green', 'Swir1']).rename('MNDWI')
        
        def get_ndwi_McFeeters(image):

            '''Here we apply the NDWI calculation'''   

            return image.normalizedDifference(['Green', 'Nir']).rename('NDWI_McFeeters')
        
        def get_ndwi_gao(image):

            '''Here we apply the NDWI calculation'''   

            return image.normalizedDifference(['Nir', 'Swir1']).rename('NDWI_Gao')
    
        def get_awei(image):
            
            '''Here we apply the SAVI calculation'''   

            # Compute the SAVI using an expression.
            return image.expression(
                ('BLUE + 2.5 * GREEN - 1.5 * (NIR + SWIR1) - 0.25 * SWIR2'), {
                'NIR': image.select('Nir'),
                'BLUE': image.select('Blue'),
                'GREEN': image.select('Green'),
                'SWIR1':image.select('Swir1'),
                'SWIR2':image.select('Swir2')}).rename(['AEWI'])
        
        def get_swir2(image):

            '''Here we apply the NDWI calculation'''   
            if collection.value == 'Sentinel 2':
                return image.select('Swir2').divide(1000).rename('SWIR2')
            elif collection.value == 'Landsat':
                return image.select('Swir2').rename('SWIR2')
            else:
                print('Please, check your collection choice')
        
        d = {'NDWI_McFeeters': get_ndwi_McFeeters, 
             'NDWI_Gao': get_ndwi_gao,  
             'AWEI': get_awei, 
             'MNDWI': get_mndwi,
             'SWIR2': get_swir2}

        #col = collection.value

        sdate = str(start_date.value)
        edate = str(end_date.value)
        col = collections[collection.value]

        with output:
            print("Loading data... Please wait...")

        # nd_bands = None
        # if (first_band.value is not None) and (second_band.value is not None):
        #     nd_bands = [first_band.value, second_band.value]

        temp_output = widgets.Output()

        if m is not None:
            
            geom = country_sites[site.value]
            
            if collection.value == 'Sentinel 2':
                dataset = col.filterBounds(geom).filterDate(ee.Date(sdate), 
                    ee.Date(edate)).filterMetadata('CLOUDY_PIXEL_PERCENTAGE', 'less_than', int(clouds.value))
            elif collection.value == 'Landsat':
                dataset = col.filterBounds(geom).filterDate(ee.Date(sdate), 
                    ee.Date(edate)).filterMetadata('CLOUD_COVER', 'less_than', int(clouds.value))
            else:
                print('Please, check your collection choice')

            clipped = dataset.map(lambda image: image.clip(geom))
            # Add ndvi band to clipped collection

            clipped = clipped.map(lambda image: image.addBands(get_ndvi(image)))
            clipped = clipped.map(lambda image: image.addBands(get_mndwi(image)))
            clipped = clipped.map(lambda image: image.addBands(get_ndwi_McFeeters(image)))
            clipped = clipped.map(lambda image: image.addBands(get_ndwi_gao(image)))
            clipped = clipped.map(lambda image: image.addBands(get_awei(image)))
            clipped = clipped.map(lambda image: image.addBands(get_bsi(image)))
            clipped = clipped.map(lambda image: image.addBands(get_swir2(image)))

            #banda = clipped.map(d[windex.value])
            banda = clipped.select(windex.value)
            #vegetationrs = clipped.select(banda)

            nor_vis = {
                'min': 0,
                'max': 1,
                'palette': ['FAFBFF', 'DDE3FB', 'C1CCF7', 'A4B4F3', '889CEF', '6B84EB', '4E6DE7ff', '3255E3ff', '153DDFff']
            }


            if compendium.value == 'Max':
                banda = banda.max()
            elif compendium.value == 'Min':
                banda = banda.min()
            elif compendium.value == 'Mean':
                banda = banda.mean()
            elif compendium.value == 'Median':
                banda = banda.median()
            elif compendium.value == 'Percentile 10':
                banda = banda.reduce(ee.Reducer.percentile([10]))
            elif compendium.value == 'Percentile 20':
                banda = banda.reduce(ee.Reducer.percentile([20]))
            elif compendium.value == 'Percentile 90':
                banda = banda.reduce(ee.Reducer.percentile([90]))
            elif compendium.value == 'Percentile 95':
                banda = banda.reduce(ee.Reducer.percentile([95]))
            else:
                banda = banda.median()

            # Here we apply the mask
            if mask.value == True:
                if windex.value != 'SWIR2':  
                    banda = banda.updateMask(banda.gte(threshold.value))
                    name = windex.value + ' ' + collection.value + ' ' + compendium.value + ' ' + 'Masked'
                    m.addLayer(banda, nor_vis, name)
                elif windex.value == 'SWIR2':
                    nor_vis = {
                    'min': 0,
                    'max': 1,
                    'palette': ['153DDFff', '3255E3ff', '4E6DE7ff', '6B84EB', '889CEF', 'A4B4F3', 'C1CCF7', 'DDE3FB', 'FAFBFF']
            }
                    #print('estoy en swir')
                    banda = banda.updateMask(banda.lte(threshold.value))
                    name = windex.value + ' ' + collection.value + ' ' + compendium.value + ' ' + 'Masked'
                    m.addLayer(banda, nor_vis, name)
                else:
                    print('Please, check your water index choice')

                # We made a dict with the images loaded in the map, key is the name and image and geometry are the values for each entry
                downloads_images[name] = [banda, geom]
                rdlist.options = [i for i in list(downloads_images.keys())]
                m.addLayer(clipped.median(), {'bands': ['Swir1', 'Nir', 'Blue'], 'min': 0, 'max': 3000}, 'Composite RGB', False)
                m.addLayer(clipped.median(), {'bands': ['BSI', 'NDVI', 'MNDWI'], 'min': -0.5, 'max': 0.8}, 'Composite Indexes', False)
                
            else:

                banda = banda
                name = windex.value + ' ' + collection.value + ' ' + compendium.value

                # We made a dict with the images loaded in the map, key is the name and image and geometry are the values for each entry
                downloads_images[name] = [banda, geom]
                rdlist.options = [i for i in list(downloads_images.keys())]

                if windex.value != 'SWIR2':
                    nor_vis = nor_vis
                elif windex.value == 'SWIR2':
                    nor_vis = {
                    'min': 0,
                    'max': 1,
                    'palette': ['153DDFff', '3255E3ff', '4E6DE7ff', '6B84EB', '889CEF', 'A4B4F3', 'C1CCF7', 'DDE3FB', 'FAFBFF']
                }
                m.addLayer(clipped.median(), {'bands': ['Swir1', 'Nir', 'Blue'], 'min': 0, 'max': 3000}, 'Composite RGB', False)
                m.addLayer(clipped.median(), {'bands': ['BSI', 'NDVI', 'MNDWI'], 'min': -0.5, 'max': 0.8}, 'Composite Indexes', False)
                m.addLayer(banda, nor_vis, name)

            
            # Let's also add a beautiful RGB image to the map
            


            with output:

                output.clear_output()
                print("The raster has been added to the map.")
    
    load_rasters.on_click(submit_clicked)

    reset_btn = widgets.Button(
        description="Reset",
        button_style="primary",
        style=style,
        layout=widgets.Layout(padding="0px", width=button_width),
    )

    def reset_btn_click(change):
        output.clear_output()

    reset_btn.on_click(reset_btn_click)

    dwlnd_btn = widgets.Button(
        description="Download",
        button_style="primary",
        style=style,
        layout=widgets.Layout(padding="0px", width=button_width),
    )

    def dwlnd_btn_click(change):
        
        sc = scale.value
        crs_ = "EPSG:"+ crs.value
        rs = rdlist.value
        outname = output_name.value
        download_ee_image(downloads_images[rs][0], outname, scale=sc, region=downloads_images[rs][1].geometry(), crs=crs_)
        print('Downloading raster to the current folder... Por dios ya...')

    dwlnd_btn.on_click(dwlnd_btn_click)
 
    output = widgets.Output(layout=widgets.Layout(width=widget_width, padding=padding))

    tab1 = widgets.VBox(children=[crs, scale, output_name])
    rdlist.options = [i for i in list(downloads_images.keys())]
    tab2 = widgets.VBox(children=[rdlist])
    tab = widgets.Tab(children=[tab2, tab1])
    tab.set_title(1, 'Download Options')
    tab.set_title(0, 'Rasters list')

    toolbar_widget = widgets.VBox(layout=widgets.Layout(border="solid blue"))
    toolbar_widget.children = [toolbar_button]
    toolbar_header = widgets.HBox()
    toolbar_header.children = [close_button, toolbar_button]
    toolbar_footer = widgets.VBox()
    toolbar_footer.children = [
        network,
        site,
        collection,
        widgets.HBox([start_date, end_date]),
        widgets.HBox([clouds, clouds_label]),
        windex,
        widgets.HBox([threshold, threshold_label]),
        mask,
        compendium, #statistic method
        ndvi2gif,
        legend,
        tab,
        widgets.HBox([load_rasters, dwlnd_btn, reset_btn]),
        output,
    ]

    toolbar_event = ipyevents.Event(
        source=toolbar_widget, watched_events=["mouseenter", "mouseleave"]
    )

    def handle_toolbar_event(event):

        if event["type"] == "mouseenter":
            toolbar_widget.children = [toolbar_header, toolbar_footer]
        elif event["type"] == "mouseleave":
            if not toolbar_button.value:
                toolbar_widget.children = [toolbar_button]
                toolbar_button.value = False
                close_button.value = False

    toolbar_event.on_dom_event(handle_toolbar_event)

    def toolbar_btn_click(change):
        if change["new"]:
            close_button.value = False
            toolbar_widget.children = [toolbar_header, toolbar_footer]
        else:
            if not close_button.value:
                toolbar_widget.children = [toolbar_button]

    toolbar_button.observe(toolbar_btn_click, "value")

    def close_btn_click(change):
        if change["new"]:
            toolbar_button.value = False
            if m is not None:
                if m.tool_control is not None and m.tool_control in m.controls:
                    m.remove_control(m.tool_control)
                    m.tool_control = None
                m.toolbar_reset()
            toolbar_widget.close()

    close_button.observe(close_btn_click, "value")

    toolbar_button.value = True
    if m is not None:
        toolbar_control = ipyleaflet.WidgetControl(
            widget=toolbar_widget, position="topright"
        )

        if toolbar_control not in m.controls:
            m.add_control(toolbar_control)
            m.tool_control = toolbar_control
    else:
        return toolbar_widget


##############################################################################################################
##############################################################################################################
##############################################################################################################
      
def LST(m=None):

    """Showing Land Surface Temperature for eLTER sites

    Args:
        m (geemap.Map, optional staellite collection and phenometrics DOY or value): A geemap Map instance. Defaults to None.

    Returns:
        ipywidgets: The interactive GUI.
    """

    if m is not None:
        m.add_basemap("Esri.WorldImagery")

    

    #############################################
    # eLTER sites stuffs
    #############################################

    #Adding eLETR shapes through deimsPY
    
    eelter_object = ee.FeatureCollection('projects/ee-digdgeografo/assets/elter_lyon')

    deimsDict = {'Donana': "bcbc866c-3f4f-47a8-bbbc-0a93df6de7b2",
                 'Braila_Island': "d4854af8-9d9f-42a2-af96-f1ed9cb25712",
                 'Baixo': "45722713-80e3-4387-a47b-82c97a6ef62b",
                 'River_Exe': "b8e9402a-10bc-4892-b03d-1e85fc925c99",
                 'Cairngorms': "1b94503d-285c-4028-a3db-bc78e31dea07",
                 'Veluwe': "bef0bbd2-d8a9-4672-9e5b-085d049f4879",
                 'Gran_Paradiso': "15c3e841-8494-42d2-a44e-c49a0ff25946",
                 'Schorfheide': "94c53dd1-acad-4ad8-a73b-62669ec7af2a",
                 'Neusiedler': "1230b149-9ba5-4ab8-86c9-cf93120f8ae2"}
    
    networks = {"Austria": "d45c2690-dbef-4dbc-a742-26ea846edf28",
            "Belgica": "735946e0-4e9e-484a-acee-85e31f4e2a2e",
            "Bulgaria": "20ad4fa2-cc07-4848-b9ed-8952c55f1a3f",
            "Denmark": "e3911e8a-ce9b-46ce-8265-c2dc9676ad03",
            "Finland": "aaae2a46-f355-41d0-8067-c2f0cd52e814",
            "France": "d8d9206f-b1bd-4f90-84b7-8c662d4235a2",
            "Germany": "e904354a-f3a0-40ce-a9b5-61741f66c824",
            "Greece": "83453a6c-792d-4549-9dbb-c17ced2e0cc3",
            "Hungary": "0615a89f-2883-47ab-8cd0-2508f413cab7",
            "Israel": "e0f680c2-22b1-4424-bf54-58aa9b7476a0",
            "Italy": "7fef6b73-e5cb-4cd2-b438-ed32eb1504b3",
            "Netherlands": "8312c2c4-a787-4986-9a3d-3f1364bab3ba",
            "Norway": "bc7c517b-3648-40cc-a04c-8c98d009c4a9",
            "Poland": "67763729-45a7-4248-a70d-622b1d0a3d41",
            "Portugal": "d8eb4823-b707-4590-94d8-d90c1d07d6f8",
            "Romania": "4260f964-0ac4-4406-8adc-5afc06e31779",
            "Slovakia": "3d6a8d72-9f86-4082-ad56-a361b4cdc8a0",
            "Slovenia": "fda2984f-9aea-4abf-9f6c-c3eca0f82eb8",
            "Spain": "2b70f1fb-f7d9-4615-a1a3-33fc6fa44600",
            "Sweden": "a50d9e39-d4b6-4d30-bba2-43580ac8c0b2",
            "Switzerland": "cedf695c-c6dc-4660-b944-3c22f12ad0d9"}

    country_sites = {}    

    for k, v in deimsDict.items():
        eLTER_SITES[k] = [deims.getSiteById(v)['title'], gdf_to_ee(deims.getSiteBoundaries(v))]

    # Shape Styling

    style = {
            "stroke": True,
            "color": "#FF5F1F",
            "weight": 3,
            "opacity": 0.5,
            "fill": False,
            "fillColor": "blue",
            "fillOpacity": 0,
            "clickable": False
        }

    #m.add_ee_layer(eelter_object, style, 'eLTER sites')
    for k, v in deimsDict.items():
        m.add_elter_sites(v, style, k)
    m.centerObject(eelter_object)


    #############################################
    # GEE collections stuffs
    #############################################


    LC09col = ee.ImageCollection("LANDSAT/LC09/C02/T1_L2")#.filterBounds(self.roi) 
    LC08col = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")#.filterBounds(self.roi) 
    OLI = LC08col.merge(LC09col)
    Landsat = OLI.map(scale_OLI_ST)
    
    # Notice that S2 is not in Surface Reflectance but in TOA, this because otherwise only
    # had data starting in 2017. Using BOA we have 2 extra years, starting at 2015
    # We use the wide 8 band instead of the 8A narrower badn, that is also more similar to landsat NIR
    # But this way we have NDVI at 10 m instead of 20. And we are using TOA instead of SR so, who cares?
    
    #"MODIS/061/MOD11A1"
    MODIS = ee.ImageCollection("MODIS/061/MOD11A1").map(scale_MODIS_ST)
    
    
    collections = {'Landsat': Landsat, 'MODIS': MODIS}


    #############################################
    # Widgets stuffs
    #############################################


    output_widget = widgets.Output(layout={'border': '1px solid black'})
    output_control = ipyleaflet.WidgetControl(widget=output_widget, position='bottomright')
    m.add_control(output_control)

    output_widget.clear_output()
    logo = widgets.HTML(
        value='<img src="https://pbs.twimg.com/profile_images/1310893180234141697/XbUuptdr_400x400.jpg" width="50px" height="50px">')
    with output_widget:
        display(logo)

    #m.add_shapefile(lter_shp, style=style, layer_name='eLTER sites')
    #m.centerObject(eelter_object, 5)

    widget_width = "350px"
    padding = "0px 0px 0px 4px"  # upper, right, bottom, left
    style = {"description_width": "initial"}

    toolbar_button = widgets.ToggleButton(
        value=False,
        tooltip="Toolbar",
        icon="thermometer-empty",
        button_style="warning",
        layout=widgets.Layout(width="28px", height="28px", padding="0px 0px 0px 4px"),
    )

    close_button = widgets.ToggleButton(
        value=False,
        tooltip="Close the tool",
        icon="times",
        button_style="primary",
        layout=widgets.Layout(height="28px", width="28px", padding="0px 0px 0px 4px"),
    )
    
    #Here we start the changes
    network = widgets.Dropdown(
        options=[i for i in networks.keys()],
        value=None,
        description="eLTER Network:",
        layout=widgets.Layout(width=widget_width, padding=padding),
        style=style,
    )

    site = widgets.Dropdown(
        options=[],
        value=None,
        description="eLTER Site:",
        layout=widgets.Layout(width=widget_width, padding=padding),
        style=style,
    )

    collection = widgets.Dropdown(
        options=[
            "Landsat",
            "MODIS"
        ],
        value="MODIS",
        description="Collection:",
        layout=widgets.Layout(width=widget_width, padding=padding),
        style=style,
    )

    start_date = widgets.DatePicker(
        description="Start date:",
        disabled=False,
        value=None,
        style=style,
        layout=widgets.Layout(width="200px", padding=padding),
    )
    end_date = widgets.DatePicker(
        description="End date:",
        disabled=False,
        value=None,
        style=style,
        layout=widgets.Layout(width="200px", padding=padding),
    )

    ndvi2gif = widgets.Checkbox(
        value=True,
        description="Show Ndvi2Gif NDWI composite",
        tooltip="Show last seasons NDWI median composite",
        style=style,
    )

    legend = widgets.Checkbox(
        value=False,
        description="Show Raster legend",
        tooltip="Show legend for the current raster",
        style=style,
    )

    clouds = widgets.IntSlider(
        description="Clouds:",
        value=10,
        min=0,
        max=100,
        readout=False,
        style=style,
        layout=widgets.Layout(width="75%", padding=padding),
    )

    clouds_label = widgets.Label()
    widgets.jslink((clouds, "value"), (clouds_label, "value"))

    rdlist = widgets.Dropdown(
        options=[],
        value=None,
        description="Raster to download:",
        layout=widgets.Layout(width=widget_width, padding=padding),
        style = {'description_width': 'initial'},
    )

    scale = widgets.IntSlider(
    value=30,
    min=10,
    max=1000,
    step=10,
    description='Scale:',
    disabled=False,
    continuous_update=False,
    orientation='horizontal',
    readout=True,
    readout_format='d',
    layout=widgets.Layout(width="320px", padding=padding),
    )

    crs = widgets.Text(
    value='4326',
    style = {'description_width': 'initial'},
    description='CRS (EPSG code)',
    layout=widgets.Layout(width="250px", padding=padding),
    )   

    output_name = widgets.Text(
    value='Insert the name',
    style = {'description_width': 'initial'},
    description='Output raster',
    layout=widgets.Layout(width="250px"),
    )   

    # Indexes
    windex = widgets.Dropdown(
        options=['ST_B10', 'LST_Day_1km', 'LST_Night_1km'],
        value='LST_Day_1km',
        description="Select the LST band:",
        layout=widgets.Layout(width=widget_width, padding=padding),
        style=style,
    )

    # Stats
    compendium = widgets.Dropdown(
        options=['Max', 'Min', 'Mean', 'Median', 'Percentile 10', 'Percentile 20', 'Percentile 90', 'Percentile 95'],
        value=None, 
        description="Statistics Per Pixel:",
        layout=widgets.Layout(width=widget_width, padding=padding),
        style=style,
    )

    
    def network_change(change):

        #country_sites = {}
        if change['new']:

            # recorro una red nacional
            country_list = deims.getListOfSites(networks[change['new']])

            for i in country_list:        
                #print(i)        
                name = deims.getSiteById(i)['title'].split(' - ')[0]
                #print(name)        
                geom = deims.getSiteBoundaries(i)['geometry']#geemap.gdf_to_ee(deims.getSiteBoundaries(i))
                if len(geom) != 0:
                    country_sites[name] = gdf_to_ee(deims.getSiteBoundaries(i))
                else:
                    continue 
            
            site.options = [i for i in list(country_sites.keys())]
            # geom = eLTER_SITES[change['new']][1]
            # title = eLTER_SITES[change['new']][0]
            # m.centerObject(geom)
            
            # with output:
            #     output.clear_output()
            #     print('eLTER Title:', title)
                
    network.observe(network_change, "value")

    def site_change(change):

        #print(country_sites)
        if change['new']:
            
            geom = country_sites[change['new']]
            #title = eLTER_SITES[change['new']][0]
            m.centerObject(geom)
            if ndvi2gif.value==True:

                MyClass = NdviSeasonality(roi=geom, sat='S2', key='perc_90', periods=4,start_year=2018, end_year=2022, index='ndvi')
                median = MyClass.get_year_composite().mean()
                vizParams = {'bands': ['spring', 'autumn', 'winter'], 'min': 0.15, 'max': 0.8}
                m.addLayer(median, vizParams, 'perc_90')

            # with output:
            #     output.clear_output()
            #     print('eLTER Title:', title)
                
    site.observe(site_change, "value")

    def legend_change(c):   

        if legend.value == True:
    
            legend_keys = [i for i in range(-18, 40, 2)]
            #legend_colors = ['f5cb5c', 'fee440', '9ef01a', '70e000', '38b000', '008000', '007200', '006400', '004b23']
            legend_colors = [
                    '040274', '040281', '0502a3', '0502b8', '0502ce', '0502e6',
                    '0602ff', '235cb1', '307ef3', '269db1', '30c8e2', '32d3ef',
                    '3be285', '3ff38f', '86e26f', '3ae237', 'b5e22e', 'd6e21f',
                    'fff705', 'ffd611', 'ffb613', 'ff8b13', 'ff6e08', 'ff500d',
                    'ff0000', 'de0101', 'c21301', 'a71001', '911003']
            
            m.add_legend(labels=legend_keys, colors=legend_colors, title="Degrees ºC", position='bottomleft')

            with output:
                output.clear_output()
                print('Showing legend...')

        else:
            m.legend_widget.close()


    legend.observe(legend_change, "value")


    button_width = "113px"
    load_rasters = widgets.Button(
        description="Apply",
        button_style="primary",
        tooltip="Load the LST products",
        style=style,
        layout=widgets.Layout(padding="0px", width=button_width),
    )

    

    def submit_clicked(b):

        #####################################################################
        #functions to compute LST and Emissivity
        #####################################################################


        sdate = str(start_date.value)
        edate = str(end_date.value)
        col = collections[collection.value]

        with output:
            print("Loading data... Please wait...")

        # nd_bands = None
        # if (first_band.value is not None) and (second_band.value is not None):
        #     nd_bands = [first_band.value, second_band.value]

        temp_output = widgets.Output()

        if m is not None:
            
            geom = country_sites[site.value] 

            # Apply cloud filter to landsat
            if collection.value == 'Landsat':
                dataset = col.filterBounds(geom).filterDate(ee.Date(sdate), 
                    ee.Date(edate)).filterMetadata('CLOUD_COVER', 'less_than', int(clouds.value))
            else:
                #print('Please, check your collection choice')
                dataset = col.filterBounds(geom).filterDate(ee.Date(sdate), ee.Date(edate)) 


            clipped = dataset.map(lambda image: image.clip(geom))

            #banda = clipped.map(d[windex.value])
            banda = clipped.select(windex.value)
            #vegetationrs = clipped.select(banda)

            nor_vis = {
                'min': -10,
                'max': 40,
                'palette': [
                    '040274', '040281', '0502a3', '0502b8', '0502ce', '0502e6',
                    '0602ff', '235cb1', '307ef3', '269db1', '30c8e2', '32d3ef',
                    '3be285', '3ff38f', '86e26f', '3ae237', 'b5e22e', 'd6e21f',
                    'fff705', 'ffd611', 'ffb613', 'ff8b13', 'ff6e08', 'ff500d',
                    'ff0000', 'de0101', 'c21301', 'a71001', '911003'
                ],
            }

            name = windex.value + ' ' + collection.value + ' ' + compendium.value

        
            if compendium.value == 'Max':
                banda = banda.max()
            elif compendium.value == 'Min':
                banda = banda.min()
            elif compendium.value == 'Mean':
                banda = banda.mean()
            elif compendium.value == 'Median':
                banda = banda.median()
            elif compendium.value == 'Percentile 10':
                banda = banda.reduce(ee.Reducer.percentile([10]))
            elif compendium.value == 'Percentile 20':
                banda = banda.reduce(ee.Reducer.percentile([20]))
            elif compendium.value == 'Percentile 90':
                banda = banda.reduce(ee.Reducer.percentile([90]))
            elif compendium.value == 'Percentile 95':
                banda = banda.reduce(ee.Reducer.percentile([95]))
            else:
                banda = banda.median()
            
            # We made a dict with the images loaded in the map, key is the name and image and geometry are the values for each entry
            downloads_images[name] = [banda, geom]
            rdlist.options = [i for i in list(downloads_images.keys())]
            #print('desde submit', downloads_images)
            m.addLayer(banda, nor_vis, name)
       
            with output:

                output.clear_output()
                print("The raster has been added to the map.")
    
    load_rasters.on_click(submit_clicked)

    reset_btn = widgets.Button(
        description="Reset",
        button_style="primary",
        style=style,
        layout=widgets.Layout(padding="0px", width=button_width),
    )

    def reset_btn_click(change):
        output.clear_output()

    reset_btn.on_click(reset_btn_click)

    dwlnd_btn = widgets.Button(
        description="Download",
        button_style="primary",
        style=style,
        layout=widgets.Layout(padding="0px", width=button_width),
    )

    def dwlnd_btn_click(change):
        
        sc = scale.value
        crs_ = "EPSG:"+ crs.value
        rs = rdlist.value
        outname = output_name.value
        download_ee_image(downloads_images[rs][0], outname, scale=sc, region=downloads_images[rs][1].geometry(), crs=crs_)
        print('Downloading raster to the current folder... Por dios ya...')
        

    dwlnd_btn.on_click(dwlnd_btn_click)
 
    output = widgets.Output(layout=widgets.Layout(width=widget_width, padding=padding))

    tab1 = widgets.VBox(children=[crs, scale, output_name])
    rdlist.options = [i for i in list(downloads_images.keys())]
    tab2 = widgets.VBox(children=[rdlist])
    tab = widgets.Tab(children=[tab2, tab1])
    tab.set_title(1, 'Download Options')
    tab.set_title(0, 'Rasters list')


    toolbar_widget = widgets.VBox(layout=widgets.Layout(border="solid orange"))
    toolbar_widget.children = [toolbar_button]
    toolbar_header = widgets.HBox()
    toolbar_header.children = [close_button, toolbar_button]
    toolbar_footer = widgets.VBox()
    toolbar_footer.children = [
        network,
        site,
        collection,
        widgets.HBox([start_date, end_date]),
        widgets.HBox([clouds, clouds_label]),
        windex,
        #time_series, # Someday we will have this
        compendium, #statistic method
        ndvi2gif,
        legend,
        #scale,
        #widgets.VBox([scale, crs]),
        #get_keys(),
        tab,
        widgets.HBox([load_rasters, dwlnd_btn, reset_btn]),
        output,
    ]

    toolbar_event = ipyevents.Event(
        source=toolbar_widget, watched_events=["mouseenter", "mouseleave"]
    )

    def handle_toolbar_event(event):

        if event["type"] == "mouseenter":
            toolbar_widget.children = [toolbar_header, toolbar_footer]
        elif event["type"] == "mouseleave":
            if not toolbar_button.value:
                toolbar_widget.children = [toolbar_button]
                toolbar_button.value = False
                close_button.value = False

    toolbar_event.on_dom_event(handle_toolbar_event)

    def toolbar_btn_click(change):
        if change["new"]:
            close_button.value = False
            toolbar_widget.children = [toolbar_header, toolbar_footer]
        else:
            if not close_button.value:
                toolbar_widget.children = [toolbar_button]

    toolbar_button.observe(toolbar_btn_click, "value")

    def close_btn_click(change):
        if change["new"]:
            toolbar_button.value = False
            if m is not None:
                if m.tool_control is not None and m.tool_control in m.controls:
                    m.remove_control(m.tool_control)
                    m.tool_control = None
                m.toolbar_reset()
            toolbar_widget.close()

    close_button.observe(close_btn_click, "value")

    toolbar_button.value = True
    if m is not None:
        toolbar_control = ipyleaflet.WidgetControl(
            widget=toolbar_widget, position="topright"
        )

        if toolbar_control not in m.controls:
            m.add_control(toolbar_control)
            m.tool_control = toolbar_control
    else:
        return toolbar_widget
    


##############################################################################################################
##############################################################################################################
##############################################################################################################

def Form(m=None):

    """Form to send us data and feedback

    Args:
        m (geemap.Map, optional staellite collection and phenometrics DOY or value): A geemap Map instance. Defaults to None.

    Returns:
        ipywidgets: The interactive GUI.
    """

    if m is not None:
        m.add_basemap("Esri.WorldImagery")

    

    #############################################
    # eLTER sites stuffs
    #############################################

    #Adding eLETR shapes through deimsPY
    
    eelter_object = ee.FeatureCollection('projects/ee-digdgeografo/assets/elter_lyon')

    deimsDict = {'Donana': "bcbc866c-3f4f-47a8-bbbc-0a93df6de7b2",
                 'Braila_Island': "d4854af8-9d9f-42a2-af96-f1ed9cb25712",
                 'Baixo': "45722713-80e3-4387-a47b-82c97a6ef62b",
                 'River_Exe': "b8e9402a-10bc-4892-b03d-1e85fc925c99",
                 'Cairngorms': "1b94503d-285c-4028-a3db-bc78e31dea07",
                 'Veluwe': "bef0bbd2-d8a9-4672-9e5b-085d049f4879",
                 'Gran_Paradiso': "15c3e841-8494-42d2-a44e-c49a0ff25946",
                 'Schorfheide': "94c53dd1-acad-4ad8-a73b-62669ec7af2a",
                 'Neusiedler': "1230b149-9ba5-4ab8-86c9-cf93120f8ae2"}
    
    networks = {"Austria": "d45c2690-dbef-4dbc-a742-26ea846edf28",
            "Belgica": "735946e0-4e9e-484a-acee-85e31f4e2a2e",
            "Bulgaria": "20ad4fa2-cc07-4848-b9ed-8952c55f1a3f",
            "Denmark": "e3911e8a-ce9b-46ce-8265-c2dc9676ad03",
            "Finland": "aaae2a46-f355-41d0-8067-c2f0cd52e814",
            "France": "d8d9206f-b1bd-4f90-84b7-8c662d4235a2",
            "Germany": "e904354a-f3a0-40ce-a9b5-61741f66c824",
            "Greece": "83453a6c-792d-4549-9dbb-c17ced2e0cc3",
            "Hungary": "0615a89f-2883-47ab-8cd0-2508f413cab7",
            "Israel": "e0f680c2-22b1-4424-bf54-58aa9b7476a0",
            "Italy": "7fef6b73-e5cb-4cd2-b438-ed32eb1504b3",
            "Netherlands": "8312c2c4-a787-4986-9a3d-3f1364bab3ba",
            "Norway": "bc7c517b-3648-40cc-a04c-8c98d009c4a9",
            "Poland": "67763729-45a7-4248-a70d-622b1d0a3d41",
            "Portugal": "d8eb4823-b707-4590-94d8-d90c1d07d6f8",
            "Romania": "4260f964-0ac4-4406-8adc-5afc06e31779",
            "Slovakia": "3d6a8d72-9f86-4082-ad56-a361b4cdc8a0",
            "Slovenia": "fda2984f-9aea-4abf-9f6c-c3eca0f82eb8",
            "Spain": "2b70f1fb-f7d9-4615-a1a3-33fc6fa44600",
            "Sweden": "a50d9e39-d4b6-4d30-bba2-43580ac8c0b2",
            "Switzerland": "cedf695c-c6dc-4660-b944-3c22f12ad0d9"}

    country_sites = {}    

    for k, v in deimsDict.items():
        eLTER_SITES[k] = [deims.getSiteById(v)['title'], gdf_to_ee(deims.getSiteBoundaries(v))]

    # Shape Styling

    style = {
            "stroke": True,
            "color": "red",
            "weight": 3,
            "opacity": 0.5,
            "fill": False,
            "fillColor": "blue",
            "fillOpacity": 0,
            "clickable": False
        }

    
    for k, v in deimsDict.items():
        m.add_elter_sites(v, style, k)
    m.centerObject(eelter_object)


    #############################################
    # Widgets stuffs
    #############################################


    output_widget = widgets.Output(layout={'border': '1px solid black'})
    output_control = ipyleaflet.WidgetControl(widget=output_widget, position='bottomright')
    m.add_control(output_control)

    output_widget.clear_output()
    logo = widgets.HTML(
        value='<img src="https://pbs.twimg.com/profile_images/1310893180234141697/XbUuptdr_400x400.jpg" width="50px" height="50px">')
    with output_widget:
        display(logo)

    #m.add_shapefile(lter_shp, style=style, layer_name='eLTER sites')
    #m.centerObject(eelter_object, 5)

    widget_width = "350px"
    padding = "0px 0px 0px 4px"  # upper, right, bottom, left
    style = {"description_width": "initial"}

    toolbar_button = widgets.ToggleButton(
        value=False,
        tooltip="Toolbar",
        icon="list",
        button_style="danger",
        layout=widgets.Layout(width="28px", height="28px", padding="0px 0px 0px 4px"),
    )

    close_button = widgets.ToggleButton(
        value=False,
        tooltip="Close the tool",
        icon="times",
        button_style="primary",
        layout=widgets.Layout(height="28px", width="28px", padding="0px 0px 0px 4px"),
    )
    
    #Here we start the changes
    network = widgets.Dropdown(
        options=[i for i in networks.keys()],
        value=None,
        description="eLTER Network:",
        layout=widgets.Layout(width=widget_width, padding=padding),
        style=style,
    )

    site = widgets.Dropdown(
        options=[],
        value=None,
        description="eLTER Site:",
        layout=widgets.Layout(width=widget_width, padding=padding),
        style=style,
    )

    #displaying the text widget
    collector_name = widgets.Text(
        description="Collector Name", 
        layout=widgets.Layout(width='350px', padding=padding),
        flex_flow='column',
        align_items='stretch', 
        style= {'description_width': 'initial'}
        )
   
    collector_mail = widgets.Text(
        description="Collector Email", 
        layout=widgets.Layout(width='350px', padding=padding),
        flex_flow='column',
        align_items='stretch', 
        style= {'description_width': 'initial'}
        )

    float_Xtext = widgets.FloatText(
            value=37.8756,
            step=0.001,
            description='Insert Latitude Coord (decimal degrees):',
            layout=widgets.Layout(width='350px', padding=padding),
            flex_flow='column',
            align_items='stretch', 
            style= {'description_width': 'initial'}
            )
    
    float_Ytext = widgets.FloatText(
        value=-6.8756,
        step=0.001,
        description='Insert Longitude Coord (decimal degrees):',
        layout=widgets.Layout(width='350px', padding=padding),
        flex_flow='column',
        align_items='stretch', 
        style= {'description_width': 'initial'}
    )

    filename = widgets.Text(
        description="Upload file", 
        value="Upload file", 
        width='150px',
        flex_flow='column',
        align_items='stretch', 
        padding=padding
    )
    
    upload = widgets.FileUpload(
        accept='.csv', 
        multiple=False, 
        width='75px',
        flex_flow='column',
        align_items='stretch', 
        padding=padding
    )

    start_year = widgets.IntSlider(
        description="Year:",
        value=2017,
        min=2001,
        max=2022,
        readout=False,
        layout=widgets.Layout(width="320px"),
        style= {'description_width': 'initial'})

    start_year_label = widgets.Label()
    widgets.jslink((start_year, "value"), (start_year_label, "value"))
    #aa = widgets.HBox([start_year, start_year_label])

    ndvi2gif = widgets.Checkbox(
        value=True,
        description="Show Ndvi2Gif NDWI composite",
        tooltip="Show last seasons NDWI median composite",
        style=style,
    )

    #Here we start the tab form
    metrics = widgets.Dropdown(
        options=["SOS", "MOS", "EOS"],
        value=None,
        description="Phenometric:",
        layout=widgets.Layout(width=widget_width, padding=padding),
        style=style,
    )

    doy = widgets.IntSlider(
        description="DOY:",
        value=162,
        min=1,
        max=365,
        readout=True,
        layout=widgets.Layout(width="320px"),
        style= {'description_width': 'initial'})
    
    #Here we start the tab form
    floods = widgets.Checkbox(
        value=False,
        description="Water presence",
        tooltip="Show last seasons NDWI median composite",
        style=style,
    )

    depth = widgets.FloatRangeSlider(
        value=[5, 7.5],
        min=0,
        max=10.0,
        step=0.1,
        description='Depth levels:',
        disabled=False,
        continuous_update=False,
        orientation='horizontal',
        readout=True,
        readout_format='.1f',
    )

    depth_label = widgets.Label()
    widgets.jslink((depth, "value"), (depth_label, "value"))

    temps = widgets.BoundedFloatText(
        value=25.5,
        min=-50,
        max=50,
        step=0.1,
        description='Temperature ºC:',
        disabled=False,
        style= {'description_width': 'initial'}
    )



    
    def network_change(change):

        #country_sites = {}
        if change['new']:

            # recorro una red nacional
            country_list = deims.getListOfSites(networks[change['new']])

            for i in country_list:        
                #print(i)        
                name = deims.getSiteById(i)['title'].split(' - ')[0]
                #print(name)        
                geom = deims.getSiteBoundaries(i)['geometry']#geemap.gdf_to_ee(deims.getSiteBoundaries(i))
                if len(geom) != 0:
                    country_sites[name] = gdf_to_ee(deims.getSiteBoundaries(i))
                else:
                    continue 
            
            site.options = [i for i in list(country_sites.keys())]
            
                
    network.observe(network_change, "value")

    def site_change(change):

        #print(country_sites)
        if change['new']:
            
            geom = country_sites[change['new']]
            #title = eLTER_SITES[change['new']][0]
            m.centerObject(geom)
            if ndvi2gif.value==True:

                MyClass = NdviSeasonality(roi=geom, sat='S2', key='perc_90', periods=4,start_year=2018, end_year=2022, index='ndvi')
                median = MyClass.get_year_composite().mean()
                vizParams = {'bands': ['spring', 'autumn', 'winter'], 'min': 0.15, 'max': 0.8}
                m.addLayer(median, vizParams, 'perc_90')

            # with output:
            #     output.clear_output()
            #     print('eLTER Title:', title)
                
    site.observe(site_change, "value")

    
    button_width = "113px"
    load_rasters = widgets.Button(
        description="Apply",
        button_style="primary",
        tooltip="Send your data and feedback",
        style=style,
        layout=widgets.Layout(padding="0px", width=button_width),
    )

    

    def submit_clicked(b):

        #####################################################################
        #functions to upload form data to DataLab
        #####################################################################


        with output:
            print("Sending data... Please wait...")

        temp_output = widgets.Output()

        if m is not None:
            
            try:

                file = os.path.join(os.getcwd(), 'validation_data.txt')

                t1 = '\nCollector {} with email {} have upload some data for {} eLTER Site:'.format(collector_name.value,
                                            collector_mail.value, site.value)
                t2 = ' Year: {} Metrics: {} DOY: {} Flood: {} Depth: {} LST: {}'.format(start_year.value, metrics.value, doy.value, 
                            floods.value, depth.value, temps.value)
                t3 = " Coords: " + str(float_Xtext.value) + " " + str(float_Xtext.value) + ' Attached file: ' + str('upload.value') +'\n'

                
                with open(file, 'a+') as val:
                    #for k, v in textmail3.items():
                        #print(k,v)
                    val.write(t1)
                    val.write(t2)
                    val.write(t3)
                    
                csv = list(upload.value.values())[0]
                if len(csv) != 0:
                    now = datetime.datetime.now().strftime('%Y-%m-%d')
                    content = csv['content']
                    content = io.StringIO(content.decode('utf-8'))
                    df = pd.read_csv(content)
                    dfname = filename.value + "_" + now + ".csv"
                    #print(dfname)
                    df.to_csv(os.path.join(os.getcwd(), dfname))

                else:
                    print('No csv file to upload, but thanks for your data and time')
                    return
               
            except Exception as e:
                #print(e)
                print('No csv file to upload, but thanks for your data and time')
                return
       
            with output:
                output.clear_output()
                print("The data has been uploaded to the Datlab, thank you.")
    
    load_rasters.on_click(submit_clicked)

    reset_btn = widgets.Button(
        description="Reset",
        button_style="primary",
        style=style,
        layout=widgets.Layout(padding="0px", width=button_width),
    )

    def reset_btn_click(change):
        output.clear_output()

    reset_btn.on_click(reset_btn_click)

    # dwlnd_btn = widgets.Button(
    #     description="Download",
    #     button_style="primary",
    #     style=style,
    #     layout=widgets.Layout(padding="0px", width=button_width),
    # )

    # def dwlnd_btn_click(change):
        
    #     sc = scale.value
    #     crs_ = "EPSG:"+ crs.value
    #     rs = rdlist.value
    #     outname = output_name.value
    #     download_ee_image(downloads_images[rs][0], outname, scale=sc, region=downloads_images[rs][1].geometry(), crs=crs_)
    #     print('Downloading raster to the current folder... Por dios ya...')
        

    # dwlnd_btn.on_click(dwlnd_btn_click)
 
    output = widgets.Output(layout=widgets.Layout(width=widget_width, padding=padding))

    tab1 = widgets.VBox(children=[metrics, doy])
    tab2 = widgets.VBox(children=[floods, depth])
    tab3 = widgets.VBox(children=[temps])
    tab = widgets.Tab(children=[tab1, tab2, tab3])
    tab.set_title(0, 'PhenoMetrics')
    tab.set_title(1, 'Flood')
    tab.set_title(2, 'LST')


    toolbar_widget = widgets.VBox(layout=widgets.Layout(border="solid orange"))
    toolbar_widget.children = [toolbar_button]
    toolbar_header = widgets.HBox()
    toolbar_header.children = [close_button, toolbar_button]
    toolbar_footer = widgets.VBox()
    toolbar_footer.children = [
        network,
        site,
        collector_name,
        collector_mail,
        widgets.VBox([float_Xtext, float_Ytext]),
        widgets.VBox([filename, upload]),
        widgets.HBox([start_year, start_year_label]),
        ndvi2gif,
        #scale,
        #widgets.VBox([scale, crs]),
        #get_keys(),
        tab,
        widgets.HBox([load_rasters, reset_btn]),
        output,
    ]

    toolbar_event = ipyevents.Event(
        source=toolbar_widget, watched_events=["mouseenter", "mouseleave"]
    )

    def handle_toolbar_event(event):

        if event["type"] == "mouseenter":
            toolbar_widget.children = [toolbar_header, toolbar_footer]
        elif event["type"] == "mouseleave":
            if not toolbar_button.value:
                toolbar_widget.children = [toolbar_button]
                toolbar_button.value = False
                close_button.value = False

    toolbar_event.on_dom_event(handle_toolbar_event)

    def toolbar_btn_click(change):
        if change["new"]:
            close_button.value = False
            toolbar_widget.children = [toolbar_header, toolbar_footer]
        else:
            if not close_button.value:
                toolbar_widget.children = [toolbar_button]

    toolbar_button.observe(toolbar_btn_click, "value")

    def close_btn_click(change):
        if change["new"]:
            toolbar_button.value = False
            if m is not None:
                if m.tool_control is not None and m.tool_control in m.controls:
                    m.remove_control(m.tool_control)
                    m.tool_control = None
                m.toolbar_reset()
            toolbar_widget.close()

    close_button.observe(close_btn_click, "value")

    toolbar_button.value = True
    if m is not None:
        toolbar_control = ipyleaflet.WidgetControl(
            widget=toolbar_widget, position="topright"
        )

        if toolbar_control not in m.controls:
            m.add_control(toolbar_control)
            m.tool_control = toolbar_control
    else:
        return toolbar_widget

