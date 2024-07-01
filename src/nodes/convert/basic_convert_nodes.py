from ...graph import BaseNode, AttributeKind, AttributeDefinition, ListAttributeDefinition ,IntegerAttributeDefinition, AnyAttributeDefinition, FloatAttributeDefinition, BoolenAttributeDefinition, StringAttributeDefinition
import copy

class ToAnyNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.set_default_input("in", 0)
    
    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {"in": AnyAttributeDefinition()}
    
    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return {"out": AnyAttributeDefinition()}
    
    @classmethod
    def name(cls) -> str:
        return "To Any"
    
    @classmethod
    def category(cls) -> str:
        return "Convert"
    
    def run(self, **kwargs) -> dict:
        return {"out": kwargs.get("in", 0)}
    
class ToListNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.set_default_input("in", 0)

        self.__output_definitions = {"out": ListAttributeDefinition(AnyAttributeDefinition())}

        self._on_input_connected += self.__change_output_definition_on_connect
        self._on_input_disconnected += self.__change_output_definition_on_disconnect

    def __change_output_definition_on_connect(self, input_name: str, output_node: BaseNode, output_name: str):
        definition = output_node.output_definitions.get(output_name, AnyAttributeDefinition())
        self.__output_definitions["out"] = definition.copy()
        self.__output_definitions["out"].kind = AttributeKind.VALUE
        self.refresh_ui()

    def __change_output_definition_on_disconnect(self, _, __, ___):
        self.__output_definitions["out"] = ListAttributeDefinition(AnyAttributeDefinition())
        self.refresh_ui()
    
    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {"in": AnyAttributeDefinition()}
    
    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return self.__output_definitions
    
    @classmethod
    def name(cls) -> str:
        return "To List"
    
    @classmethod
    def category(cls) -> str:
        return "Convert"
    
    def run(self, **kwargs) -> dict:
        return {"out": [kwargs.get("in", 0)]}

class ToIntegerNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.set_default_input("in", 0)
    
    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {"in": AnyAttributeDefinition()}
    
    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return {"out": IntegerAttributeDefinition()}
    
    @classmethod
    def name(cls) -> str:
        return "To Integer"
    
    @classmethod
    def category(cls) -> str:
        return "Convert"
    
    def run(self, **kwargs) -> dict:
        return {"out": kwargs.get("in", 0)}
    
class ToFloatNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.set_default_input("in", 0.0)
    
    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {"in": AnyAttributeDefinition()}
    
    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return {"out": FloatAttributeDefinition()}
    
    @classmethod
    def name(cls) -> str:
        return "To Float"
    
    @classmethod
    def category(cls) -> str:
        return "Convert"
    
    def run(self, **kwargs) -> dict:
        return {"out": kwargs.get("in", 0.0)}
    
class ToStringNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.set_default_input("in", "")
    
    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {"in": AnyAttributeDefinition()}
    
    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return {"out": StringAttributeDefinition()}
    
    @classmethod
    def name(cls) -> str:
        return "To String"
    
    @classmethod
    def category(cls) -> str:
        return "Convert"
    
    def run(self, **kwargs) -> dict:
        return {"out": str(kwargs.get("in", ""))}
    
class ToBooleanNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.set_default_input("in", False)
    
    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {"in": AnyAttributeDefinition()}
    
    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return {"out": BoolenAttributeDefinition()}
    
    @classmethod
    def name(cls) -> str:
        return "To Boolean"
    
    @classmethod
    def category(cls) -> str:
        return "Convert"
    
    def run(self, **kwargs) -> dict:
        return {"out": bool(kwargs.get("in", False))}
    
class SplitStringNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.set_default_input("separator", "\\n")
        self.set_default_input("in", "")
    
    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {"in": StringAttributeDefinition(), "separator": StringAttributeDefinition()}
    
    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return {"out": ListAttributeDefinition(StringAttributeDefinition())}
    
    @classmethod
    def name(cls) -> str:
        return "Split String"
    
    @classmethod
    def category(cls) -> str:
        return "Convert"
    
    def run(self, **kwargs) -> dict:
        separator: str = kwargs.get("separator", ",")
        in_data: str = kwargs.get("in", "")
        
        # unescape separator
        separator = separator.encode().decode('unicode_escape')

        return {"out": in_data.split(separator)}

class JoinStringNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.set_default_input("separator", "\\n")
        self.set_default_input("in", [])
    
    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {"in": ListAttributeDefinition(StringAttributeDefinition()), "separator": StringAttributeDefinition()}
    
    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return {"out": StringAttributeDefinition()}
    
    @classmethod
    def name(cls) -> str:
        return "Join String"
    
    @classmethod
    def category(cls) -> str:
        return "Convert"
    
    def run(self, **kwargs) -> dict:
        separator: str = kwargs.get("separator", ",")
        in_data: list[str] = kwargs.get("in", [])
        
        # unescape separator
        separator = separator.encode().decode('unicode_escape')

        return {"out": separator.join(in_data)}
    
class ListCountNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.set_default_input("in", [])
    
    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {"in": ListAttributeDefinition(AnyAttributeDefinition())}
    
    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return {"out": IntegerAttributeDefinition()}
    
    @classmethod
    def name(cls) -> str:
        return "List Count"
    
    @classmethod
    def category(cls) -> str:
        return "Convert"
    
    def run(self, **kwargs) -> dict:
        in_data: list = kwargs.get("in", [])
        return {"out": len(in_data)}