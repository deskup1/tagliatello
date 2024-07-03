import sys
if __name__ == "__main__":
    sys.path.append("src")

from .node import BaseNode, AttributeKind, BaseNodeEvent
from src.nodes.unknown_node import UnknownNode

import yaml
# import multiprocessing
import threading
import os
import importlib
import queue
import time

class GraphException(Exception):
    def __init__(self, message: str):
        super().__init__(message)

class Connection:
    def __init__(self, output_node_name: str = "", output_name: str = "", input_node_name: str = "", input_name: str = ""):
        self.output_node_name = output_node_name
        self.output_name = output_name
        self.input_node_name = input_node_name
        self.input_name = input_name

    def save_to_dict(self) -> dict:
        return {
            "output_node_name": self.output_node_name,
            "output_name": self.output_name,
            "input_node_name": self.input_node_name,
            "input_name": self.input_name
        }
    
    def load_from_dict(self, data: dict):
        self.output_node_name = data["output_node_name"]
        self.output_name = data["output_name"]
        self.input_node_name = data["input_node_name"]
        self.input_name = data["input_name"]

    def __str__(self) -> str:
        return f"{self.output_node_name}.{self.output_name} -> {self.input_node_name}.{self.input_name}"

class Graph:
    def __init__(self):
        self.nodes: dict[str, BaseNode] = {}
        self.connections: dict[str, Connection] = {}
        self.available_nodes: dict[str, lambda: BaseNode] = {}

        self.on_connection_added = BaseNodeEvent()
        self.on_connection_removed = BaseNodeEvent()

        self.on_node_added = BaseNodeEvent()
        self.on_node_removed = BaseNodeEvent()

        self.on_graph_started = BaseNodeEvent()
        self.on_graph_stopped = BaseNodeEvent()

        self.on_error = BaseNodeEvent()


        self.__max_concurrency = 10

        self._run_results = {}
        self.__nodes_with_unfinished_generator_inputs = set()
        self.__nodes_with_unfinished_generator_outputs = set()

        self.__running = False
        self.__main_process = None


    def is_running(self) -> bool:
        return self.__running

    def register_nodes(self, nodes: list[BaseNode]):
        for node in nodes:
            self.register_node(node)

    def register_modules(self, root_directory: str, module_prefix: str = None):

        if module_prefix is None:
            module_prefix = root_directory.replace("/", ".").replace("\\", ".")

        # iterate over all folders in root_directory
        for directory in os.listdir(root_directory):
            if not os.path.isdir(os.path.join(root_directory, directory)):
                continue

            if not os.path.exists(os.path.join(root_directory, directory, "__init__.py")):
                continue

            if directory.startswith("__"):
                continue

            module_name = f"{module_prefix}.{directory}"
            spec = importlib.util.spec_from_file_location(module_name, os.path.join(root_directory, directory, "__init__.py"))
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if hasattr(module, "register_nodes"):
                self.register_nodes(module.register_nodes())
            
    def register_node(self, node_cls):
        self.available_nodes[node_cls.name()] = node_cls

    def get_unique_node_name(self, node: BaseNode) -> str:
        counter = 0
        name = f"{node.name()} {counter}"
        while name in self.nodes:
            counter += 1
            name = f"{node.name()} {counter}"

        return name
    
    def add_node(self, node: BaseNode) -> str:
        name = self.get_unique_node_name(node)
        self.nodes[name] = node
        self.on_node_added.trigger(node)
        return name
    
    def get_node_by_name(self, name: str) -> BaseNode:
        return self.nodes[name]
    
    def get_node_name(self, node: BaseNode) -> str:
        for name, n in self.nodes.items():
            if n == node:
                return name
        return None
    
    def get_connections_for_node(self, node: BaseNode|str) -> list[Connection]:
        node_name = node if isinstance(node, str) else self.get_node_name(node)
        return [connection for connection in self.connections.values() if connection.output_node_name == node or connection.input_node_name == node_name]

    def get_output_connections_for_node(self, node: BaseNode|str) -> list[Connection]:
        node_name = node if isinstance(node, str) else self.get_node_name(node)
        return [connection for connection in self.connections.values() if connection.output_node_name == node_name]
    
    def get_input_connections_for_node(self, node: BaseNode|str) -> list[Connection]:
        node_name = node if isinstance(node, str) else self.get_node_name(node)
        return [connection for connection in self.connections.values() if connection.input_node_name == node_name]

    def can_add_connection(self, output_node: BaseNode|str, output_name: str, input_node: BaseNode|str, input_name: str) -> tuple[bool, str|None]:
        output_node_name = output_node if isinstance(output_node, str) else self.get_node_name(output_node)
        if output_node_name is None or output_node_name not in self.nodes:
            return (False, f"Output node not found: {output_node_name}")

        input_node_name = input_node if isinstance(input_node, str) else self.get_node_name(input_node)
        if input_node_name is None or input_node_name not in self.nodes:
            return (False, f"Input node not found: {input_node_name}")
        
        # check if nodes has the output and input names
        output_node = self.nodes[output_node_name]
        if output_name not in output_node.output_definitions:
            return (False, f"Output name not found: {output_name} in {output_node_name}")
        
        input_node = self.nodes[input_node_name]
        if input_name not in input_node.input_definitions:
            return (False, f"Input name not found: {input_name} in {input_node_name}")
        
        if input_node == output_node:
            return (False, f"Cannot connect node to itself")
        
        # check if in loop
        if self.check_if_loop(input_node, output_node):
            return (False, f"Loop detected")
        
        # check if valid attribute types
        output_type = output_node.output_definitions[output_name]
        input_type = input_node.input_definitions[input_name]

        can_connect = input_type.can_connect(output_type)
        if not can_connect:
            return (False, f"Incompatible types: {output_type} -> {input_type}")
        
        return (True, None)
    
    def check_if_loop(self, node: BaseNode|str, target_node: BaseNode|str, visited_nodes: list[BaseNode] = []) -> bool:
        node_name = node if isinstance(node, str) else self.get_node_name(node)
        target_node_name = target_node if isinstance(target_node, str) else self.get_node_name(target_node)
        visited_nodes.append(node_name)

        connections = self.get_output_connections_for_node(node_name)
        for connection in connections:
            if connection.input_node_name == target_node_name:
                return True
            if connection.input_node_name not in visited_nodes:
                if self.check_if_loop(connection.input_node_name, target_node_name, visited_nodes):
                    return True
        
        return False


    def add_connection(self, output_node: BaseNode|str, output_name: str, input_node: BaseNode|str, input_name: str):
        
        output_node_name = output_node if isinstance(output_node, str) else self.get_node_name(output_node)
        input_node_name = input_node if isinstance(input_node, str) else self.get_node_name(input_node)

        can_connect, error = self.can_add_connection(output_node_name, output_name, input_node_name, input_name)
        if not can_connect:
            raise GraphException(error)
        
        connection = Connection(output_node_name, output_name, input_node_name, input_name)

        self.remove_input_connection_for_node(input_node_name, input_name)

        try:
            output_node = self.get_node_by_name(output_node_name)
            input_node = self.get_node_by_name(input_node_name)
            output_node._on_output_connected.trigger(output_name, input_node, input_name)
            input_node._on_input_connected.trigger(input_name, output_node, output_name)
            self.on_connection_added.trigger(connection)
        except Exception as e:
            output_node._on_error.trigger(e)
            input_node._on_error.trigger(e)
            raise e

        self.connections[f"{output_node_name}.{output_name} -> {input_node_name}.{input_name}"] = connection
        return connection

    def remove_connection(self, connection: Connection):
        print(f"Removing connection: {connection}")

        connection_to_remove = None
        for key, conn in self.connections.items():
            if conn == connection:
                connection_to_remove = key
                input_node = self.get_node_by_name(conn.input_node_name)
                output_node = self.get_node_by_name(conn.output_node_name)

                try:
                    input_node._on_input_disconnected.trigger(conn.input_name, output_node, conn.output_name)
                    output_node._on_output_disconnected.trigger(conn.output_name, input_node, conn.input_name)
                    self.on_connection_removed.trigger(connection)
                except Exception as e:
                    input_node._on_error.trigger(e)
                    output_node._on_error.trigger(e)
                    raise e
                finally:
                    del self.connections[connection_to_remove]
                break
            
    def remove_connections_for_node(self, node: BaseNode|str):
        print(f"Removing connections for node: {node}")
        node_name = node if isinstance(node, str) else self.get_node_name(node)
        connections_to_remove = self.get_connections_for_node(node_name)
        for connection in connections_to_remove:
            self.remove_connection(connection)

    def remove_output_connection_for_node(self, node: BaseNode|str, output_name: str):
        print(f"Removing output connection for node: {node}")
        node_name = node if isinstance(node, str) else self.get_node_name(node)
        connections_to_remove = [connection for connection in self.get_output_connections_for_node(node_name) if connection.output_name == output_name]
        for connection in connections_to_remove:
            self.remove_connection(connection)

    def remove_input_connection_for_node(self, node: BaseNode|str, input_name: str):
        print(f"Removing input connection for node: {node}")
        node_name = node if isinstance(node, str) else self.get_node_name(node)
        connections_to_remove = [connection for connection in self.get_input_connections_for_node(node_name) if connection.input_name == input_name]
        for connection in connections_to_remove:
            self.remove_connection(connection)

    def remove_node(self, node: BaseNode|str):
        print(f"Removing node: {node}")
        node_name = node if isinstance(node, str) else self.get_node_name(node)
        self.remove_connections_for_node(node_name)
        self.on_node_removed.trigger(node)
        del self.nodes[node_name]
    
    def clear(self):
        self.nodes = {}
        self.connections = {}

        self.__running = False
        self._run_results = {}
        self.__nodes_with_unfinished_generator_inputs = set()
        self.__nodes_with_unfinished_generator_outputs = set()

        # run_data lock


    def save_to_file(self, file_path: str):
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        data = {
            "nodes": {},
            "connections": {}
        }

        for name, node in self.nodes.items():
            data["nodes"][name] = node.save_to_dict()

        for key, connection in self.connections.items():
            data["connections"][key] = connection.save_to_dict()

        with open(file_path, "w") as file:
            yaml.dump(data, file)


    def load_from_file(self, file_path: str):

        with open(file_path, "r") as file:
            data = yaml.load(file, Loader=yaml.FullLoader)

        for name, node_data in data["nodes"].items():
            node: BaseNode = self.available_nodes.get(node_data.get("type"), UnknownNode)()
            try:
                node.load_from_dict(node_data)
            except Exception as e:
                node._on_error.trigger(e)
            self.nodes[name] = node
            self.on_node_added.trigger(node)

        for key, connection_data in data["connections"].items():
            connection = Connection()
            try:
                connection.load_from_dict(connection_data)

                # check if can add connection
                output_node = self.get_node_by_name(connection.output_node_name)
                input_node = self.get_node_by_name(connection.input_node_name)
                can_connect, error = self.can_add_connection(output_node, connection.output_name, input_node, connection.input_name)
                if not can_connect:
                    raise GraphException(error)

                self.connections[key] = connection
            except Exception as e:
                self.on_error.trigger(e)
                continue

            try:    
                self.on_connection_added.trigger(connection)
                input_node = self.get_node_by_name(connection.input_node_name)
                output_node = self.get_node_by_name(connection.output_node_name)

                input_node._on_input_connected.trigger(connection.input_name, output_node, connection.output_name)
                output_node._on_output_connected.trigger(connection.output_name, input_node, connection.input_name)
            except Exception as e:
                self.on_error.trigger(e)

    def __mark_loop_as_finished(self, node: BaseNode):
        # get output connections
        output_connections = self.get_output_connections_for_node(node)

        # if any ot the output is generator with unfinished input, mark it as finished
        # and remove it from the list
        # else, continue with loop
        for connection in output_connections:
            input_node = self.get_node_by_name(connection.input_node_name)
            if connection.input_name in input_node.input_definitions:
                definition = input_node.input_definitions[connection.input_name]
                if definition.kind == AttributeKind.GENERATOR:
                    if connection.input_node_name in self.__nodes_with_unfinished_generator_inputs:
                        self.__nodes_with_unfinished_generator_inputs.remove(connection.input_node_name)

                        # run node with generator input as generator exit
                        inputs_override = {connection.input_name: BaseNode.GeneratorExit()}
                        self.__run_node(input_node, inputs_override)
                    else:
                        self.__mark_loop_as_finished(input_node)
                else:
                    self.__mark_loop_as_finished(input_node)

    def __run_node(self, node: BaseNode, inputs_override: dict[str, any] = {}):
        
       
        node_name = self.get_node_name(node)
        print(f"Running node: {node_name}")

        # get input data
        input_data = node.default_inputs.copy()
        for connection in self.get_input_connections_for_node(node):

            output_data = self._run_results.get(connection.output_node_name, None)

            if connection.output_node_name in self._run_results and len(output_data) == 0:
                self.__run_node(self.get_node_by_name(connection.output_node_name))

            output_data = self._run_results.get(connection.output_node_name, {}).get(connection.output_name, BaseNode.GeneratorExit())
            input_data[connection.input_name] = output_data


        input_data.update(inputs_override)
        print(input_data)

        # run node
        result = node.run(**input_data)
        self._run_results[node_name] = result

        for name, definition in node.output_definitions.items():
            if definition.kind == AttributeKind.GENERATOR:
                output_result = result[name]
                if output_result != BaseNode.GeneratorExit():
                    self.__nodes_with_unfinished_generator_outputs.add(node_name)
                elif node_name in self.__nodes_with_unfinished_generator_outputs:
                    self.__nodes_with_unfinished_generator_outputs.remove(node_name)
                    self.__mark_loop_as_finished(node)

        for name, definition in node.input_definitions.items():
            if definition.kind == AttributeKind.GENERATOR:
                input_result = input_data[name]
                if input_result != BaseNode.GeneratorExit():
                    self.__nodes_with_unfinished_generator_inputs.add(node_name)
                elif node_name in self.__nodes_with_unfinished_generator_inputs:
                    self.__nodes_with_unfinished_generator_inputs.remove(node_name)

        # clear non cacheable input nodes
        for connection in self.get_input_connections_for_node(node):
            if not self.get_node_by_name(connection.output_node_name).cache:
                self._run_results[connection.output_node_name] = {}
                print(f"Clearing node {connection.output_node_name}")

        return result

    def __can_run_node(self, node: BaseNode) -> bool:
        for connection in self.get_input_connections_for_node(node):
            output_node = self.get_node_by_name(connection.output_node_name)
            input_node = self.get_node_by_name(connection.input_node_name)

            definition = input_node.input_definitions[connection.input_name]
            if definition.kind == AttributeKind.EVENT:
                continue

            if connection.output_node_name not in self._run_results:
                if not output_node.cache:
                    can_run_output_node = self.__can_run_node(output_node)
                    if not can_run_output_node:
                        print(f"Cant run node {input_node} because output node {output_node} cant run")
                        return False
                    continue

                else:
                    print(f"Cant run node {input_node} because output node {output_node} is not in run results")
                    return False
            if connection.output_name not in self._run_results[connection.output_node_name]:
                print(f"Cant run node {input_node} because output name {connection.output_name} is not in run results")
                return False
            
            node_value = self._run_results[connection.output_node_name][connection.output_name]
            if node_value == BaseNode.GeneratorExit() or node_value == BaseNode.GeneratorContinue():
                print(f"Cant run node {input_node} because output node {connection.output_node_name} is generator exit or continue")
                return False
            
        return True
    
    def __run(self):

        # get all staring nodes
        run_queue = queue.Queue()
        scheduled_nodes = set()
        nodes_priority = {}
        iteration_counter = 0

        for node in self.nodes.values():
            if len(self.get_input_connections_for_node(node)) == 0:
                run_queue.put(node)
                node_name = self.get_node_name(node)
                nodes_priority[node_name] = iteration_counter

        # init nodes
        for node in self.nodes.values():
            if not self.__running:
                return
            
            try:
                if not node.lazy_init:
                    node._on_init.trigger()
                    node.init()
                    node._on_init_finished.trigger()
            except Exception as e:
                self.on_error.trigger(e)
                node._on_error.trigger(e)
                self.__running = False
                break

        # run nodes
        while not run_queue.empty() and self.__running:

            iteration_counter += 1

            node: BaseNode = run_queue.get()
            node_name = self.get_node_name(node)

            if node in scheduled_nodes:
                scheduled_nodes.remove(node)

            try:

                node._on_run.trigger()
                # time.sleep(1)
                self.__run_node(node)
                node._on_run_finished.trigger()
            except Exception as e:
                node._on_error.trigger(e)
                self.__running = False
                break

            for connection in self.get_output_connections_for_node(node):
                input_node = self.get_node_by_name(connection.input_node_name)
                input_node_name = self.get_node_name(input_node)
                scheduled_nodes.add(input_node)
                if input_node_name not in nodes_priority:
                    nodes_priority[input_node_name] = iteration_counter

            if run_queue.qsize() == 0:
                # sort nodes by priority descending
                sorted_nodes = sorted(scheduled_nodes, key=lambda x: -nodes_priority[self.get_node_name(x)])

                # add nodes to queue
                for node in sorted_nodes:
                    if self.__can_run_node(node):
                        run_queue.put(node)
                        scheduled_nodes.remove(node)
            
            if run_queue.qsize() == 0:
                #  find unfinished generator input with largest priority
                max_priority = -1
                max_node = None
                for node_name in self.__nodes_with_unfinished_generator_outputs:
                    node = self.get_node_by_name(node_name)
                    if nodes_priority[node_name] > max_priority:
                        max_priority = nodes_priority[node_name]
                        max_node = node
                
                if max_node is not None:
                    print(f"Adding node with unfinished generator output: {max_node}")
                    run_queue.put(max_node)

        
        print("Finished running graph")
        for node in self.__nodes_with_unfinished_generator_outputs:
            print(f"Node with unfinished generator output: {node}")

                

    def run(self):
        if self.__running:
            return

        self.__running = True
        # self.__main_process = multiprocessing.Process(target=self.__run)

        def run():
            try:
                self.on_graph_started.trigger()
                self.__run()
            except Exception as e:
                self.on_error.trigger(e)
            finally:
                self.__running = False
                self.on_graph_stopped.trigger()

        self.__main_process = threading.Thread(target=run)
        self.__main_process.start()

    def stop(self):
        if not self.__running:
            return

        self.__running = False

    def kill(self):
        if self.__main_process is not None:
            self.__main_process.terminate()
            self.__main_process = None 