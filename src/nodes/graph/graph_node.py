from ...graph import BaseNode, DPG_DEFAULT_INPUT_WIDTH, BoolenAttributeDefinition
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
        self.set_static_input("hide_middle_nodes", True)

        self.__graph: Graph = None
        self.__file_selector = None
        self.__file_button = None

        self.__graph_inputs = {}
        self.__graph_outputs = {}


    def load_graph(self, path: str):
        try:
            self.default_inputs = {}

            if self.__graph is not None:
                self.__graph.on_error -= self._on_error.trigger

            self.__graph = None
            self.__input_definitions = {}
            self.__output_definitions = {}
            self.__graph_inputs = {}
            self.__graph_outputs = {}

            self.__graph = Graph()
            self.__graph.on_error += self._on_error.trigger
            self.__graph.register_modules("src/nodes")
            self.__graph.register_modules("custom_nodes")
            self.__graph.load_from_file(path)
            
        except Exception as e:
            self._on_error.trigger(e)
            self.refresh_ui()

            if self.__file_button is not None and dpg.does_item_exist(self.__file_button):
                dpg.configure_item(self.__file_button, label="Select Graph")
            return
        
        if self.__file_button is not None and dpg.does_item_exist(self.__file_button):
            dpg.configure_item(self.__file_button, label=f"{os.path.basename(path)}")

        try:
            hide_middle_nodes = self.static_inputs.get("hide_middle_nodes", True)

            for node_name, node in self.__graph.nodes.items():
                input_connections = self.__graph.get_input_connections_for_node(node_name)
                output_connections = self.__graph.get_output_connections_for_node(node_name)

                if hide_middle_nodes and len(input_connections) > 0 and len(output_connections) > 0:
                    continue

                def has_connection(input_name, connections: list[Connection]):
                    return any([connection.input_name == input_name for connection in connections])

                for input_name, input_def in node.input_definitions.items():
                    if has_connection(input_name, input_connections):
                        continue
                    self.__input_definitions[f"{node_name}.{input_name}"] = input_def.copy()
                    self.__graph_inputs[f"{node_name}.{input_name}"] = (node_name, input_name)

                    self.set_default_input(f"{node_name}.{input_name}", node.default_inputs.get(input_name, None))

                for output_name, output_def in node.output_definitions.items():
                    if has_connection(output_name, output_connections):
                        continue
                    self.__output_definitions[f"{node_name}.{output_name}"] = output_def.copy()
                    self.__graph_outputs[f"{node_name}.{output_name}"] = (node_name, output_name)

            self.refresh_ui()
        except Exception as e:
            self._on_error.trigger(e)


    def load_from_dict(self, data: dict):
        super().load_from_dict(data)
        try:
            self.load_graph(self.default_inputs.get("path", ""))
        except Exception as e:
            self._on_error.trigger(e)

    @property
    def input_definitions(self):
        return self.__input_definitions
    
    @property
    def output_definitions(self):
        return self.__output_definitions
    
    @property
    def static_input_definitions(self):
        return {
            "hide_middle_nodes": BoolenAttributeDefinition()
        }
    
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
        self.__file_button = dpg.add_button(label="Select Graph", callback=lambda: dpg.show_item(self.__file_selector), parent=parent, width=DPG_DEFAULT_INPUT_WIDTH)
        return super().show_custom_ui(parent)

    def init(self):
        self.set_progress(-1, -1)
        return super().init()

    def run(self, **kwargs) -> dict[str, object]:

        if self.__graph is None:
            raise ValueError("No graph loaded")
        
        count = len(self.__graph.nodes)
        self.set_progress(0, count)

        for inputs in self.__graph_inputs.values():
            node_name, input_name = inputs
            node = self.__graph.get_node_by_name(node_name)
            node.set_default_input(input_name, kwargs.get(f"{node_name}.{input_name}", None))

        self.__graph.run()

        while self.__graph.is_running():
            self.set_progress(len(self.__graph._run_results), count)

        run_results = self.__graph._run_results
        result = {}
        for graph_output, output in self.__graph_outputs.items():
            if output[0] not in run_results:
                continue
            elif output[1] not in run_results[output[0]]:
                continue
            result[graph_output] = run_results[output[0]][output[1]]

        self.set_progress(len(self.__graph._run_results), count, show_eta=False)

        return result

        