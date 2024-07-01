import dearpygui.dearpygui as dpg
import os
import sys
import traceback
import time
import textwrap
import random

if __name__ == "__main__":
    sys.path.append("")

# load from version.txt
try:
    with open("version.txt", "r") as f:
        VERSION = f.read()
except:
    VERSION = "0.0.0"


from src.graph import  AttributeDefinition, DPG_DEFAULT_INPUT_WIDTH
from src.graph.graph import Graph, Connection, BaseNode, GraphException
import threading

import src.update as update

from src.settings import SETTINGS

DEBUG = False

dpg.create_context()
dpg.configure_app(manual_callback_management=DEBUG)


def exception_full_message(e):
    if not isinstance(e, Exception):
        return str(e)
    elif isinstance(e, GraphException) or isinstance(e, ValueError):
        return f"{e}"
    try:
        raise e
    except Exception as e:
        return traceback.format_exc()


class GuiConnection:
    def __init__(self, connection: Connection):
        self.connection = connection
        self.id = None

    def create_connection(self, output, input, parent):
        self.id = dpg.add_node_link(output, input, parent=parent, label=str(self.connection))
        return self.id
    
    def __str__(self):
        return f"{self.connection}"

class GuiNodeInput:
    def __init__(self, node, name, attribute_definition: AttributeDefinition):
        self.node: "GuiNode"  = node
        self.name = name
        self.attribute_definition = attribute_definition
        self.id = None

    def add_attribute(self, parent) -> int:
        return self.attribute_definition.show_ui(self.node.node, self.name, dpg.mvNode_Attr_Input, parent)
    
class GuiNodeOutput:
    def __init__(self, node, name, attribute_definition: AttributeDefinition):
        self.node: "GuiNode"  = node
        self.name = name
        self.attribute_definition = attribute_definition
        self.id = None

    def add_attribute(self, parent) -> int:
        return self.attribute_definition.show_ui(self.node.node, self.name, dpg.mvNode_Attr_Output, parent)
    
class GuiNodeStaticInput:
    def __init__(self, node, name, attribute_definition: AttributeDefinition):
        self.node: "GuiNode" = node
        self.name = name
        self.attribute_definition = attribute_definition
        self.id = None

    def add_attribute(self, parent) -> int:
        return self.attribute_definition.show_ui(self.node.node, self.name, dpg.mvNode_Attr_Static, parent)

class GuiNode:
    def __init__(self, graph, node):

        if graph is None:
            raise ValueError("Graph cannot be None")

        if node is None:
            raise ValueError("Node cannot be None")

        # node
        self.node: BaseNode = node
        self.graph: Graph = graph
        self.id = None

        def on_error(error: Exception):
            self.change_theme("error")
            self.show_error_message(str(error), exception_full_message(error))

        def on_warning(warning: str):
            self.change_theme("warning")
            title = warning.split("\n")[0]
            self.show_warning_message(title, warning)

        self.node._on_error += on_error
        self.node._on_init += lambda: self.clear_ui()
        self.node._on_init += lambda:  self.change_theme("init")
        self.node._on_init_finished += lambda:  self.change_theme("default")
        self.node._on_node_ready += lambda:  self.change_theme("default")
        self.node._on_run += lambda:  self.change_theme("running")
        self.node._on_run_finished += lambda:  self.change_theme("completed")
        self.node._on_error += lambda error: self.change_theme("error")
        # self.node._on_warning += on_warning

        self.node._on_refresh += self.refresh_ui

        # message ui
        self.error_button = None
        self.warning_button = None

        # inputs
        self.inputs_ids: dict[int, GuiNodeInput] = {}
        self.outputs_ids: dict[int, GuiNodeOutput] = {}
        self.static_inputs_ids: dict[int, GuiNodeStaticInput] = {}

    def change_theme(self, theme: str):
        if dpg.does_item_exist(self.id):
            dpg.bind_item_theme(self.id, self.node_themes[theme])

    def __create_node_theme(r, g, b):
        with dpg.theme() as node_theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvNodeCol_NodeOutline, (r,g,b), category=dpg.mvThemeCat_Nodes)
        return node_theme
    
    def __create_button_theme(r, g, b):
        with dpg.theme() as button_theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 5, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_Text, (r,g,b), category=dpg.mvThemeCat_Core)

        return button_theme
    
    node_themes = {
        "default" : None,
        "completed" : __create_node_theme(255, 255, 255),
        "running" : __create_node_theme(0, 255, 0),
        "init" : __create_node_theme(0, 0, 255),
        "error" : __create_node_theme(255, 0, 0),
        "warning" : __create_node_theme(255, 255, 0),
    }

    button_themes = {
        "default" : None,
        "warning" : __create_button_theme(255, 255, 0),
        "error" : __create_button_theme(255, 0, 0),
    }


    @property
    def name(self) -> str:
        return self.node.name()
    
    def get_input_id(self, name):
        for id, input in self.inputs_ids.items():
            if input.name == name:
                return id
        return None
    
    def get_output_id(self, name):
        for id, output in self.outputs_ids.items():
            if output.name == name:
                return id
        return None
    
    def get_static_input_id(self, name):
        for id, static_input in self.static_inputs_ids.items():
            if static_input.name == name:
                return id
        return None
    

    def _add_static_input(self, name, definition: AttributeDefinition, parent):
        try:
            children = dpg.get_item_children(parent, 1)
            for child in children:
                dpg.delete_item(child)

            static_input = GuiNodeStaticInput(self, name, definition)
            static_input.add_attribute(parent)
            self.inputs_ids[parent] = static_input  
        except Exception as e:
            self.show_error_message(f"Failed to add static input - {name}", exception_full_message(e))

    def _add_input(self, name, definition: AttributeDefinition, parent):
        try:

            children = dpg.get_item_children(parent, 1)
            for child in children:
                dpg.delete_item(child)

            input = GuiNodeInput(self, name, definition)
            input.add_attribute(parent)
            self.inputs_ids[parent] = input

            dpg.bind_item_theme(parent, definition.theme)

        except Exception as e:
            self.show_error_message(f"Failed to add input - {name}", exception_full_message(e))

    def _add_output(self, name, definition: AttributeDefinition, parent):
        try:
            children = dpg.get_item_children(parent, 1)
            for child in children:
                dpg.delete_item(child)

            output = GuiNodeOutput(self, name, definition)
            output.add_attribute(parent)
            self.outputs_ids[parent] = output
            dpg.bind_item_theme(parent, definition.theme)
        except Exception as e:
            self.show_error_message(f"Failed to add output - {name}", exception_full_message(e))

    
    def show_error_message(self, title, message):
        if self.error_button == None or not dpg.does_item_exist(self.error_button):
            return
        wrapped_title = "\n".join(textwrap.wrap(title, 40, break_long_words=True))
        dpg.set_item_label(self.error_button, f"{wrapped_title}\nClick to show details")
        dpg.set_item_user_data(self.error_button, {"title": title, "message": message})
        dpg.show_item(self.error_button)

    def show_warning_message(self, title, message):
        if self.warning_button == None or dpg.does_item_exist(self.warning_button):
            return
        wrapped_title = "\n".join(textwrap.wrap(title, 40, break_long_words=True))
        dpg.set_item_label(self.warning_button, f"{wrapped_title}\nClick to show details")
        dpg.set_item_user_data(self.warning_button, {"title": title, "message": message})
        dpg.show_item(self.warning_button)

    def clear_ui(self):
        self.change_theme("default")
        dpg.hide_item(self.warning_button)
        dpg.hide_item(self.error_button)

    def refresh_ui(self):
        # remove old inputs
        for id, input in list(self.inputs_ids.items()):
            if input.name not in self.node.input_definitions:
                dpg.delete_item(id)
                del self.inputs_ids[id]

        # remove old outputs
        for id, output in list(self.outputs_ids.items()):
            if output.name not in self.node.output_definitions:
                dpg.delete_item(id)
                del self.outputs_ids[id]

        # remove old static inputs
        for id, static_input in list(self.static_inputs_ids.items()):
            if static_input.name not in self.node.static_input_definitions:
                dpg.delete_item(id)
                del self.static_inputs_ids[id]

        counter = 0

        def get_th_child(id):
            children = dpg.get_item_children(self.id, 1)
            if len(children) > id and id >= 0:
                return children[id]
            return 0

        for name, input in self.node.static_input_definitions.items():
            counter += 1
            static_input = self.get_static_input_id(name)
            if static_input is None:
                static_input = dpg.add_node_attribute(attribute_type=dpg.mvNode_Attr_Static, before=get_th_child(counter))
            self._add_static_input(name, input, static_input)

        for name, input in self.node.input_definitions.items():
            counter += 1
            input_id = self.get_input_id(name)
            if input_id is None:
                input_id = dpg.add_node_attribute(attribute_type=dpg.mvNode_Attr_Input, before=get_th_child(counter), shape=input.shape)
            self._add_input(name, input, input_id)

        for name, output in self.node.output_definitions.items():
            counter += 1
            output_id = self.get_output_id(name)
            if output_id is None:
                output_id = dpg.add_node_attribute(attribute_type=dpg.mvNode_Attr_Output, before=get_th_child(counter), shape=output.shape)
            self._add_output(name, output, output_id)


    def create_node(self, parent, pos=[0, 0], uuid=None):
        if uuid is None:
            uuid = dpg.generate_uuid()

        with dpg.window(label="Warning", show=False) as message_popup:
            message_popup_text = dpg.add_text("No message")

        def show_popup(sender, app_data, user_data):
            title = user_data.get("title", self.node.name())
            message = user_data.get("message", "No message")
            pos = dpg.get_mouse_pos(local=False)
            dpg.set_item_pos(message_popup, pos)
            dpg.show_item(message_popup)
            dpg.set_value(message_popup_text, message)
            dpg.set_item_label(message_popup, title)

        with dpg.node(label=self.name, parent=parent, pos=pos, tag=uuid) as node:
            self.id = node  
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static):
                self.error_button = dpg.add_button(label="Error message\nClick to show details", callback=show_popup, user_data={"title": "Error", "message": ""}, show=False)
                self.warning_button = dpg.add_button(label="Warning message\nClick to show details", callback=show_popup, user_data={"title": "Warning", "message": ""}, show=False)

                dpg.bind_item_theme(self.error_button, self.button_themes["error"])
                dpg.bind_item_theme(self.warning_button, self.button_themes["warning"])

            for static_input_name, static_input_type in self.node.static_input_definitions.items():
                static_input = dpg.add_node_attribute(attribute_type=dpg.mvNode_Attr_Static)
                self._add_static_input(static_input_name, static_input_type, static_input)

            for input_name, input_definition in self.node.input_definitions.items():
                input = dpg.add_node_attribute(attribute_type=dpg.mvNode_Attr_Input, shape=input_definition.shape)
                self._add_input(input_name, input_definition, input)

            for output_name, output_definition in self.node.output_definitions.items():
                output = dpg.add_node_attribute(attribute_type=dpg.mvNode_Attr_Output, shape=output_definition.shape)
                self._add_output(output_name, output_definition, output)
                
            # custom ui attribute
            with dpg.node_attribute(label="Custom UI", attribute_type=dpg.mvNode_Attr_Static) as custom_ui:
                self.node.show_custom_ui(custom_ui)
                   
        return self.id
    

    def __str__(self):
        return f"{self.name} - {self.node}"


class GuiGraph:
    def __init__(self):
        self.graph = Graph()
        self.gui_nodes: dict[int, GuiNode] = {}
        self.gui_connections: dict[int, GuiConnection] = {}

        self.graph.register_modules("src/nodes")
        self.graph.register_modules("custom_nodes")

        self.graph.on_connection_removed += self.on_connection_removed
        self.graph.on_connection_added += self.on_connection_added
        self.graph.on_node_removed += self.on_node_removed
        self.graph.on_node_added += self.on_node_added

        self.graph.on_graph_started += self.on_graph_started
        self.graph.on_graph_stopped += self.on_graph_stopped

        self.graph.on_error += lambda error: self.display_main_popup("Error", exception_full_message(error))

    def on_graph_started(self):
        dpg.configure_item("graph_run_button", label="Stop")
        pass

    def on_graph_stopped(self):
        dpg.configure_item("graph_run_button", label="Run")
        pass

    def display_main_popup(self, title, text):
        try:
            if dpg.does_item_exist("error_popup") == False:
                return
            
            dpg.hide_item("connection_menu")
            dpg.hide_item("node_menu")
            dpg.hide_item("selection_menu")
            dpg.hide_item("graph_menu")

            dpg.set_item_label("error_popup", title)
            dpg.set_value("error_popup_text", text)
            
            window_width = dpg.get_viewport_width()
            window_height = dpg.get_viewport_height()
            popup_width = dpg.get_item_width("error_popup")
            popup_height = dpg.get_item_height("error_popup")
            center = [window_width/2 - popup_width/2, window_height/2 - popup_height]
            dpg.set_item_pos("error_popup", center)
          
            # todo: do it normally
            def display_popup_thread():
                start_time = time.time()
                while not dpg.is_item_visible("error_popup"):
                    if time.time() - start_time > 10:
                        break
                    dpg.show_item("error_popup")
                    if dpg.is_item_visible("error_popup"):
                        break
                    time.sleep(1)

            # Create and start a new thread for displaying the popup
            popup_thread = threading.Thread(target=display_popup_thread)
            popup_thread.start()

        except Exception as e:
            print(f"Error displaying popup: {exception_full_message(e)}")

    def save_graph_callback(self, sender, app_data, user_data = None):
        file_path_name = app_data.get("file_path_name")
        if not file_path_name:
            return
        
        filter = app_data.get("current_filter")
        if filter is not None and ".yaml" in filter and not file_path_name.endswith(".yaml"):
            file_path_name += ".yaml"
        
        try:
            # iterate over gui nodes and its keys
            for node_id, gui_node in self.gui_nodes.items():
                node_position = dpg.get_item_pos(node_id)
                gui_node.node.metadata["position"] = node_position
            self.graph.save_to_file(file_path_name)
        except Exception as e:
            self.display_main_popup("Error saving graph", str(e))

    def clear_graph(self):
        for node_id in self.gui_nodes:
            if dpg.does_item_exist(node_id):
                dpg.delete_item(node_id)
            
        self.gui_nodes = {}

        for connection_id in self.gui_connections:
            if dpg.does_item_exist(connection_id):
                dpg.delete_item(connection_id)
        self.gui_connections = {}
        self.graph.clear()

    def get_node_id(self, node_name):
        node = self.graph.nodes.get(node_name)
        if node is not None:
            for id, gui_node in self.gui_nodes.items():
                if gui_node.node == node:
                    return id
        return None
    
    def get_connection_id(self, connection):
        for id, gui_connection in self.gui_connections.items():
            if gui_connection.connection == connection:
                return id
        return None

    def new_graph_callback(self, sender, app_data, user_data = None):
        self.clear_graph()

    def load_graph_callback(self, sender, app_data, user_data = None):

        self.clear_graph()

        file_path_name = app_data.get("file_path_name")
        
        if not os.path.exists(file_path_name):
            self.display_main_popup("Error loading graph", f"File {file_path_name} does not exist.")
            return
        
        try:
            self.graph.load_from_file(file_path_name)
        except Exception as e:
            self.display_main_popup("Error loading graph", exception_full_message(e))

    def run_callback(self, sender, app_data, user_data = None):
        try:
            if self.graph.is_running():
                self.graph.stop()
            else:
                self.graph.run()

        except Exception as e:
            self.display_main_popup("Error running graph", exception_full_message(e))

    __last_hovered = None
    def node_hover_callback(self, sender, app_data, user_data = None):
        hovered = app_data
        if self.__last_hovered == hovered:
            return
        self.__last_hovered = hovered

        node = self.gui_nodes.get(hovered)
        if node is not None:
            dpg.set_value("info_text", dpg.get_item_alias(app_data))

        pass

    def connection_hover_callback(self, sender, app_data, user_data = None):
        hovered = app_data
        if self.__last_hovered == hovered:
            return
        self.__last_hovered = hovered

        connection = self.gui_connections.get(hovered)
        if connection is not None:
            dpg.set_value("info_text", f"{connection}")

    def check_for_updates_silent(self):
        check_for_updates = SETTINGS.get("check_for_updates", True)
        if not check_for_updates:
            return

        try:
            version = update.get_version_to_update(VERSION)
            print(f"New version available: {version}")
            if version is not None:
                self.check_for_updates_callback(None, None)
        except Exception as e:
            print(f"Error checking for updates: {exception_full_message(e)}")
            pass

    def check_for_updates_callback(self, sender, app_data):
        try:
            dpg.show_item("update_popup")
            dpg.set_value("update_popup_text", "Checking for updates...")
            version = update.get_version_to_update(VERSION)
            if version is not None:
                dpg.set_value("update_popup_text", f"New version available: {version}")
            else:
                dpg.set_value("update_popup_text", "No updates available.")
        except Exception as e:
            self.display_main_popup("Error checking for updates", exception_full_message(e))

    def dpg_main_menu(self):
        with dpg.menu_bar():
            with dpg.menu(label="File"):
                dpg.add_menu_item(label="New", callback=self.new_graph_callback)
                dpg.add_menu_item(label="Save", callback=lambda: dpg.show_item("save_graph_file_dialog"))
                dpg.add_menu_item(label="Load", callback=lambda: dpg.show_item("load_graph_file_dialog"))
                dpg.add_menu_item(label="Exit", callback=lambda: dpg.stop_dearpygui())

            with dpg.menu(label="Settings"):
                dpg.add_menu_item(label="Settings", callback=lambda: dpg.show_item("settings_popup"))

            with dpg.menu(label="Help"):
                dpg.add_menu_item(label="About", callback=lambda: dpg.show_item("about_popup"))
                dpg.add_menu_item(label="Changelog", callback=lambda: dpg.show_item("changelog_popup"))
                dpg.add_menu_item(label="Check for updates", callback=self.check_for_updates_callback)

    def dpg_load_save_file_dialogs(self):
        with dpg.file_dialog(label="Save Graph", tag="save_graph_file_dialog", width=700, height=400, show=False, callback=self.save_graph_callback):
            dpg.add_file_extension("Yaml files (*.yml *.yaml){.yml,.yaml}")

        with dpg.file_dialog(label="Load Graph", tag="load_graph_file_dialog", width=700, height=400, show=False, callback=self.load_graph_callback):
            dpg.add_file_extension("Yaml files (*.yml *.yaml){.yml,.yaml}")

    def dpg_node_menu(self):
        with dpg.window(label="Node menu", modal=True, tag="node_menu", no_title_bar=False, user_data=[], show=False):
            def delete_selected(sender, app_data, user_data):
                user_data = dpg.get_item_user_data("node_menu")
                self.delete_nodes_callback(sender, app_data, user_data)

            def duplicate_selected(sender, app_data, user_data):
                user_data = dpg.get_item_user_data("node_menu")
                self.duplicate_nodes_callback(sender, app_data, user_data)

            dpg.add_button(label="Delete Node", callback=delete_selected)
            dpg.add_button(label="Duplicate Node", callback=duplicate_selected)


    def dpg_connection_menu(self):
        with dpg.window(label="Connection Menu", modal=True, tag="connection_menu", no_title_bar=False, user_data=[], show=False):
            def delete_selected(sender, app_data, user_data):
                user_data = dpg.get_item_user_data("connection_menu")
                self.delete_connections_callback(sender, app_data, user_data)
            dpg.add_button(label="Delete link", callback=delete_selected)     

    def dpg_selection_menu(self):
        with dpg.window(label="Selection Menu", modal=True, tag="selection_menu", no_title_bar=False, user_data={}, show=False):
            def delete_selected(sender, app_data, user_data):
                user_data = dpg.get_item_user_data("selection_menu")
                self.delete_nodes_callback(sender, app_data, user_data.get("nodes", []))
                self.delete_connections_callback(sender, app_data, user_data.get("links", []))
            def duplicate_selected(sender, app_data, user_data):
                user_data = dpg.get_item_user_data("selection_menu")
                self.duplicate_selected_callback(sender, app_data, {
                    "nodes": user_data.get("nodes", []),
                    "links": user_data.get("links", [])
                })
                
            dpg.add_button(label="Delete Selected", callback=delete_selected)
            dpg.add_button(label="Duplicate Selected", callback=duplicate_selected)

    def dpg_graph_menu(self):
        with dpg.window(label="Create Node", modal=True, tag="graph_menu", no_title_bar=False, width=200, show=False):
            
            # search bar
            buttons = {}
            categories = {}
            categories_items = {}


            def update_search_callback(sender, app_data):
                search = dpg.get_value(sender)
                # hide all categories
                for category, category_header in categories.items():
                    dpg.hide_item(category_header)

                for node_name, button in buttons.items():
                    if search.lower() in node_name.lower():
                        dpg.configure_item(button, show=True)
                        node = self.available_nodes.get(node_name)
                        category = node.category()
                        dpg.show_item(categories[category])
                    else:
                        dpg.configure_item(button, show=False)

            dpg.add_input_text(label="Search", width=-1, callback=update_search_callback)

        
            for node_name, node in self.available_nodes.items():
                category = node.category()
                if category not in categories_items:
                    categories_items[category] = []
                categories_items[category].append(node_name)
            
            for category, nodes in categories_items.items():
                with dpg.collapsing_header(label=category, default_open=True) as category_header:
                    categories[category] = category_header
                    for node_name in nodes:
                        button = dpg.add_button(label=node_name, callback=self.add_node_callback, user_data=node_name, width=-1)
                        buttons[node_name] = button

    def dpg_error_popup(self):
        with dpg.window(label="Error", modal=True, tag="error_popup", no_title_bar=False, min_size=[85,85], show=False, no_close=True):
            dpg.add_text("Error Message", tag="error_popup_text")
            dpg.add_separator()
            dpg.add_button(label ="Close", callback=lambda: dpg.configure_item("error_popup", show=False))

    def dpg_about_popup(self):
        with dpg.window(label="About", tag="about_popup", no_title_bar=False, min_size=[600,100], show=False):
            dpg.add_text(f"        _______                  _   _           _            _   _            ")
            dpg.add_text(f"       |__   __|                | | (_)         | |          | | | |           ")
            dpg.add_text(f"          | |     __ _    __ _  | |  _    __ _  | |_    ___  | | | |   ___     ")
            dpg.add_text(f"          | |    / _' |  / _' | | | | |  / _' | | __|  / _ \ | | | |  / _ \    ")
            dpg.add_text(f"          | |   | (_| | | (_| | | | | | | (_| | | |_  |  __/ | | | | | (_) |   ")
            dpg.add_text(f"          |_|    \__,_|  \__, | |_| |_|  \__,_|  \__|  \___| |_| |_|  \___/    ")
            dpg.add_text(f"                          __/ |                                                ") 
            dpg.add_text(f"                         |___/                    Version: {VERSION}")               
            dpg.add_text(f"                                                   Author: deskup@protonmail.com")
            dpg.add_text(f"                                                   Github: deskup1/tagliatello")
            dpg.add_separator()
            dpg.add_text("Tagliatello is a graph editor for creating and running data processing pipelines.")
            dpg.add_text("It is built on top of the DearPyGui library.")
            dpg.add_text("Please note that this is an early version and it is still under development.")
            dpg.add_text("If you didn't encounter any bugs, it means you haven't used it enough.")
            dpg.add_separator()
            dpg.add_text("This is early alpha version. Expect that graphs won't be compatible with future versions.", color=(255, 0, 0))
            dpg.add_separator()

        center = [dpg.get_viewport_width()/2 - 300, dpg.get_viewport_height()/2 - 300]
        dpg.set_item_pos("about_popup", center)

    def dpg_update_popup(self):

        with dpg.window(label="Check for updates", tag="update_popup",  min_size=[400,85], show=False):
            dpg.add_text("Checking for updates...", tag="update_popup_text")
            dpg.add_separator()
            dpg.add_text("To update to the latest version, run 'update.ps1' script.")

        center = [dpg.get_viewport_width()/2 - 200, dpg.get_viewport_height()/2 - 100]
        dpg.set_item_pos("update_popup", center)

        node_editor.check_for_updates_silent()

    def dpg_changelog_popup(self):
        show_changelog = SETTINGS.get("version", "0.0.0") != VERSION
        SETTINGS.set("version", VERSION)
        SETTINGS.save()

        with dpg.window(label="Changelog", tag="changelog_popup", max_size=[600,3000],  min_size=[600,85], show=show_changelog) as changelog_popup:
            update.dpg_changelog(changelog_popup, 600)

        center = [dpg.get_viewport_width()/2  - 300, dpg.get_viewport_height()/2 - 300]
        dpg.set_item_pos("changelog_popup", center)

    def dpg_settings_popup(self):
        with dpg.window(label="Settings", tag="settings_popup", no_title_bar=False, show=False, min_size=[400,100]):
            dpg.add_text("Settings")
            dpg.add_separator()
            dpg.add_text("General")
            dpg.add_checkbox(label="Check for updates on startup", default_value=SETTINGS.get("check_for_updates", True), callback=lambda _, app_data: SETTINGS.set("check_for_updates", app_data))
            dpg.add_separator()
            dpg.add_text("Hugging Face")
            dpg.add_input_text(label="Cache Directory", default_value=SETTINGS.get("hf_cache_dir", ""), callback=lambda _, app_data: SETTINGS.set("hf_cache_dir", app_data))
            
            dpg.add_separator()
            dpg.add_button(label="Save", callback=lambda: SETTINGS.save())
        
        center = [dpg.get_viewport_width()/2 - 200, dpg.get_viewport_height()/2 - 100]
        dpg.set_item_pos("settings_popup", center)
    def show(self):
        
        with dpg.handler_registry():
            dpg.add_mouse_click_handler(button=dpg.mvMouseButton_Right, callback=self.right_click_callback)

        with dpg.item_handler_registry(tag = "node_handler_registry"):
            dpg.add_item_hover_handler(callback=self.node_hover_callback)

        with dpg.item_handler_registry(tag = "connection_handler_registry"):
            dpg.add_item_hover_handler(callback=self.connection_hover_callback)

        with dpg.window(label="Tutorial", width=400, height=400, tag="graph_window") as graph_window:
     
            # graph window
            with dpg.child_window(no_scrollbar=True, no_scroll_with_mouse=True, border=False):
                with dpg.table(header_row=False, resizable=True, indent=0):
                    dpg.add_table_column()
                    dpg.add_table_column(width_fixed=True, init_width_or_weight=200)

                    
                    with dpg.table_row():

                        # node editor
                        with dpg.node_editor(callback=self.link_callback, delink_callback=self.delink_callback, tag="node_editor", minimap=True, minimap_location=dpg.mvNodeMiniMap_Location_BottomRight):    
                            pass
                        
                        # toolbar
                        with dpg.child_window(tag="toolbar", no_scrollbar=True):
                            dpg.add_text("Right click to open menu")
                            dpg.add_separator()
                            dpg.add_button(label="Run", width=-1, callback=self.run_callback, tag="graph_run_button")
                            dpg.add_button(label="Clear messages", width=-1, callback=self.clear_ui_callback)
                            dpg.add_separator()
                            dpg.add_text("", tag="info_text")


            self.dpg_main_menu()
            self.dpg_load_save_file_dialogs()
            self.dpg_node_menu()
            self.dpg_connection_menu()
            self.dpg_selection_menu()
            self.dpg_graph_menu()
            self.dpg_error_popup()
            self.dpg_about_popup()
            self.dpg_update_popup()
            self.dpg_changelog_popup()
            self.dpg_settings_popup()

        return graph_window
    
    def clear_ui_callback(self, sender, app_data, user_data):
        # iterate over nodes
        for node_id, gui_node in self.gui_nodes.items():
            gui_node.clear_ui()

    def link_callback(self, sender, app_data, user_data):
        
        output_attribute = app_data[0]
        input_attribute = app_data[1]

        output_attribute_parent = dpg.get_item_parent(output_attribute)
        input_attribute_parent = dpg.get_item_parent(input_attribute)

        output_node_name = dpg.get_item_alias(output_attribute_parent)
        input_node_name = dpg.get_item_alias(input_attribute_parent)
        
        output_node_gui: GuiNode  = self.gui_nodes.get(output_node_name)
        input_node_gui: GuiNode = self.gui_nodes.get(input_node_name)

        output_attribute_name: GuiNodeInput = output_node_gui.outputs_ids.get(output_attribute).name
        input_attribute_name: GuiNodeOutput = input_node_gui.inputs_ids.get(input_attribute).name
        
        try:
            if self.graph.can_add_connection(output_node_gui.node, output_attribute_name, input_node_gui.node, input_attribute_name)[0]:
                self.graph.add_connection(output_node_gui.node, output_attribute_name, input_node_gui.node, input_attribute_name)
        except Exception as e:
            self.display_main_popup("Error creating connection", exception_full_message(e))
            return

    def on_node_added(self, node: BaseNode):
        gui_node = GuiNode(self.graph, node)
        node_name = self.graph.get_node_name(node)
        position = node.metadata.get("position", [0, 0])
        gui_node.create_node("node_editor", position, node_name)
        dpg.bind_item_handler_registry(node_name, "node_handler_registry")
        self.gui_nodes[node_name] = gui_node

    def on_node_removed(self, node: BaseNode):
        node_name = self.graph.get_node_name(node)
        if dpg.does_item_exist(node_name):
            dpg.delete_item(node_name)
        del self.gui_nodes[node_name]

    def on_connection_removed(self, connection: Connection):

        connection_id = self.get_connection_id(connection)
        if dpg.does_item_exist(connection_id):
            dpg.delete_item(connection_id)

        if connection_id in self.gui_connections:
            del self.gui_connections[connection_id]

    def on_connection_added(self, connection: Connection):
        gui_connection = GuiConnection(connection)
        output_attribute = self.gui_nodes.get(connection.output_node_name).get_output_id(connection.output_name)
        input_attribute = self.gui_nodes.get(connection.input_node_name).get_input_id(connection.input_name)
        connection_id = gui_connection.create_connection(output_attribute, input_attribute, "node_editor")
        dpg.bind_item_handler_registry(connection_id, "connection_handler_registry")
        self.gui_connections[connection_id] = gui_connection
        pass

    def delink_callback(self, sender, app_data, user_data):
        link_id = app_data
        if link_id in self.gui_connections:
            connection = self.gui_connections[link_id]
            self.graph.remove_connection(connection.connection)

    @property
    def available_nodes(self):
        return self.graph.available_nodes
    
    def delete_nodes_callback(self, sender, app_data, user_data = []):
        nodes_to_delete = user_data
        for node_id in nodes_to_delete:
            if isinstance(node_id, int):
                node_name = dpg.get_item_alias(node_id)
            else:
                node_name = node_id

            gui_node = self.gui_nodes.get(node_name)
            if gui_node is None:
                continue

            self.graph.remove_node(gui_node.node)

        dpg.hide_item("node_menu")
        dpg.hide_item("selection_menu")

    def delete_connections_callback(self, sender, app_data, user_data = []):
        try:
            connections_to_delete = user_data
            for connection in connections_to_delete:
                gui_connection = self.gui_connections.get(connection)
                if gui_connection is None:
                    continue

                self.graph.remove_connection(gui_connection.connection)
                
        except Exception as e:
            self.display_main_popup("Error deleting connections", exception_full_message(e))
            raise e

        dpg.hide_item("connection_menu")
        dpg.hide_item("selection_menu")

    def show_node_menu_callback(self, sender, app_data, user_data):

        dpg.set_item_label("node_menu", dpg.get_item_label(user_data))
        dpg.set_item_pos("node_menu", dpg.get_mouse_pos(local=False))

        dpg.set_item_user_data("node_menu", [user_data])

        dpg.show_item("node_menu")
        dpg.hide_item("connection_menu")
        dpg.hide_item("selection_menu")

    def show_connection_menu_callback(self, sender, app_data, user_data):
        
        dpg.set_item_label("connection_menu", dpg.get_item_label(user_data))
        dpg.set_item_pos("connection_menu", dpg.get_mouse_pos(local=False))

        dpg.set_item_user_data("connection_menu", [user_data])

        dpg.show_item("connection_menu")
        dpg.hide_item("node_menu")
        dpg.hide_item("selection_menu")

    def duplicate_nodes_callback(self, sender, app_data, user_data):
        nodes_to_duplicate = user_data
        self.__duplicate_nodes(nodes_to_duplicate)
        dpg.hide_item("node_menu")
        dpg.hide_item("selection_menu")

    def __duplicate_nodes(self, nodes_to_duplicate):
        new_nodes = []
        try:
            for node_id in nodes_to_duplicate:
                node_name = dpg.get_item_alias(node_id)
                node = self.gui_nodes.get(node_name).node
                node_data = node.save_to_dict()
                new_node = node.__class__()
                new_node.load_from_dict(node_data)
                old_position = dpg.get_item_pos(node_id)
                new_node.metadata["position"] = [old_position[0] + 50, old_position[1] + 50]
                new_nodes.append(self.graph.add_node(new_node))
        except Exception as e:
            self.display_main_popup("Error duplicating nodes", exception_full_message(e))
        return new_nodes

    def duplicate_selected_callback(self, sender, app_data, user_data):
        selected_nodes = dpg.get_selected_nodes("node_editor")
        selected_nodes_names = [dpg.get_item_alias(node) for node in selected_nodes]
        new_nodes_names = self.__duplicate_nodes(selected_nodes)

        def get_node_index(node_name):
            for index, node in enumerate(selected_nodes_names):
                if node == node_name:
                    return index
            return None

        selected_links = dpg.get_selected_links("node_editor")
        try:
            for link_id in selected_links:
                gui_connection = self.gui_connections.get(link_id)
                if gui_connection is None:
                    continue

                new_input_node = new_nodes_names[get_node_index(gui_connection.connection.input_node_name)]
                new_output_node = new_nodes_names[get_node_index(gui_connection.connection.output_node_name)]
                self.graph.add_connection(new_output_node, gui_connection.connection.output_name, new_input_node, gui_connection.connection.input_name)
        except Exception as e:
            self.display_main_popup("Error duplicating connections", exception_full_message(e))

        dpg.clear_selected_links("node_editor")
        dpg.clear_selected_nodes("node_editor")

        for node_name in new_nodes_names:
            config = dpg.get_item_configuration(node_name)
            dpg.is_item_clicked
            print(config)
       
        dpg.hide_item("selection_menu")


    def show_selection_menu_callback(self, sender, app_data, user_data):
        selected_links = user_data.get("links")
        selected_nodes = user_data.get("nodes")

        if len(selected_links) == 0 and len(selected_nodes) == 1:
            self.show_node_menu_callback(sender, app_data, selected_nodes[0])
            return
        
        if len(selected_links) == 1 and len(selected_nodes) == 0:
            self.show_connection_menu_callback(sender, app_data, selected_links[0])
            return

        # create label showing number of selected links and nodes
        label = ""
        width = 0
        if len(selected_links) > 0:
            label += f"Selected links: {len(selected_links)}"
            width += 150
        if len(selected_nodes) > 0:
            if label != "":
                label += " | "
            label += f"Selected nodes: {len(selected_nodes)}"
            width += 150

        dpg.set_item_label("selection_menu", label)
        dpg.set_item_width("selection_menu", width)
        dpg.set_item_pos("selection_menu", dpg.get_mouse_pos(local=False))

        dpg.set_item_user_data("selection_menu", {"links": selected_links, "nodes": selected_nodes})

        dpg.show_item("selection_menu")
        dpg.hide_item("node_menu")
        dpg.hide_item("connection_menu")
        dpg.hide_item("graph_menu")


    def show_graph_menu_callback(self, sender, app_data, user_data = None):
        position = dpg.get_mouse_pos(local=False)
        dpg.set_item_pos("graph_menu", position)
        dpg.set_item_user_data("graph_menu", position)
        dpg.show_item("graph_menu")
        dpg.hide_item("node_menu")
        dpg.hide_item("connection_menu")
        dpg.hide_item("selection_menu")

    def add_node_callback(self, sender, app_data, user_data):
        try:
            node = self.available_nodes.get(user_data)()

            children = dpg.get_item_children("node_editor", 1)
            # you need to have reference point to be able to add new node
            # this is a workaround to add first node
            if len(children) == 0:
                dummy_item = dpg.add_node(parent="node_editor", label="dummy")
                ref_screen_pos = dpg.get_item_rect_min(dummy_item)
                ref_grid_pos = dpg.get_item_pos(dummy_item)
                dpg.delete_item(dummy_item)
            else:
                ref_item = children[0]
                ref_screen_pos = dpg.get_item_rect_min(ref_item)
                ref_grid_pos = dpg.get_item_pos(ref_item)

            # starting_pos = dpg.get_mouse_pos(local=False)
            starting_pos = dpg.get_item_user_data("graph_menu")
            pos = [starting_pos[0] - ref_screen_pos[0] + ref_grid_pos[0], 
                   starting_pos[1] - ref_screen_pos[1] + ref_grid_pos[1]]

            node.metadata["position"] = pos
            self.graph.add_node(node)
            dpg.hide_item("graph_menu")
        except Exception as e:
            self.display_main_popup("Error adding node", exception_full_message(e))

    def right_click_callback(self, sender, app_data):

        if dpg.is_item_shown("graph_menu"):
            dpg.hide_item("graph_menu")
            return
        
        if dpg.is_item_shown("node_menu"):
            dpg.hide_item("node_menu")
            return
        
        if dpg.is_item_shown("connection_menu"):
            dpg.hide_item("connection_menu")
            return
        
        if dpg.is_item_shown("selection_menu"):
            dpg.hide_item("selection_menu")
            return
            
        selected_nodes = dpg.get_selected_nodes("node_editor")
        selected_links = dpg.get_selected_links("node_editor")

        # if something is selected, show selection menu
        if len(selected_nodes) > 0 or len(selected_links) > 0:
            self.show_selection_menu_callback("node_editor", app_data, {"nodes": selected_nodes, "links": selected_links})
            return

        # if connection is hovered, show connection menu
        cleanup_connections = []
        for connection in self.gui_connections:
            if not dpg.does_item_exist(connection):
                cleanup_connections.append(connection)
                continue
            if dpg.is_item_hovered(connection):
                self.show_connection_menu_callback(sender, app_data, connection)
                return
            
        for connection in cleanup_connections:
            del self.gui_connections[connection]

        # if node is hovered, show node menu
        cleanup_nodes = []
        for node in self.gui_nodes:
            if not dpg.does_item_exist(node):
                cleanup_nodes.append(node)
                continue
            if dpg.is_item_hovered(node):
                self.show_node_menu_callback(sender, app_data, node)
                return
            
        for node in cleanup_nodes:
            del self.gui_nodes[node]

        # if graph is hovered, show graph menu
        if dpg.is_item_hovered("node_editor"):
            self.show_graph_menu_callback(sender, app_data)
            return



large_icon = "icon.ico"
small_icon = "icon.ico"

dpg.create_viewport(title='Tagiatello', large_icon=large_icon, small_icon=small_icon)
dpg.setup_dearpygui()

dpg.show_viewport()

node_editor = GuiGraph()
graph_window = node_editor.show()


dpg.set_primary_window(graph_window, True)

if DEBUG:
    # dpg.show_style_editor()
    while dpg.is_dearpygui_running():
        jobs = dpg.get_callback_queue() # retrieves and clears queue
        dpg.run_callbacks(jobs)
        dpg.render_dearpygui_frame()
else:
    dpg.start_dearpygui()


dpg.destroy_context()