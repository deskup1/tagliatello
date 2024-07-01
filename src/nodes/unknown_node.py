from ..graph import BaseNode


class UnknownNode(BaseNode):
    def __init__(self):
        self.__name = "Unknown Node"
        super().__init__()

    @classmethod
    def name(cls) -> str:
        return "Unknown Node"
    
    @classmethod
    def category(cls) -> str:
        return "Internal"

    def load_from_dict(self, data: dict):
        self.__name = data.get("type", "")
        return super().load_from_dict(data)

    def show_custom_ui(self, parent):
        self._on_error.trigger(f"Unknown node type: {self.__name}")
        pass
    
    def run(self, **kwargs) -> dict:
        raise NotImplementedError("Node not implemented")