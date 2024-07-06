from ...graph import BaseNode, AttributeDefinition, ComboAttributeDefinition, FloatAttributeDefinition, StringAttributeDefinition
import dearpygui.dearpygui as dpg
from .llm_message import LlmChatMessage

from openai import OpenAI

from .llm_message import LlmChatMessage

class OpenAIChatModel:
    def __init__(self, api_key, base_url, timeout, max_retries, model = ""):
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.model = model
        client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout,
            max_retries=max_retries,
        )

        self.client = client

    def get_models(self, timeout: int = 3,):
        return [model.id for model in self.client.models.list(timeout=timeout)]

    def __llm_message_to_openai_format(self, message: LlmChatMessage) -> dict:
        messsage_dict = {
            "role": message.role,
            "content": [
                {
                    "type": "text",
                    "text": message.text,
                }
            ],
        }
        if message.image:
            messsage_dict["content"].append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": message.image,
                    }
                }
            )
        return messsage_dict

    def chat(self, 
             messages: list[LlmChatMessage], 
             message: LlmChatMessage|None,
             temperature: float,
             top_p: float,
             max_tokens: int,
             stop: list[str],
             frequency_penalty: float,

             ) -> LlmChatMessage:
        messages = [m for m in messages if m is not None]
        history = [self.__llm_message_to_openai_format(m) for m in messages]
        if message:
            history.append(self.__llm_message_to_openai_format(message))


        if temperature < 0:
            temperature = None
        if top_p < 0:
            top_p = None
        if max_tokens < 0:
            max_tokens = None
        if frequency_penalty < 0:
            frequency_penalty = None
            

        response = self.client.chat.completions.create(
            model=self.model,
            messages=history,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            stop=stop,
            frequency_penalty=frequency_penalty,
            stream=True,
        )

        response_message = ""
        for chunk in response:
            content = chunk.choices[0].delta.content
            if content == None:
                content = " "
            response_message += content

        print(response_message)

        return LlmChatMessage(
            role="assistant",
            text=response_message
        )


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