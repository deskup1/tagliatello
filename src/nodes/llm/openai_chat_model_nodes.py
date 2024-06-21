from ...graph import BaseNode, AttributeKind, AttributeDefinition, FileAttributeDefinition, ComboAttributeDefinition, MultipleAttributeDefinition, BoolenAttributeDefinition, FloatAttributeDefinition, StringAttributeDefinition
import dearpygui.dearpygui as dpg
from .llm_message import LlmChatMessage
from .openai_chat_model import OpenAIChatModel

class OpenAiChatModelNode(BaseNode):
        
    def __init__(self):
        super().__init__()
        self.set_static_input("base_url", "http://localhost:1234/v1")
        self.set_static_input("api_key", "<DUMMY_KEY>")
        self.set_static_input("timeout", 60.0)
        self.set_static_input("max_retries", 3)
        self.set_static_input("model", "")

    @property
    def static_input_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "base_url": StringAttributeDefinition(),
            "api_key": StringAttributeDefinition(),
            "timeout": FloatAttributeDefinition(),
            "max_retries": FloatAttributeDefinition(),
            "model": ComboAttributeDefinition(values_callback=lambda:self.__get_model().get_models())
        }
    
    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "model": AttributeDefinition(type_name="llm")
        }
    
    @classmethod
    def name(cls) -> str:
        return "OpenAI Chat"
    
    @classmethod
    def category(cls) -> str:
        return "LLM"

    def __get_model(self):
        api_key = self.static_inputs["api_key"]
        base_url = self.static_inputs["base_url"]
        timeout = self.static_inputs["timeout"]
        max_retries = self.static_inputs["max_retries"]
        model = self.static_inputs["model"]
        return OpenAIChatModel(api_key, base_url, timeout, max_retries, model)
    
    def run(self, **kwargs) -> dict:
        return {"model": self.__get_model()}