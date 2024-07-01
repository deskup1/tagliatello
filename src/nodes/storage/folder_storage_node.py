
from typing import Any
import os
from ...graph import BaseNode, StringAttributeDefinition, AttributeDefinition, ComboAttributeDefinition


class FolderStorage:

    def __init__(self, path, extension=".txt"):
        self.path = path
        self.extension = extension

        if self.extension is None:
            self.extension = ""
        elif self.extension != "" and not self.extension.startswith("."):
            self.extension = f".{self.extension}"

    def __setattr__(self, name: str, value: Any) -> None:
        try:
            os.makedirs(self.path, exist_ok=True)
            with open(f"{self.path}/{name}{self.extension}", "w") as f:
                f.write(str(value))
        except Exception as e:
            raise ValueError(f"Failed to save value to file: {e}")

    def __getattr__(self, name: str) -> Any:
        # check if file exists
        if not os.path.exists(f"{self.path}/{name}{self.extension}"):
            return None

        # read value from file
        try:
            with open(f"{self.path}/{name}{self.extension}", "r") as f:
                return f.read()
        except FileNotFoundError:
            return None
        except Exception as e:
            raise ValueError(f"Failed to read value from file: {e}")
        

class FolderStorageNode(BaseNode):
    
    def __init__(self):
        super().__init__()
        self.set_static_input("path", "")
        self.set_static_input("extension", "txt")
        self.storage = None

    @classmethod
    def name(cls):
        return "Folder Storage Node"
    
    @classmethod
    def category(cls):
        return "Storage"
    
    @property
    def static_input_definitions(self):
        return {
            "path": StringAttributeDefinition(),
            "extension": StringAttributeDefinition()
        }
    
    @property
    def output_definitions(self):
        return {
            "storage": AttributeDefinition(type_name="storage")
        }
    
    def init(self):
        path = self.static_inputs["path"]
        extension = self.static_inputs["extension"]
        self.storage = FolderStorage(path, extension)
        return super().init()
    
    def run(self, **kwargs):
        return {
            "storage": self.storage
        }
    
    