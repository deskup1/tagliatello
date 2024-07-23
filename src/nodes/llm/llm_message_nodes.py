from ...graph import BaseNode, AttributeKind, AttributeDefinition, FileAttributeDefinition, ComboAttributeDefinition, ComboAttributeDefinition, BoolenAttributeDefinition, ListAttributeDefinition, StringAttributeDefinition
import dearpygui.dearpygui as dpg
from .llm_message import LlmChatMessage

import yaml
import json

class LlmChatMessageNode(BaseNode):
    
    def __init__(self):
        super().__init__()
        self.set_default_input("message", "")
        self.set_default_input("role", "user")
        self.set_default_input("image", "")

    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "message": StringAttributeDefinition(large=True),
            "role": ComboAttributeDefinition(values_callback=lambda: ["user", "assistant", "system"]),
            "image": FileAttributeDefinition(allowed_extensions=[".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp", ".ico"])
        }
    
    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "message": AttributeDefinition(type_name="chat_message")
        }
    
    @classmethod
    def name(cls) -> str:
        return "Llm Chat Message"
    
    @classmethod
    def category(cls) -> str:
        return "LLM"
    
    def run(self, **kwargs) -> dict:
        message = kwargs.get("message")
        role = kwargs.get("role")
        image = kwargs.get("image")
        return {"message": LlmChatMessage(role, message, image)}

class SplitLlmChatMessageNode(BaseNode):
    
    def __init__(self):
        super().__init__()
        self.set_default_input("message", None)

    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "message": AttributeDefinition(type_name="chat_message")
        }
    
    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "role": StringAttributeDefinition(),
            "text": StringAttributeDefinition(),
            "image": StringAttributeDefinition()
        }
    
    @classmethod
    def name(cls) -> str:
        return "Split Llm Chat Message"
    
    @classmethod
    def category(cls) -> str:
        return "LLM"
    
    def run(self, **kwargs) -> dict:
        message = kwargs.get("message")
        return {"role": message.role, "text": message.text, "image": message.image}

class LlmChatMessageFromString(BaseNode):
        
        def __init__(self):
            super().__init__()
            self.set_default_input("message", "")
    
        @property
        def input_definitions(self) -> dict[str, AttributeDefinition]:
            return {
                "message": StringAttributeDefinition(),
                "type": ComboAttributeDefinition(values_callback=lambda: ["yaml", "json", "auto detect"])
            }
        
        @property
        def output_definitions(self) -> dict[str, AttributeDefinition]:
            return {
                "message": AttributeDefinition(type_name="chat_message")
            }
        
        @classmethod
        def name(cls) -> str:
            return "Llm Chat Message from String"
        
        @classmethod
        def category(cls) -> str:
            return "LLM"
        
        def run(self, **kwargs) -> dict:
            message = kwargs.get("message")
            message_type = kwargs.get("type")

            if message_type == "auto detect":
                try:
                    message = yaml.safe_load(message)
                except yaml.YAMLError:
                    try:
                        message = json.loads(message)
                    except json.JSONDecodeError:
                        raise ValueError("Failed to auto detect message type")
                    
            elif message_type == "yaml":
                message = yaml.safe_load(message)
            elif message_type == "json":
                message = json.loads(message)

            role = message.get("role")
            text = message.get("text")
            image = message.get("image")

            return {"message": LlmChatMessage(role, text, image)}


class LlmChatMessagesFromString(BaseNode):
        
    def __init__(self):
        super().__init__()
        self.set_default_input("messages", "")
        self.set_default_input("type", "yaml")

    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "messages": StringAttributeDefinition(),
            "type": ComboAttributeDefinition(values_callback=lambda: ["yaml", "json", "auto detect"])
        }
    
    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "messages": ListAttributeDefinition(AttributeDefinition(type_name="chat_message"))
        }
    
    @classmethod
    def name(cls) -> str:
        return "Llm Chat Messages from String"
    
    @classmethod
    def category(cls) -> str:
        return "LLM"
    
    def run(self, **kwargs) -> dict:
        messages = kwargs.get("messages")
        message_type = kwargs.get("type")

        if message_type == "auto detect":
            try:
                messages = yaml.safe_load(messages)
            except yaml.YAMLError:
                try:
                    messages = json.loads(messages)
                except json.JSONDecodeError:
                    raise ValueError("Failed to auto detect message type")
                
        elif message_type == "yaml":
            messages = yaml.safe_load(messages)
        elif message_type == "json":
            messages = json.loads(messages)

        return {"messages": [LlmChatMessage(message.get("role"), message.get("text"), message.get("image")) for message in messages]}

