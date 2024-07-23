

import ollama
import sys

import dearpygui.dearpygui as dpg


if __name__ == "__main__":
    sys.path.append("")
    from src.nodes.llm.llm_message import LlmChatMessage
    from src.helpers import pillow_from_any_string, convert_pil_to_base64
    from src.graph import BaseNode, AttributeDefinition, ComboAttributeDefinition, FloatAttributeDefinition, StringAttributeDefinition
    from src.nodes.llm.llm_message import LlmChatMessage
else:

    from .llm_message import LlmChatMessage
    from ...helpers import pillow_from_any_string, convert_pil_to_base64
    from ...graph import BaseNode, AttributeDefinition, ComboAttributeDefinition, FloatAttributeDefinition, StringAttributeDefinition
    from .llm_message import LlmChatMessage


class OllamaChatModel:
    def __init__(self, api_key, base_url, timeout, model = ""):
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.model = model

    def get_models(self, timeout: int = 3,):
        return [model["name"] for model in ollama.Client(host = self.base_url, timeout = timeout).list()["models"]]
    
    def __llm_message_to_ollama_format(self, message: LlmChatMessage) -> ollama.Message:
        messsage_dict = {
            "role": message.role,
            "content": message.text,
        }

        if message.image:
            messsage_dict["images"] = [ message.base64_image.split(",")[1] ]

        return messsage_dict
    
    def chat(self, 
             messages: list[LlmChatMessage] = [],
             message: LlmChatMessage|None = None,
             temperature: float|None = None,
             top_p: float|None = None,
             max_tokens: int|None = None,
             stop: list[str]|None = None,
             frequency_penalty: float|None = None,
             ) -> LlmChatMessage:
        
        messages = [m for m in messages if m is not None]
        history = [self.__llm_message_to_ollama_format(m) for m in messages]
        if message:
            history.append(self.__llm_message_to_ollama_format(message))

        response = ollama.Client(host = self.base_url, timeout = self.timeout).chat(
            model=self.model,
            messages=history,
            stream=True,
            options=ollama.Options(
                top_p=top_p,
                temperature=temperature,
                max_tokens=max_tokens,
                stop=stop,
                frequency_penalty=frequency_penalty,
            )
        )

        message = ""
        for part in response:
            message += part['message']['content']

        return LlmChatMessage(role="response", text=message, image=None)
    


class OllamaChatModelNode(BaseNode):
        
    def __init__(self):
        super().__init__()
        self.set_static_input("base_url", "http://localhost:11434")
        self.set_static_input("api_key", "<DUMMY_KEY>")
        self.set_static_input("timeout", 60.0)
        self.set_static_input("model", "")

    @property
    def static_input_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "base_url": StringAttributeDefinition(),
            "api_key": StringAttributeDefinition(),
            "timeout": FloatAttributeDefinition(),
            "model": ComboAttributeDefinition(values_callback=lambda:self.__get_model().get_models())
        }
    
    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "model": AttributeDefinition(type_name="llm")
        }
    
    @classmethod
    def name(cls) -> str:
        return "Ollama Chat"
    
    @classmethod
    def category(cls) -> str:
        return "LLM"

    def __get_model(self):
        api_key = self.static_inputs["api_key"]
        base_url = self.static_inputs["base_url"]
        timeout = self.static_inputs["timeout"]
        model = self.static_inputs["model"]
        return OllamaChatModel(api_key, base_url, timeout, model)
    
    def run(self, **kwargs) -> dict:
        return {"model": self.__get_model()}


if __name__ == "__main__":
    model = OllamaChatModel("api_key", "localhost:11434", 30, model="llama3")
    model.chat(message=LlmChatMessage("user", "Hello!"), messages=[], temperature=0.5, top_p=0.9, max_tokens=50, stop=[], frequency_penalty=0.0)
