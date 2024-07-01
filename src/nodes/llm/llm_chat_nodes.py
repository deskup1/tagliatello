from ...graph import BaseNode, ListAttributeDefinition, AttributeDefinition, IntegerAttributeDefinition, ComboAttributeDefinition, MultipleAttributeDefinition, BoolenAttributeDefinition, FloatAttributeDefinition, StringAttributeDefinition
import dearpygui.dearpygui as dpg
from .llm_message import LlmChatMessage
from .openai_chat_model import OpenAIChatModel

class InferenceLlmNode(BaseNode):
            
        def __init__(self):
            super().__init__()
            self.set_default_input("messages", [])
            self.set_default_input("message", None)
            self.set_default_input("temperature", -1.0)
            self.set_default_input("top_p", -1.0)
            self.set_default_input("max_tokens", -1)
            self.set_default_input("stop", [])
            self.set_default_input("frequency_penalty", -1.0)
    
        @property
        def input_definitions(self) -> dict[str, AttributeDefinition]:
            return {
                "model": AttributeDefinition(type_name="llm"),
                "messages": ListAttributeDefinition(AttributeDefinition(type_name="chat_message")),
                "message": AttributeDefinition(type_name="chat_message"),
                "temperature": FloatAttributeDefinition(min_value=-1.0),
                "top_p": FloatAttributeDefinition(min_value=-1.0),
                "max_tokens": IntegerAttributeDefinition(min_value=-1),
                "stop": ListAttributeDefinition(StringAttributeDefinition()),
                "frequency_penalty": FloatAttributeDefinition()
            }
        
        @property
        def output_definitions(self) -> dict[str, AttributeDefinition]:
            return {
                "message": AttributeDefinition(type_name="chat_message")
            }
        
        @classmethod
        def name(cls) -> str:
            return "Inference LLM"
        
        @classmethod
        def category(cls) -> str:
            return "LLM"
        
        def run(self, **kwargs) -> dict:
            model = kwargs.get("model")
            messages = kwargs.get("messages")
            message = kwargs.get("message")
            temperature = kwargs.get("temperature")
            top_p = kwargs.get("top_p")
            max_tokens = kwargs.get("max_tokens")
            stop = kwargs.get("stop")
            frequency_penalty = kwargs.get("frequency_penalty")
            return {"message": model.chat(messages, message, temperature, top_p, max_tokens, stop, frequency_penalty)}