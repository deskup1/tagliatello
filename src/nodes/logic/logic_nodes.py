from ...graph import BaseNode, AttributeKind, AttributeDefinition, AnyAttributeDefinition, IntegerAttributeDefinition, ListAttributeDefinition, BoolenAttributeDefinition, FloatAttributeDefinition, StringAttributeDefinition
from ...graph import DPG_DEFAULT_INPUT_WIDTH
import dearpygui.dearpygui as dpg
from ..progress_node import ProgressNode

class IteratorNode(ProgressNode):

    def __init__(self):
        super().__init__()
        self.last_id = 0

    def init(self):
        self.last_id = 0
        super().init()
        
    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "in": ListAttributeDefinition(AnyAttributeDefinition()),
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
            self.set_progress(0,0)
            return {"out": BaseNode.GeneratorExit()}
        elif not isinstance(input, list):
            self.set_progress(-1, -1)
            raise ValueError("Input is not a list")
        
        if self.last_id >= len(input):
            self.set_progress(len(input), len(input))
            self.last_id = 0
            return {"out": BaseNode.GeneratorExit()}
        
        output = input[self.last_id]
        self.set_progress(self.last_id, len(input))
        self.last_id += 1
        return {"out": output}

class IfElseNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.set_default_input("condition", False)

        self.__outputs_definitions = {"true": AnyAttributeDefinition(kind=AttributeKind.EVENT), "false": AnyAttributeDefinition(kind=AttributeKind.EVENT)}

    def _on_input_connected(self, input_name: str, output_node: BaseNode, output_name: str):
        if input_name == "condition":
            attribute_type = output_node.output_definitions[output_name].copy()
            attribute_type.kind = AttributeKind.EVENT
            self.__outputs_definitions = {"true": attribute_type, "false": attribute_type}
            self.refresh_ui()

    def _on_input_disconnected(self, input_name: str, output_node: BaseNode, output_name: str):
        if input_name == "condition":
            self.__outputs_definitions = {"true": AnyAttributeDefinition(kind=AttributeKind.EVENT), "false": AnyAttributeDefinition(kind=AttributeKind.EVENT)}
            self.refresh_ui()

    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "condition": BoolenAttributeDefinition(),
            "input": AnyAttributeDefinition()
        }
    
    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return self.__outputs_definitions
    
    @classmethod
    def name(cls) -> str:
        return "If Else"
    
    @classmethod
    def category(cls) -> str:
        return "Logic"
    
    def run(self, **kwargs) -> dict:
        condition = kwargs.get("condition", False)
        input = kwargs.get("input")

        if condition:
            return {"true": input, "false": BaseNode.GeneratorExit()}
        else:
            return {"false": input, "true": BaseNode.GeneratorExit()}
        
class IsNullNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.set_default_input("input", None)

    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "input": AnyAttributeDefinition()
        }
    
    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "out": BoolenAttributeDefinition()
        }
    
    @classmethod
    def name(cls) -> str:
        return "Is Null"
    
    @classmethod
    def category(cls) -> str:
        return "Logic"
    
    def run(self, **kwargs) -> dict:
        input = kwargs.get("input")
        return {"out": input is None}
    
class IsNullOrEmptyNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.set_default_input("input", "")

    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "input": AnyAttributeDefinition()
        }
    
    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "out": BoolenAttributeDefinition()
        }
    
    @classmethod
    def name(cls) -> str:
        return "Is Null Or Empty"
    
    @classmethod
    def category(cls) -> str:
        return "Logic"
    
    def run(self, **kwargs) -> dict:
        input = kwargs.get("input")
        if input == None:
            return {"out": True}
        elif isinstance(input, str):
            return {"out": input == ""}
        elif isinstance(input, list):
            return {"out": len(input) == 0}
        elif isinstance(input, dict):
            return {"out": len(input) == 0}
        else:
            return {"out": False}


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
                self.__outputs_definitions[f"out{i}"] = attribute_type.copy()
                self.__outputs_definitions[f"out{i}"].kind = AttributeKind.EVENT
        self.refresh_ui()

    def __on_input_disconnected(self, input_name: str):
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
            self.count_input = dpg.add_input_int(label="Count", 
                                                 parent=parent, 
                                                 default_value=default_value, 
                                                 min_value=2, min_clamped=True, 
                                                 max_value=16, max_clamped=True, 
                                                 callback= self.__on_count_changed, 
                                                 width=DPG_DEFAULT_INPUT_WIDTH)

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
        return {"out": ListAttributeDefinition(AnyAttributeDefinition(), kind=AttributeKind.EVENT)}
    
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
            result = self.collected
            self.collected = []
            return {"out": result}
        else:
            self.collected.append(input)
            return {"out": BaseNode.GeneratorContinue()}
        
class ConnectorNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.set_static_input("count", 2)
        self.count_input = None
        self.__inputs_definitions = {"input0": AnyAttributeDefinition(kind=AttributeKind.EVENT), "input1": AnyAttributeDefinition(kind=AttributeKind.EVENT)}

    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return self.__inputs_definitions
    
    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return {"out": AnyAttributeDefinition(kind=AttributeKind.EVENT)}
    
    @classmethod
    def name(cls) -> str:
        return "Connector"
    
    @classmethod
    def category(cls) -> str:
        return "Logic"
    
    def load_from_dict(self, data: dict):
        super().load_from_dict(data)

        count = self.static_inputs.get("count", 2)
        self.__inputs_definitions = {}
        for i in range(count):
            self.__inputs_definitions[f"input{i}"] = AnyAttributeDefinition(kind=AttributeKind.EVENT)
    
    def __on_count_changed(self, sender, app_data):
        self.set_static_input("count", app_data)

        output_definition = self.__inputs_definitions.get("input0", AnyAttributeDefinition(kind=AttributeKind.EVENT))
        output_definition.kind = AttributeKind.EVENT

        self.__inputs_definitions = {}
        for i in range(app_data):
            self.__inputs_definitions[f"input{i}"] = output_definition
        self.refresh_ui()

    def show_custom_ui(self, parent: int | str):
        default_value = self.static_inputs.get("count", 2)

        if self.count_input is None or not dpg.does_item_exist(self.count_input):
            self.count_input = dpg.add_input_int(label="Count", 
                                                 parent=parent, 
                                                 default_value=default_value, 
                                                 min_value=2, 
                                                 min_clamped=True, 
                                                 max_value=16, 
                                                 max_clamped=True, 
                                                 callback= self.__on_count_changed, 
                                                 width=DPG_DEFAULT_INPUT_WIDTH)

    def run(self, **kwargs) -> dict:
        for item in kwargs.values():
            if item != BaseNode.GeneratorExit() and item != BaseNode.GeneratorContinue():
                return {"out": item}
        return {"out": BaseNode.GeneratorExit()}

class LoopNode(ProgressNode):
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
        super().init()
    
    def run(self, **kwargs) -> dict:
        count = kwargs.get("count", 1)
        input = kwargs.get("input")

        if self.last_id >= count:
            self.set_progress(count, count)
            self.last_id = 0
            return {"out": BaseNode.GeneratorExit()}
        else:
            self.set_progress(self.last_id, count)
            self.last_id += 1
            return {"out": input}

class ReplaceNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.set_default_input("input", "")
        self.set_default_input("replace", "")

    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "trigger": AnyAttributeDefinition(),
            "input": AnyAttributeDefinition(),
        }
    
    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "input": AnyAttributeDefinition()
        }
    
    @classmethod
    def name(cls) -> str:
        return "Replace"
    
    @classmethod
    def category(cls) -> str:
        return "Logic"
    
    def run(self, **kwargs) -> dict:
        replace = kwargs.get("replace")
        return {"out": replace}