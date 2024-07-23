from .llm_message_nodes import LlmChatMessageNode, SplitLlmChatMessageNode, LlmChatMessageFromString, LlmChatMessagesFromString
from .llm_chat_nodes import InferenceLlmNode
from .openai_chat_model_nodes import OpenAiChatModelNode
from .ollama_chat_model_nodes import OllamaChatModelNode

def register_nodes():
    return [
        LlmChatMessageNode,
        LlmChatMessageFromString,
        LlmChatMessagesFromString,
        SplitLlmChatMessageNode,
        InferenceLlmNode,
        OpenAiChatModelNode,
        OllamaChatModelNode
    ]