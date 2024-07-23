
from typing import Any
import os
from ...graph import BaseNode, StringAttributeDefinition, AttributeDefinition, FileAttributeDefinition


class FolderStorage:

    def __init__(self, storage_path, extension=".txt"):
        self.extension = extension
        self.storage_path = storage_path

        if extension!= None and len(extension) > 0 and extension[0] != ".":
            self.extension = f".{extension}"

    def get(self, name: str) -> Any:
        return self.__getitem__(name)
    
    def set(self, name: str, value: Any) -> None:
        self.__setitem__(name, value)

    def all_keys(self):
        listdir = os.listdir(self.storage_path)
        keys = []
        for file in listdir:
            if file.endswith(self.extension):
                key = file.replace(self.extension, "")
                key = key.encode("utf-8","ignore").decode("ascii")
                key = key.replace("\\", "")
                key = key.replace("/", "")
                key = key.replace(":", "[colon]")
                key = key.replace("*", "[star]")
                key = key.replace("?", "[question]")
                keys.append(key)

        return keys

        
    def __setitem__(self, name: str, value: Any) -> None:
        try:
            os.makedirs(self.storage_path, exist_ok=True)

            name = name.encode("ascii","ignore").decode("utf-8")
            name = name.replace("\\", "")
            name = name.replace("/", "")
            name = name.replace(":", "[colon]")
            name = name.replace("*", "[star]")
            name = name.replace("?", "[question]")

            with open(f"{self.storage_path}/{name}{self.extension}", "w") as f:
                f.write(str(value))
        except Exception as e:
            raise ValueError(f"Failed to save value to file: {e}")

    def __getitem__(self, name: str) -> Any:


        name=name.encode("ascii","ignore").decode("utf-8")
        name = name.replace("\\", "")
        name = name.replace("/", "")

        # check if file exists
        if not os.path.exists(f"{self.storage_path}/{name}{self.extension}"):
            return None

        # read value from file
        try:
            with open(f"{self.storage_path}/{name}{self.extension}", "r") as f:
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
            "path": FileAttributeDefinition(directory_selector=True),
            "extension": StringAttributeDefinition()
        }
    
    @property
    def output_definitions(self):
        return {
            "storage": AttributeDefinition(type_name="storage")
        }
    
    def init(self):
        super().init()
        path = self.static_inputs["path"]
        extension = self.static_inputs["extension"]
        self.storage = FolderStorage(path, extension)
    
    def run(self, **kwargs):
        return {
            "storage": self.storage
        }
    
    