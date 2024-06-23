import dearpygui.dearpygui as dpg
import os
import cv2
import numpy as np
import numpy
import PIL.Image
import sys
import traceback
import time


if __name__ == "__main__":
    sys.path.append("")

# load from version.txt
try:
    with open("version.txt", "r") as f:
        VERSION = f.read()
except:
    VERSION = "0.0.0"


from src.graph import  AttributeDefinition
from src.graph.graph import Graph, Connection, BaseNode, GraphException
import threading

import src.nodes.input as input_nodes
import src.nodes.output as output_nodes
import src.nodes.convert as convert_nodes
import src.nodes.tagger as tagger_nodes
import src.nodes.dictionary as dictionary_nodes
import src.nodes.logic as logic_nodes
import src.nodes.llm as llm_nodes

import src.update as update

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

        def change_theme(theme: str):
            dpg.bind_item_theme(self.id, self.node_themes[theme])

        def on_error(error: Exception):
            change_theme("error")
            self.show_message("Error", exception_full_message(error))


        self.node._on_error += on_error
        self.node._on_init += lambda: self.hide_message()
        self.node._on_init += lambda: change_theme("init")
        self.node._on_init_finished += lambda: change_theme("default")
        self.node._on_node_ready += lambda: change_theme("default")
        self.node._on_run += lambda: change_theme("running")
        self.node._on_run_finished += lambda: change_theme("completed")
        self.node._on_error += lambda error: change_theme("error")

        self.node._on_refresh += self.refresh_ui

        # message ui
        self.message_ui_id = None
        self.message_ui_title_id = None
        self.message_ui_text_id = None

        # inputs
        self.inputs_ids: dict[int, GuiNodeInput] = {}
        self.outputs_ids: dict[int, GuiNodeOutput] = {}
        self.static_inputs_ids: dict[int, GuiNodeStaticInput] = {}

    def __create_node_theme(r, g, b):
        with dpg.theme() as node_theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvNodeCol_NodeOutline, (r,g,b), category=dpg.mvThemeCat_Nodes)
        return node_theme
    
    node_themes = {
        "default" : None,
        "completed" : __create_node_theme(255, 255, 255),
        "running" : __create_node_theme(0, 255, 0),
        "init" : __create_node_theme(0, 0, 255),
        "error" : __create_node_theme(255, 0, 0),
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
            self.show_message("Error", exception_full_message(e))

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
            self.show_message("Error", exception_full_message(e))

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
            self.show_message("Error", exception_full_message(e))

    
    def show_message(self, title, message):
        if self.message_ui_id is None or not dpg.does_item_exist(self.message_ui_id):
            return
        if self.message_ui_title_id is None or not dpg.does_item_exist(self.message_ui_title_id):
            return
        if self.message_ui_text_id is None or not dpg.does_item_exist(self.message_ui_text_id):
            return
        
        dpg.show_item(self.message_ui_id)
        dpg.set_value(self.message_ui_title_id, f"--- {title} ---")
        dpg.set_value(self.message_ui_text_id, message)


    def hide_message(self):
        if self.message_ui_id is None or not dpg.does_item_exist(self.message_ui_id):
            return
        
        dpg.hide_item(self.message_ui_id)

    def refresh_ui(self):

        self.hide_message()

        print(f"Refreshing {self.name}")

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
        with dpg.node(label=self.name, parent=parent, pos=pos, tag=uuid) as node:

            with dpg.node_attribute(label=self.name, attribute_type=dpg.mvNode_Attr_Static, show=False) as message_ui:
                self.message_ui_id = message_ui
                self.message_ui_title_id = dpg.add_text("Title")
                self.message_ui_text_id = dpg.add_text("Message")

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
                   

        self.id = node

        return self.id
    

    def __str__(self):
        return f"{self.name} - {self.node}"


class GuiGraph:
    def __init__(self):
        self.graph = Graph()
        self.gui_nodes: dict[int, GuiNode] = {}
        self.gui_connections: dict[int, GuiConnection] = {}

        self.graph.register_nodes(input_nodes.register_nodes())
        self.graph.register_nodes(output_nodes.register_nodes())
        self.graph.register_nodes(convert_nodes.register_nodes())
        self.graph.register_nodes(tagger_nodes.register_nodes())
        self.graph.register_nodes(dictionary_nodes.register_nodes())
        self.graph.register_nodes(logic_nodes.register_nodes())
        self.graph.register_nodes(llm_nodes.register_nodes())

        self.graph.on_connection_removed += self.on_connection_removed
        self.graph.on_connection_added += self.on_connection_added
        self.graph.on_node_removed += self.on_node_removed
        self.graph.on_node_added += self.on_node_added

        self.graph.on_graph_started += self.on_graph_started
        self.graph.on_graph_stopped += self.on_graph_stopped

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
            dpg.set_value("info_text", f"{node.node.help}")

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
                        with dpg.child_window( tag="toolbar", no_scrollbar=True):
                            dpg.add_text("Right click to open menu")
                            dpg.add_separator()
                            dpg.add_button(label="Run", width=-1, callback=self.run_callback, tag="graph_run_button")
                            dpg.add_separator()
                            dpg.add_text("", tag="info_text")

            # menu bar 
            with dpg.menu_bar():
                with dpg.menu(label="File"):
                    dpg.add_menu_item(label="New", callback=self.new_graph_callback)
                    dpg.add_menu_item(label="Save", callback=lambda: dpg.show_item("save_graph_file_dialog"))
                    dpg.add_menu_item(label="Load", callback=lambda: dpg.show_item("load_graph_file_dialog"))
                    dpg.add_menu_item(label="Exit", callback=lambda: dpg.stop_dearpygui())

                with dpg.menu(label="Help"):
                    dpg.add_menu_item(label="About", callback=lambda: dpg.show_item("About"))
                    dpg.add_menu_item(label="Check for updates", callback=lambda: dpg.show_about())

            # save and load file dialogs
            with dpg.file_dialog(tag="save_graph_file_dialog", callback=self.save_graph_callback, width=700, height=400, show=False):
                dpg.add_file_extension("Yaml files (*.yml *.yaml){.yml,.yaml}")

            with dpg.file_dialog(tag="load_graph_file_dialog", callback=self.load_graph_callback, width=700, height=400, show=False):
                dpg.add_file_extension("Yaml files (*.yml *.yaml){.yml,.yaml}")

            # node menu
            with dpg.window(label="Node menu", modal=True, tag="node_menu", no_title_bar=False, user_data=[], show=False):
                def delete_selected(sender, app_data, user_data):
                    user_data = dpg.get_item_user_data("node_menu")
                    self.delete_nodes_callback(sender, app_data, user_data)

                dpg.add_button(label="Delete Node", callback=delete_selected)
                dpg.add_button(label="Clone Node (todo)", callback=lambda: print("Duplicate Node"), enabled=False)

            # connection menu
            with dpg.window(label="Connection Menu", modal=True, tag="connection_menu", no_title_bar=False, user_data=[], show=False):
                def delete_selected(sender, app_data, user_data):
                    user_data = dpg.get_item_user_data("connection_menu")
                    self.delete_connections_callback(sender, app_data, user_data)
                dpg.add_button(label="Delete link", callback=delete_selected)

            # selection menu
            with dpg.window(label="Selection Menu", modal=True, tag="selection_menu", no_title_bar=False, user_data={}, show=False):
                def delete_selected(sender, app_data, user_data):
                    user_data = dpg.get_item_user_data("selection_menu")
                    self.delete_nodes_callback(sender, app_data, user_data.get("nodes", []))
                    self.delete_connections_callback(sender, app_data, user_data.get("links", []))
                dpg.add_button(label="Delete All", callback=delete_selected)
                dpg.add_button(label="Clone All (todo)", callback=lambda: print("Duplicate All"), enabled=False)

            # graph menu
            with dpg.window(label="Create Node", modal=True, tag="graph_menu", no_title_bar=False, width=200, show=False):
                
                # search bar
                buttons = {}

                def update_search_callback(sender, app_data):
                    search = dpg.get_value(sender)
                    for node_name, button in buttons.items():
                        if search.lower() in node_name.lower():
                            dpg.configure_item(button, show=True)
                        else:
                            dpg.configure_item(button, show=False)

                dpg.add_input_text(label="Search", width=-1, callback=update_search_callback)

                
                categories = {}
                for node_name, node in self.available_nodes.items():
                    category = node.category()
                    if category not in categories:
                        categories[category] = []
                    categories[category].append(node_name)
                
                for category, nodes in categories.items():
                    with dpg.collapsing_header(label=category, default_open=True):
                        for node_name in nodes:
                            button = dpg.add_button(label=node_name, callback=self.add_node_callback, user_data=node_name, width=-1)
                            buttons[node_name] = button

            with dpg.window(label="Error", modal=True, tag="error_popup", no_title_bar=False, width=200, height=85, min_size=[85,85], show=False, no_close=True):
                dpg.add_text("Error Message", tag="error_popup_text")
                dpg.add_separator()
                dpg.add_button(label ="Close", callback=lambda: dpg.configure_item("error_popup", show=False))

            center = [dpg.get_viewport_width()/2 - 200, dpg.get_viewport_height()/2 - 200]
            with dpg.window(label="About", tag="About", no_title_bar=False, min_size=[85,85], show=False, pos=center):
                dpg.add_text(f"Welcome to the Tagliatello Graph Editor!")
                dpg.add_text(f"Version: {VERSION}")
                dpg.add_text("Author: deskup@protonmail.com")
                dpg.add_separator()
                dpg.add_text("Tagliatello is a graph editor for creating and running data processing pipelines.")
                dpg.add_text("It is built on top of the DearPyGui library.")
                dpg.add_text("Please note that this is an early version and it is still under development.")
                dpg.add_text("If you didn't encounter any bugs, it means you haven't used it enough.")
                dpg.add_separator()
                dpg.add_text("This is early alpha version. Expect that graphs won't be compatible with future versions.", color=(255, 0, 0))
                dpg.add_separator()
                dpg.add_text("Known issues and limitations:")
                dpg.add_text("1. No undo/redo functionality")
                dpg.add_text("2. Copy/paste not implemented")
                dpg.add_text("3. Error messages are not always helpful and may clutter the screen")
                dpg.add_text("4. No support for custom nodes yet")
                dpg.add_text("5. A lot of missing nodes")
                dpg.add_text("6. Collector and Iterator nodes don't work if are connected directly")
                dpg.add_text("7. Nodes not being added at the mouse position")
                dpg.add_text("8. More bugs which I didn't bother to write down")

        with dpg.window(label="Check for updates", tag="update_popup",  min_size=[85,85], show=False, pos=center):
            dpg.add_text("Checking for updates...", tag="update_popup_text")
            dpg.add_separator()
            dpg.add_text("To update to the latest version, run 'update.ps1' script.")

        node_editor.check_for_updates_silent()

        return graph_window

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
        dpg.set_item_pos("graph_menu", dpg.get_mouse_pos(local=False))
        dpg.show_item("graph_menu")
        dpg.hide_item("node_menu")
        dpg.hide_item("connection_menu")
        dpg.hide_item("selection_menu")


    def add_node_callback(self, sender, app_data, user_data):
        try:
            node = self.available_nodes.get(user_data)()
            node.metadata["position"] = dpg.get_mouse_pos(local=True)
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

dpg.create_viewport(title='Tagiatello', width=800, height=600, large_icon=large_icon, small_icon=small_icon)
dpg.setup_dearpygui()

dpg.show_viewport()

node_editor = GuiGraph()
graph_window = node_editor.show()


dpg.set_primary_window(graph_window, True)

dpg.start_dearpygui()


if DEBUG:
    while dpg.is_dearpygui_running():
        jobs = dpg.get_callback_queue() # retrieves and clears queue
        dpg.run_callbacks(jobs)
        dpg.render_dearpygui_frame()


dpg.destroy_context()