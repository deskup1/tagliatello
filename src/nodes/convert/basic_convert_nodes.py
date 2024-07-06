from ...graph import BaseNode, AttributeKind, AttributeDefinition, ListAttributeDefinition ,IntegerAttributeDefinition, AnyAttributeDefinition, FloatAttributeDefinition, BoolenAttributeDefinition, StringAttributeDefinition, DPG_DEFAULT_INPUT_WIDTH
import dearpygui.dearpygui as dpg

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
        self.set_static_input("count", 1)

        self.__output_definitions = {"out": ListAttributeDefinition(AnyAttributeDefinition())}
        self.__input_definitions = {"in[0]": AnyAttributeDefinition()}

    
    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return self.__input_definitions
    
    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return self.__output_definitions
    
    def load_from_dict(self, data: dict):
        super().load_from_dict(data)
        count = self.static_inputs.get("count", 1)
        for i in range(count):
            self.__input_definitions[f"in[{i}]"] = AnyAttributeDefinition()
        self.refresh_ui()
    
    def __on_count_changed(self, sender: int, app_data: str):
        self.set_static_input("count", int(app_data))
        count = int(app_data)
        self.__input_definitions = {}
        for i in range(count):
            self.__input_definitions[f"in[{i}]"] = AnyAttributeDefinition()
        self.refresh_ui()
    
    def show_custom_ui(self, parent: int | str):
        super().show_custom_ui(parent)
        dpg.add_input_int(
            label="Count", 
            default_value=self.static_inputs.get("count"), 
            callback=self.__on_count_changed, min_value=0, 
            min_clamped=True, 
            max_value=16, 
            max_clamped=True,
            width=DPG_DEFAULT_INPUT_WIDTH
            )
    
    @classmethod
    def name(cls) -> str:
        return "To List"
    
    @classmethod
    def category(cls) -> str:
        return "Convert"
    
    def run(self, **kwargs) -> dict:
        count = self.static_inputs.get("count", 1)
        in_data = [kwargs.get(f"in[{i}]", None) for i in range(count)]
        return {"out": in_data}

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