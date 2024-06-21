from .llm_message_nodes import LlmChatMessageNode, SplitLlmChatMessageNode
from .llm_chat_nodes import InferenceLlmNode
from .openai_chat_model_nodes import OpenAiChatModelNode

def register_nodes():
    return [
        LlmChatMessageNode,
        SplitLlmChatMessageNode,
        InferenceLlmNode,
        OpenAiChatModelNode
    ]