import sys
if __name__ == "__main__":
    sys.path.append("src")

from .node import BaseNode, AttributeKind, BaseNodeEvent

import queue
import yaml

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


        self.__counter = 0

        self.__max_concurrency = 10
        self.__run_data = {}
        self.__queue = queue.PriorityQueue()
        self.__running = False

    class __QueueItem:
        def __init__(self, priority, item):
            self.priority = priority
            self.item = item
        
        def __lt__(self, other):
            if hasattr(other, "priority"):
                return self.priority < other.priority
            return True
        
        def __iter__(self):
            return iter([self.priority, self.item])
        
        def __getitem__(self, key):
            if key == 0:
                return self.priority
            if key == 1:
                return self.item
            raise IndexError("Index out of range")

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
            raise Exception(error)
        
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
        self.__run_data_finished = []

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

    def __validate_run_results(self, results: dict[str, dict], node: BaseNode):
        for output_name, output_data in results.items():
            if output_name not in node.output_definitions:
                raise Exception(f"Returned output name not found in node outputs: {output_name}")


    def __check_if_node_can_be_added(self, node: BaseNode) -> bool:

        # check if finished
        if self.get_node_name(node) in self.__run_data_finished:
            print(f"Node {node.name()} already finished")
            return False
        
        # check if already in queue
        for tuple in self.__queue.queue:
            if tuple[1] == node:
                print(f"Node {node.name()} already in queue")
                return False
            
        # check if every input is filled
        input_connections = self.get_input_connections_for_node(node)
        for connection in input_connections:

            # if input node is not in run data, skip
            if connection.output_node_name not in self.__run_data:
                print(f"Node {node.name()} input node {connection.output_node_name} not in run data")
                return False
            
            # if output name is not in run data, skip
            if connection.output_name not in self.__run_data[connection.output_node_name]:
                print(f"Node {node.name()} output name {connection.output_name} not in run data")
                return False
            
            # if output is GeneratorContinue, skip
            if isinstance(self.__run_data[connection.output_node_name][connection.output_name], BaseNode.GeneratorContinue):
                print(f"Node {node.name()} output {connection.output_name} is GeneratorContinue")
                return False

        return True

    def __set_run_data(self, node: BaseNode, results: dict[str, dict]):
        self.__run_data[self.get_node_name(node)] = results

    def __run_node(self, node: BaseNode):
        try:
            # check if initialized
            node_name = self.get_node_name(node)
            if node_name not in self.__run_data and node.lazy_init:
                print(f"Initializing node {node.name()}")
                node._on_init.trigger()
                node.init()
                node._on_init_finished.trigger()

            # get inputs
            input_connections = self.get_input_connections_for_node(node_name)
            inputs = {}
            for connection in input_connections:
                output_data = self.__run_data[connection.output_node_name]
                inputs[connection.input_name] = output_data[connection.output_name]

            inputs = { **node.default_inputs, **inputs}


            for input_name, _ in node.input_definitions.items():
                # if input_name is generator, skip
                if node.input_definitions[input_name].kind == AttributeKind.GENERATOR:
                    continue
                
                # if any of the inputs is GeneratorExit, don't run node and mark it as finished
                if isinstance(inputs.get(input_name), BaseNode.GeneratorExit):
                    self.__run_data_finished.append(node_name)
                    return
        
            print(f"Running node {node.name()}")
            node._on_run.trigger()
            results = node.run(**inputs)
            self.__validate_run_results(results, node)
            node._on_run_finished.trigger()

            # if any of inputs is generator and its input is finished, rerun node
            should_rerun = False
            for connection in input_connections:
                if node.input_definitions[connection.input_name].kind == AttributeKind.GENERATOR:
                    if connection.output_node_name in self.__run_data_finished:
                        should_rerun = True
                        inputs[connection.input_name] = BaseNode.GeneratorExit()

            if should_rerun:
                print(f"Rerunning node {node.name()}")
                node._on_run.trigger()
                results = node.run(**inputs)
                self.__validate_run_results(results, node)
                node._on_run_finished.trigger()


            def rerun_non_cached_nodes():
                nodes_to_run = set()
                for connection in input_connections:
                    input_node = self.get_node_by_name(connection.output_node_name)
                    if not input_node.cache == False:
                        continue
                    nodes_to_run.add(input_node)
                for node in nodes_to_run:
                    print(f"Rerunning non-cached node {self.get_node_name(node)}")
                    self.__run_node(node)
                return False

            # if any of the inputs is not finished, don't mark node as finished
            for connection in input_connections:
                if connection.output_node_name not in self.__run_data_finished:
                    self.__set_run_data(node, results)
                    rerun_non_cached_nodes()
                    return

            # if has generator output which didn't return GeneratorExit, don't mark node as finished
            for output_name, output_definition in node.output_definitions.items():
                if output_definition.kind == AttributeKind.GENERATOR:
                    if not isinstance(results[output_name], BaseNode.GeneratorExit):
                        self.__set_run_data(node, results)
                        rerun_non_cached_nodes()
                        return

            self.__set_run_data(node, results)
            self.__run_data_finished.append(self.get_node_name(node))

        except Exception as e:
            self.__running = False
            node._on_error.trigger(e)
            raise e
                    

    def run(self):


        self.__running = True
        self.__run_data = {}
        self.__run_data_finished = []

        # get nodes without inputs
        nodes = [node for node in self.nodes.values() if self.__check_if_node_can_be_added(node)]

        # append nodes to queue
        for node in nodes:
            self.__queue.put(Graph.__QueueItem(0, node))

        print("Running")
        for node in self.nodes.values():
            if node.lazy_init == False:
                try:
                    node._on_init.trigger()
                    node.init()
                    node._on_init_finished.trigger()
                except Exception as e:
                    node._on_error.trigger(e)
                    raise e

        # main loop
        while not self.__queue.empty():

            priority, node = self.__queue.get()
            node_name = self.get_node_name(node)

            self.__run_node(node)

            node_outputs = node.output_definitions
            for output_name, output_definition in node_outputs.items():

                # add self to queue if any of the outputs is generator which didn't return GeneratorExit
                if output_definition.kind != AttributeKind.GENERATOR:
                    continue

                if not isinstance(self.__run_data[node_name][output_name], BaseNode.GeneratorExit):
                    exists = False
                    for tuple in self.__queue.queue:
                        if tuple[1] == node:
                            self.__queue.queue.remove(tuple)
                            self.__queue.put(Graph.__QueueItem(tuple[0] + priority + 1000, node))
                            exists = True
                            print(f"Changing priority of node {node.name()} in queue")

                    if not exists:
                        print(f"Adding node {node.name()} to queue - generator output {output_name}")
                        self.__queue.put(Graph.__QueueItem(priority + 1000, node))

            # get output connections
            output_connections = self.get_output_connections_for_node(node_name)
            # append connected nodes to queue if they can run
            for connection in output_connections:
                output_node = self.get_node_by_name(connection.input_node_name)


                if self.__check_if_node_can_be_added(output_node):
                    print(f"Adding node {output_node.name()} to queue - output of {self.get_node_name(node)}")
                    self.__queue.put(Graph.__QueueItem(priority + 1, output_node))

            if self.__queue.qsize() == 0:

                # get nodes which can run
                nodes = [node for node in self.nodes.values() if self.__check_if_node_can_be_added(node)]

                if len(nodes) != 0:
                    for node in nodes:
                        print(f"Node {node.name()} can run")

                    raise Exception("Deadlock detected")

        print("Finished running")
        self.__running = False
