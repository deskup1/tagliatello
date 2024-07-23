from ...graph import BaseNode, DPG_DEFAULT_INPUT_WIDTH, BoolenAttributeDefinition, AnyAttributeDefinition, StringAttributeDefinition, BaseNode, AttributeDefinition
from ...graph.graph import Graph, Connection
from ..progress_node import ProgressNode
import dearpygui.dearpygui as dpg
import time
import os

class GraphNode(ProgressNode):
    def __init__(self):
        super().__init__()
        self.__input_definitions = {}
        self.__output_definitions = {}

        self.set_static_input("path", "")

        self.__graph: Graph = None
        self.__file_selector = None
        self.__file_button = None
        self.error_raised = None

    def on_error(self, error: Exception):
        self.error_raised = error

    def load_graph(self, path: str):
        try:
            print("Loading graph", path)
            self.default_inputs = {}

            if self.__graph is not None:
                self.__graph.on_error -= self._on_error.trigger

            self.__graph = None
            self.__input_definitions = {}
            self.__output_definitions = {}

            self.__graph = Graph()
            self.__graph.on_error += self.on_error
            self.__graph.register_modules("src/nodes")
            self.__graph.register_modules("custom_nodes")
            self.__graph.load_from_file(path)
            for node in self.__graph.nodes.values():
                node._on_error += self._on_error.trigger

            
        except Exception as e:

            self.refresh_ui()

            if self.__file_button is not None and dpg.does_item_exist(self.__file_button):
                dpg.configure_item(self.__file_button, label="Select Graph")

            raise e
        
        if self.__file_button is not None and dpg.does_item_exist(self.__file_button):
            dpg.configure_item(self.__file_button, label=f"{os.path.basename(path)}")

 
        for node in self.__graph.nodes.values():
            if isinstance(node, GraphInputNode):
                print(node.save_to_dict())
                self.__input_definitions[node.static_inputs["name"]] = AnyAttributeDefinition()
            elif isinstance(node, GraphOutputNode):
                self.__output_definitions[node.static_inputs["name"]] = AnyAttributeDefinition()

        self.refresh_ui()


    def load_from_dict(self, data: dict):
        super().load_from_dict(data)
        try:
            self.load_graph(self.static_inputs.get("path", ""))
        except Exception as e:
            self._on_error.trigger(e)
        

    @property
    def input_definitions(self):
        return self.__input_definitions
    
    @property
    def output_definitions(self):
        return self.__output_definitions
    
    @classmethod
    def name(cls):
        return "Graph"
    
    @classmethod
    def category(cls):
        return "Graph"
    
    def __select_graph_callback(self, sender, app_data):
        print("Selecting graph", app_data)
        file_path_name = app_data.get("file_path_name")
        
        if not os.path.exists(file_path_name):
            self._on_error.trigger(f"File {file_path_name} does not exist")
            return
        
        self.set_static_input("path", file_path_name)
        self.load_graph(file_path_name)
    
    def show_custom_ui(self, parent):
        with dpg.file_dialog(label="Load Graph", width=700, height=400, show=False, callback=self.__select_graph_callback) as file_selector:
            dpg.add_file_extension("Yaml files (*.yml *.yaml){.yml,.yaml}")
            self.__file_selector = file_selector

        label = "No graph selected"
        if self.static_inputs.get("path", "") != "":
            label = os.path.basename(self.static_inputs.get("path", ""))
        
        self.__file_button = dpg.add_button(label=label, callback=lambda: dpg.show_item(self.__file_selector), parent=parent, width=DPG_DEFAULT_INPUT_WIDTH)
        return super().show_custom_ui(parent)

    def init(self):
        self.error_raised = None
        self.set_progress(-1, -1)
        return super().init()

    def run(self, **kwargs) -> dict[str, object]:

        if self.__graph is None:
            raise ValueError("No graph loaded")
        
        count = len(self.__graph.nodes)
        self.set_progress(0, count)

        for node in self.__graph.nodes.values():
            if isinstance(node, GraphInputNode):
                input_name = node.static_inputs["name"]
                input_value = kwargs.get(input_name, None)
                node.set_in(input_value)

        self.__graph.run()

        last_progress = 0
        while self.__graph.is_running():
            if self.error_raised is not None:
                raise self.error_raised
            last_progress = len(self.__graph._run_results)
            self.set_progress(last_progress, count)

        result = {}
        for node in self.__graph.nodes.values():
            if isinstance(node, GraphOutputNode):
                output_name = node.static_inputs["name"]
                output_value = node.get_out()
                if output_name not in result or isinstance(result[output_name], _Undefined):
                    result[output_name] = output_value
                node.clear_out()
            elif isinstance(node, GraphInputNode):
                node.clear_in()

        self.set_progress(last_progress, count, show_eta=False)
        return result

class _Undefined:
    def __eq__(self, value: object) -> bool:
        return isinstance(value, _Undefined)
        
class GraphInputNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.in_value = _Undefined()

    def set_in(self, value):
        self.in_value = value

    def clear_in(self):
        self.in_value = _Undefined()

    @property
    def output_definitions(self):
        return {
            "in": AnyAttributeDefinition()
        }

    @property
    def input_definitions(self):
        return {
            "in": AnyAttributeDefinition()
        }
    
    @property
    def static_input_definitions(self):
        return {
            "name": StringAttributeDefinition()
        }

    def run(self, **kwargs):
        in_value = self.in_value
        if self.in_value == _Undefined():
            in_value = kwargs.get("in", None)
        return {
            "in": in_value
        }

    @classmethod
    def name(cls):
        return "Graph Input"

    @classmethod
    def category(cls):
        return "Graph"
    
class GraphOutputNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.out_value = _Undefined()
        self.set_static_input("name", "")

    def get_out(self):
        return self.out_value
    
    def clear_out(self):
        self.out_value = _Undefined()

    @property
    def output_definitions(self):
        return {
            "out": AnyAttributeDefinition()
        }

    @property
    def input_definitions(self):
        return {
            "out": AnyAttributeDefinition()
        }
    
    @property
    def static_input_definitions(self):
        return {
            "name": StringAttributeDefinition()
        }

    def run(self, **kwargs):
        self.out_value = kwargs.get("out", None)
        return {
            "out": self.out_value
        }


    @classmethod
    def name(cls):
        return "Graph Output"

    @classmethod
    def category(cls):
        return "Graph"