from src.graph.node import BaseNode, StringAttributeDefinition

class ExampleCustomNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.set_default_input("input", "Hello World")

    @classmethod
    def name(cls):
        return "Example Custom Node"
    
    @classmethod
    def category(cls):
        return "Example Category"
    
    @property
    def input_definitions(self):
        return {
            "input": StringAttributeDefinition()
        }
    
    @property
    def output_definitions(self):
        return {
            "output": StringAttributeDefinition()
        }

    def run(self, **kwargs):
        return {
            "output": kwargs["input"]
        }

    def help(self):
        return "This is an example custom node that takes a string input and returns the same string as output."