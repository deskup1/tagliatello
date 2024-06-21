from ...graph import BaseNode, AttributeKind, AttributeDefinition, AnyAttributeDefinition, IntegerAttributeDefinition, MultipleAttributeDefinition, BoolenAttributeDefinition, FloatAttributeDefinition, StringAttributeDefinition
import dearpygui.dearpygui as dpg

class IteratorNode(BaseNode):

    def __init__(self):
        super().__init__()
        self.last_id = 0

    def init(self):
        self.last_id = 0
        
    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "in": AnyAttributeDefinition(list=True),
        }

    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "out": AnyAttributeDefinition(kind=AttributeKind.GENERATOR)
            }

    @classmethod
    def name(cls) -> str:
        return "Iterator"

    @classmethod
    def category(cls) -> str:
        return "Logic"

    def run(self, **kwargs) -> dict:
        input = kwargs.get("in")
        if input is None:
            return {"out": BaseNode.GeneratorExit()}
        elif not isinstance(input, list):
            raise ValueError("Input is not a list")
        
        if self.last_id >= len(input):
            return {"out": BaseNode.GeneratorExit()}
        
        output = input[self.last_id]
        self.last_id += 1
        return {"out": output}

class SwitchNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.set_default_input("id", 0)
        self.set_static_input("count", 2)

        self.__outputs_definitions = {"out0" : AnyAttributeDefinition(kind=AttributeKind.EVENT), "out1" : AnyAttributeDefinition(kind=AttributeKind.EVENT)}
        self._on_input_connected += self.__on_input_connected
        self._on_input_disconnected += self.__on_input_disconnected

        self.count_input = None

    def load_from_dict(self, data: dict):
        super().load_from_dict(data)

        count = self.static_inputs.get("count", 2)
        self.__outputs_definitions = {}
        for i in range(count):
            self.__outputs_definitions[f"out{i}"] = AnyAttributeDefinition(kind=AttributeKind.EVENT)


    def __on_input_connected(self, input_name: str, output_node: BaseNode, output_name: str):
        count = self.static_inputs.get("count", 2)

        attribute_type = output_node.output_definitions[output_name]
        if input_name == "input":
            self.__outputs_definitions = {}
            for i in range(count):
                self.__outputs_definitions[f"out{i}"] = attribute_type
        self.refresh_ui()

    def __on_input_disconnected(self, input_name: str, output_node: BaseNode, output_name: str):
        count = self.static_inputs.get("count", 2)
        if input_name == "input":
            self.__outputs_definitions = {}
            for i in range(count):
                self.__outputs_definitions[f"out{i}"] = AnyAttributeDefinition(kind=AttributeKind.EVENT)
        self.refresh_ui()

    def __on_count_changed(self, sender, app_data):
        self.set_static_input("count", app_data)

        output_definition = self.__outputs_definitions.get("out0", AnyAttributeDefinition(kind=AttributeKind.EVENT))
        output_definition.kind = AttributeKind.EVENT

        self.__outputs_definitions = {}
        for i in range(app_data):
            self.__outputs_definitions[f"out{i}"] = output_definition
        self.refresh_ui()

    def show_custom_ui(self, parent: int | str):
        default_value = self.static_inputs.get("count", 2)

        if self.count_input is None or not dpg.does_item_exist(self.count_input):
            self.count_input = dpg.add_input_int(label="Count", parent=parent, default_value=default_value, min_value=2, min_clamped=True, max_value=16, max_clamped=True, callback= self.__on_count_changed, width=100)

    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "id": IntegerAttributeDefinition(),
            "input": AnyAttributeDefinition()
        }
    
    
    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return self.__outputs_definitions
    
    @classmethod
    def name(cls) -> str:
        return "Switch"
    
    @classmethod
    def category(cls) -> str:
        return "Logic"
    
    def run(self, **kwargs) -> dict:
        id = kwargs["id"]
        input = kwargs["input"]
        count = self.static_inputs.get("count", 2)

        if not isinstance(id, (int, bool)):
            raise ValueError("ID is not an integer or boolean")
        
        if id < 0 or id >= count:
            raise ValueError("ID is out of range")
        
        result = {}
        for i in range(count):
            if i == id:
                result[f"out{i}"] = input
            else:
                result[f"out{i}"] = BaseNode.GeneratorExit()

        return result
    
class CollectorNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.collected = []


    def show_custom_ui(self, parent: int | str):
        pass

    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return { "in": AnyAttributeDefinition(kind=AttributeKind.GENERATOR) }
    
    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return {"out": AnyAttributeDefinition(list=True, kind=AttributeKind.EVENT)}
    
    @classmethod
    def name(cls) -> str:
        return "Collector"
    
    @classmethod
    def category(cls) -> str:
        return "Logic"
    
    def init(self):
        self.collected = []
    
    def run(self, **kwargs) -> dict:
        input = kwargs.get("in")
        if isinstance(input, BaseNode.GeneratorExit):
            return {"out": self.collected}
        else:
            self.collected.append(input)
            return {"out": BaseNode.GeneratorContinue()}

class LoopNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.set_default_input("count", 1)
        self.last_id = 0

    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "input": AnyAttributeDefinition(),
            "count": IntegerAttributeDefinition()
        }
    
    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return {"out": AnyAttributeDefinition(kind=AttributeKind.GENERATOR)}
    
    @classmethod
    def name(cls) -> str:
        return "Loop"
    
    @classmethod
    def category(cls) -> str:
        return "Logic"
    
    def init(self):
        self.last_id = 0
    
    def run(self, **kwargs) -> dict:
        count = kwargs.get("count", 1)
        input = kwargs.get("input")

        if self.last_id >= count:
            return {"out": BaseNode.GeneratorExit()}
        else:
            self.last_id += 1
            return {"out": input}