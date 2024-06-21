import sys
if __name__ == "__main__":
    sys.path.append("src")

from .node import BaseNode, AttributeKind, BaseNodeEvent

import queue
import yaml
import threading
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


        self.__counter = 0

        self.__max_concurrency = 10

        self.__run_data_nodes_results = {}
        self.__run_data_nodes_finished = []
        self.__run_data_jobs = {}
        self.__run_data_lock = threading.Lock()
        self.__main_thread: threading.Thread = None

        self.__running = False

    def  is_running(self) -> bool:
        return self.__running

    def register_nodes(self, nodes: list[BaseNode]):
        for node in nodes:
            self.register_node(node)

    def register_node(self, node_cls):
        self.available_nodes[node_cls.name()] = node_cls

    def add_node(self, node: BaseNode) -> str:
        name = f"{node.name()}_{self.__counter}"
        self.__counter += 1
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
        self.__counter = 0

        self.__running = False
        self.__run_data = {}
        self.__run_data_nodes_finished = []

        # run_data lock


    def save_to_file(self, file_path: str):
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
            node = self.available_nodes[node_data["type"]]()
            node.load_from_dict(node_data)
            self.nodes[name] = node
            self.on_node_added.trigger(node)

        for key, connection_data in data["connections"].items():
            connection = Connection()
            connection.load_from_dict(connection_data)
            self.connections[key] = connection

            self.on_connection_added.trigger(connection)
            input_node = self.get_node_by_name(connection.input_node_name)
            output_node = self.get_node_by_name(connection.output_node_name)

            input_node._on_input_connected.trigger(connection.input_name, output_node, connection.output_name)
            output_node._on_output_connected.trigger(connection.output_name, input_node, connection.input_name)

        # find node name with highest counter
        max_counter = 0
        for name in self.nodes.keys():
            # remove all characters from name which are not digits
            counter = int(''.join(filter(str.isdigit, name)))
            if counter > max_counter:
                max_counter = counter

        self.__counter = max_counter + 1


    def __get_available_nodes(self):

        available_nodes = []
        for name, node in self.nodes.items():

            # check if node is finished
            if name in self.__run_data_nodes_finished:
                continue

            # check if running
            if name in self.__run_data_jobs:
                continue

            inputs = self.get_input_connections_for_node(name)
            outputs = self.get_output_connections_for_node(name)

            # check if any input is running
            inputs_running = False
            for input_connection in inputs:
                if input_connection.output_node_name in self.__run_data_jobs:
                    inputs_running = True
                    break
            if inputs_running:
                continue

                # check if any output is running
            outputs_running = False
            for output_connection in outputs:
                if output_connection.input_node_name in self.__run_data_jobs:
                    outputs_running = True
                    break
            if outputs_running:
                continue
      
            # check if all inputs are finished
            inputs_finished = True
            for input_connection in inputs:
                if input_connection.output_node_name not in self.__run_data_nodes_finished:
                    inputs_finished = False
                    break

                run_data = self.__run_data_nodes_results.get(input_connection.output_node_name, {})
                input_data = run_data.get(input_connection.output_name, None) if run_data is not None else None

                if input_data is None:
                    print(f"Input data is None: {input_connection.output_node_name}.{input_connection.output_name}")
                    break

                input_type = node.input_definitions.get(input_connection.input_name, None)
                if input_type.kind == AttributeKind.GENERATOR and isinstance(input_data, BaseNode.GeneratorExit):
                    continue

                if isinstance(input_data, BaseNode.GeneratorContinue) or isinstance(input_data, BaseNode.GeneratorExit):
                    inputs_finished = False
                    break

            if not inputs_finished:
                continue

            # check if atleast 1 output is not finished if node is non cacheable
            outputs_finished = False
            if not node.cache:
                outputs_finished = True
                for output_connection in outputs:
                    if output_connection.input_node_name not in self.__run_data_nodes_finished:
                        outputs_finished = False
                        break

                    run_data = self.__run_data_nodes_results.get(output_connection.input_node_name, {})
                    output_data = run_data.get(output_connection.input_name, None)
                    if isinstance(output_data, BaseNode.GeneratorContinue) or isinstance(output_data, BaseNode.GeneratorExit):
                        outputs_finished = False
                        break

            if outputs_finished:
                continue

            available_nodes.append(name)

        return available_nodes

    def stop(self):
        self.__running = False
        self.__run_data_nodes_results = {}
        self.__run_data_nodes_finished = []
        self.__run_data_jobs = {}
        for node in self.nodes.values():
            try:
                pass
                # node.stop()
            except Exception as e:
                node._on_error.trigger(e)
        self.on_graph_stopped.trigger()
        print("Graph stopped")

    def __mark_all_outputs_as_not_finished(self, node: BaseNode, make_self_not_finished: bool = True):

        node_name = self.get_node_name(node)
        if node_name not in self.__run_data_nodes_finished:
            return
        
        # mark node as not finished
        if make_self_not_finished:
            self.__run_data_nodes_finished.remove(node_name)
            node._on_node_ready.trigger()

        # get all output connections
        output_connections = self.get_output_connections_for_node(node)
        for output_connection in output_connections:
            output_node = self.get_node_by_name(output_connection.input_node_name)
            self.__mark_all_outputs_as_not_finished(output_node, True)

    def __mark_output_generators_as_not_finished(self) -> bool:
        any_generators = False
        for node in self.nodes.values():

            node_name = self.get_node_name(node)
            if node_name not in self.__run_data_nodes_finished:
                continue


            for name, definition in node.output_definitions.items():
                if definition.kind != AttributeKind.GENERATOR:
                    continue

                result = self.__run_data_nodes_results.get(node_name, {})
                output_result = result.get(name, None)

                if not isinstance(output_result, BaseNode.GeneratorExit):
                    any_generators = True

                    self.__run_data_nodes_finished.remove(node_name)
                    
                    node._on_node_ready.trigger()
                    break

        return any_generators
    
    def __mark_input_generators_as_not_finished(self):
        
        has_generators = False
        for node in self.nodes.values():
            node_name = self.get_node_name(node)

            # skip if node is not finished
            if node_name not in self.__run_data_nodes_finished:
                continue

            mark_as_not_finished = False

            input_connections = self.get_input_connections_for_node(node_name)
            for input_connection in input_connections:
                input_definition = node.input_definitions.get(input_connection.input_name, None)
                if input_definition is None or input_definition.kind != AttributeKind.GENERATOR:
                    continue

                result = self.__run_data_nodes_results.get(input_connection.output_node_name, {})
                input_result = result.get(input_connection.output_name, None)
                if not isinstance(input_result, BaseNode.GeneratorExit):
                    mark_as_not_finished = True
                    has_generators = True

                    # replace input with GeneratorExit
                    self.__run_data_nodes_results[input_connection.output_node_name][input_connection.output_name] = BaseNode.GeneratorExit()
                    break

            if mark_as_not_finished:
                self.__run_data_nodes_finished.remove(node_name)
                node._on_node_ready.trigger()


        return has_generators
    
    def __validate_node_results(self, node: BaseNode, results: dict):
        if results is None:
            raise GraphException(f"Results for node {node.name()} is None")
        if not isinstance(results, dict):
            raise GraphException(f"Results for node {node.name()} is not a dictionary")

        for name, definition in node.output_definitions.items():
            if name not in results:
                raise GraphException(f"Output name {name} not found in results for node {node.name()}")

    
    def __run_node(self, node: BaseNode):

        # init node if lazy init and has no results in run_data
        node_name = self.get_node_name(node)
        if node.lazy_init and node_name not in self.__run_data_nodes_results:
            try:
                node._on_init.trigger()
                node.init()
                node._on_init_finished.trigger()
            except Exception as e:
                node._on_error.trigger(e)
                self.stop()
                return

        input_data = {}
        input_connections = self.get_input_connections_for_node(node)
        for input_connection in input_connections:
            run_data: dict = self.__run_data_nodes_results.get(input_connection.output_node_name, {})
            input_data[input_connection.input_name] = run_data.get(input_connection.output_name, None)


        input_data = {**node.default_inputs, **input_data}

        # if any of the inputs are GeneratorExit, replace them with null
        for input_name, input_value in input_data.items():
            input_type = node.input_definitions.get(input_name, None)
            if isinstance(input_value, BaseNode.GeneratorExit) and input_type.kind != AttributeKind.GENERATOR:
                input_data[input_name] = None

        try:
            node._on_run.trigger()
            result = node.run(**input_data)
            node._on_run_finished.trigger()

            self.__validate_node_results(node, result)

        except Exception as e:
            node._on_error.trigger(e)
            self.stop()
            return
        

        self.__run_data_nodes_results[node_name] = result
        self.__run_data_nodes_finished.append(node_name)

        # check if any outputs are generators
        for output_name, output_definition in node.output_definitions.items():
            if output_definition.kind != AttributeKind.GENERATOR:
                continue
            output_result = result.get(output_name, None)
            if not isinstance(output_result, BaseNode.GeneratorExit):
                self.__mark_all_outputs_as_not_finished(node, False)
                break

        # check if any inputs are non caching
        for input_connection in input_connections:
            input_node = self.get_node_by_name(input_connection.output_node_name)
            if not input_node.cache:
                self.__run_data_nodes_finished.remove(input_connection.output_node_name)
                input_node._on_node_ready.trigger()
     
        del self.__run_data_jobs[node_name]
        

    def __run_loop(self):
        try:
            while self.__running:
                
                # if no available nodes and no running jobs, stop
                available_nodes = self.__get_available_nodes()

                if len(available_nodes) == 0 and len(self.__run_data_jobs) == 0:
                    # check if any output generators are not finished
                    if self.__mark_output_generators_as_not_finished():
                        continue

                    # check if any input generators are not finished
                    if self.__mark_input_generators_as_not_finished():
                        continue

                    self.stop()
                    break

                # if running jobs are more or equal to max concurrency, wait for some jobs to finish
                if len(self.__run_data_jobs) >= self.__max_concurrency:
                    continue

                # run available nodes
                while len(available_nodes) > 0 and len(self.__run_data_jobs) < self.__max_concurrency:
                    node_name = available_nodes.pop(0)
                    node = self.get_node_by_name(node_name)
                    # self.__run_data_jobs[node_name] = threading.Thread(target=self.__run_node, args=(node,)).start()
                    self.__run_data_jobs[node_name] = "dummy"
                    self.__run_node(node)
            
            self.stop()
        except Exception as e:
            self.stop()
            raise e

    def run(self, max_concurrency: int = 1):
        if self.__running:
            raise GraphException("Graph is already running")
        
        if self.__main_thread is not None and self.__main_thread.is_alive():
            raise GraphException("Graph is already running")
        
        if len(self.nodes) == 0:
            raise GraphException("No nodes in graph")
        
        self.__running = True
        self.__run_data_nodes_results = {}
        self.__run_data_nodes_finished = []
        self.__run_data_jobs = {}
        self.__max_concurrency = max_concurrency
        self.on_graph_started.trigger()
        

        # initialize all non lazy nodes
        for name, node in self.nodes.items():
            if not node.lazy_init:
                try:
                    node._on_init.trigger()
                    node.init()
                    node._on_init_finished.trigger()
                except Exception as e:
                    node._on_error.trigger(e)
                    self.stop()
                    return

        # start run loop on separate thread
        self.__main_thread = threading.Thread(target=self.__run_loop).start()