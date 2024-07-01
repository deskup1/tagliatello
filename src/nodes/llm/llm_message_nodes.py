from ...graph import BaseNode, AttributeKind, AttributeDefinition, FileAttributeDefinition, ComboAttributeDefinition, MultipleAttributeDefinition, BoolenAttributeDefinition, FloatAttributeDefinition, StringAttributeDefinition
import dearpygui.dearpygui as dpg
from .llm_message import LlmChatMessage

class LlmChatMessageNode(BaseNode):
    
    def __init__(self):
        super().__init__()
        self.set_default_input("message", "")
        self.set_default_input("role", "user")
        self.set_default_input("image", "")

    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "message": StringAttributeDefinition(),
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