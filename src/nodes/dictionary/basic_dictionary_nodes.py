from ...graph import BaseNode, AttributeDefinition, AnyAttributeDefinition, DictAttributeDefinition, ComboAttributeDefinition, StringAttributeDefinition

from PIL.Image import Image
import time
import os


class DictionaryValueNode(BaseNode):
    def __init__(self):
        super().__init__()

    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "dictionary": DictAttributeDefinition(AnyAttributeDefinition(), AnyAttributeDefinition()),
            "key": AnyAttributeDefinition(),
            "default": AnyAttributeDefinition(),
        }

    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "value": AnyAttributeDefinition(),
        }

    @classmethod
    def name(cls) -> str:
        return "Get Dict Value"

    @classmethod
    def category(cls) -> str:
        return "Dictionary"

    def init(self):
        pass

    def run(self, **kwargs) -> dict[str, object]:
        dictionary = kwargs.get("dictionary")
        key = kwargs.get("key")
        if dictionary is None or key is None:
            return {"value": kwargs.get("default")}

        return {"value": dictionary.get(key, kwargs.get("default"))}
    

class JoinDictionaryNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.set_static_input("join_type", "full join")
        self.set_static_input("value_behavior", "pick second")

    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "dictionary1": DictAttributeDefinition(AnyAttributeDefinition(), AnyAttributeDefinition()),
            "dictionary2": DictAttributeDefinition(AnyAttributeDefinition(), AnyAttributeDefinition()),
        }
    
    @property
    def static_input_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "join_type": ComboAttributeDefinition(values_callback= lambda: ["left join", "right join", "inner join", "full join"], allow_custom=False),
            "value_behavior": ComboAttributeDefinition(values_callback= lambda: ["pick first", "pick second", "average", "sum", "subtract", "multiply", "divide"], allow_custom=False),
        }

    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "dictionary": DictAttributeDefinition(AnyAttributeDefinition(), AnyAttributeDefinition()),
        }
    
    @classmethod
    def name(cls) -> str:
        return "Join Dicts"
    
    @classmethod
    def category(cls) -> str:
        return "Dictionary"
    
    def init(self):
        pass

    def run(self, **kwargs) -> dict[str, object]:
        dictionary1 = kwargs.get("dictionary1")
        dictionary2 = kwargs.get("dictionary2")

        if dictionary1 is None and dictionary2 is None:
            return {"dictionary": {}}
        elif dictionary1 is None:
            return {"dictionary": dictionary2}
        elif dictionary2 is None:
            return {"dictionary": dictionary1}

        join_type = self.static_inputs["join_type"]
        value_behavior = self.static_inputs["value_behavior"]
        
        def get_value(first, second):
            if value_behavior == "pick first":
                return first
            elif value_behavior == "pick second":
                return second
            elif value_behavior == "average":
                return (first + second) / 2
            elif value_behavior == "sum":
                return first + second
            elif value_behavior == "subtract":
                return first - second
            elif value_behavior == "multiply":
                return first * second
            elif value_behavior == "divide":
                return first / second if second != 0 else 0
            else:
                return second
            
        if join_type == "left join":
            return {"dictionary": {key: get_value(value, dictionary2.get(key)) for key, value in dictionary1.items()}}
        elif join_type == "right join":
            return {"dictionary": {key: get_value(dictionary1.get(key), value) for key, value in dictionary2.items()}}
        elif join_type == "inner join":
            return {"dictionary": {key: get_value(value, dictionary2[key]) for key, value in dictionary1.items() if key in dictionary2}}
        elif join_type == "full join":
            all_keys = set(dictionary1.keys()) | set(dictionary2.keys())
            return {"dictionary": {key: get_value(dictionary1.get(key), dictionary2.get(key)) for key in all_keys}}
        else:
            return {"dictionary": {}}
        
class FilterDictionarByValueNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.set_static_input("filter_type", "equal")
        self.set_static_input("value", 0)

    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "dictionary": DictAttributeDefinition(AnyAttributeDefinition(), AnyAttributeDefinition()),
            "value": AnyAttributeDefinition(),
        }
    
    @property
    def static_input_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "filter_type": ComboAttributeDefinition(values_callback=lambda: ["equal", "not equal", "greater", "greater or equal", "less", "less or equal"], allow_custom=False),
        }

    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "dictionary": DictAttributeDefinition(AnyAttributeDefinition(), AnyAttributeDefinition()),
        }
    
    @classmethod
    def name(cls) -> str:
        return "Filter Dict By Value"
    
    @classmethod
    def category(cls) -> str:
        return "Dictionary"
    
    def init(self):
        pass

    def run(self, **kwargs) -> dict[str, object]:
        dictionary: dict = kwargs.get("dictionary")
        if dictionary is None:
            return {"dictionary": {}}

        filter_type = self.static_inputs["filter_type"]
        value = kwargs.get("value")
        
        if filter_type == "equal":
            return {"dictionary": {key: value for key, val in dictionary.items() if val == value}}
        elif filter_type == "not equal":
            return {"dictionary": {key: val for key, val in dictionary.items() if val != value}}
        elif filter_type == "greater":
            return {"dictionary": {key: val for key, val in dictionary.items() if val > value}}
        elif filter_type == "greater or equal":
            return {"dictionary": {key: val for key, val in dictionary.items() if val >= value}}
        elif filter_type == "less":
            return {"dictionary": {key: val for key, val in dictionary.items() if val < value}}
        elif filter_type == "less or equal":
            return {"dictionary": {key: val for key, val in dictionary.items() if val <= value}}
        else:
            return {"dictionary": {}}
        
class DictionaryItemsNode(BaseNode):
    def __init__(self):
        super().__init__()

    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "dictionary": DictAttributeDefinition(AnyAttributeDefinition(), AnyAttributeDefinition()),
        }

    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "items": DictAttributeDefinition(AnyAttributeDefinition(), AnyAttributeDefinition()),
        }

    @classmethod
    def name(cls) -> str:
        return "Dictionary Items"

    @classmethod
    def category(cls) -> str:
        return "Dictionary"

    def init(self):
        pass

    def run(self, **kwargs) -> dict[str, object]:
        dictionary = kwargs.get("dictionary")
        if dictionary is None:
            return {"items": {}}

        return {"items": dictionary.items()}