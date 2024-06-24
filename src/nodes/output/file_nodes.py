from ...graph import BaseNode, AttributeDefinition, FileAttributeDefinition, MultiFileAttributeDefinition, FloatAttributeDefinition, ComboAttributeDefinition, StringAttributeDefinition
import os
from PIL import Image

from ..progress_node import ProgressNode

class SaveToTextFileNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.set_default_input("mode", "overwrite")

    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "text": StringAttributeDefinition(), 
            "path": FileAttributeDefinition(),
            "mode": ComboAttributeDefinition(values_callback=lambda: ["overwrite", "append", "error if exists","skip if exists"])
            }

    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return { "path" : FileAttributeDefinition() }

    @classmethod
    def name(cls) -> str:
        return "Save to Text File"

    @classmethod
    def category(cls) -> str:
        return "File"

    def run(self, **kwargs) -> dict:
        text = kwargs["text"]
        path = kwargs["path"]
        mode = kwargs.get("mode", "overwrite")

        if mode == "error if exists" and os.path.exists(path):
            raise ValueError("File already exists")
        
        if mode == "skip if exists" and os.path.exists(path):
            return {"path": path}
        
        if mode == "append" and os.path.exists(path):
            with open(path, "a") as f:
                f.write(text)
        else:
            with open(path, "w") as f:
                f.write(text)
        return {"path": path}

class SaveToTextFilesNode(ProgressNode):
    def __init__(self):
        super().__init__()
        self.set_default_input("mode", "overwrite")

    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "texts": StringAttributeDefinition(list=True), 
            "paths": MultiFileAttributeDefinition(),
            "mode": ComboAttributeDefinition(values_callback=lambda: ["overwrite", "append", "error if exists","skip if exists"])
            }

    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return { "paths" : MultiFileAttributeDefinition() }

    @classmethod
    def name(cls) -> str:
        return "Save to Text Files"

    @classmethod
    def category(cls) -> str:
        return "File"

    def run(self, **kwargs) -> dict:
        texts = kwargs["texts"]
        paths = kwargs["paths"]
        mode = kwargs.get("mode", "overwrite")

        if len(texts) != len(paths):
            raise ValueError("Texts and paths lists must have the same length")

        remaining_paths = []

        for i in range(len(texts)):

            self.set_progress(i, len(texts))

            if mode == "error if exists" and os.path.exists(paths[i]):
                raise ValueError("File already exists")
            elif mode == "skip if exists" and os.path.exists(paths[i]):
                continue
            elif mode == "append" and os.path.exists(paths[i]):
                with open(paths[i], "a") as f:
                    f.write(texts[i])
            else:
                with open(paths[i], "w") as f:
                    f.write(texts[i])
            remaining_paths.append(paths[i])

        self.set_progress(len(texts), len(texts))
        return {"paths": remaining_paths}
   

class SaveToImageFileNode(BaseNode):
    def __init__(self):
        super().__init__()

    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {"image": AttributeDefinition(type_name="image"), "path": FileAttributeDefinition()}

    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return { "path" : FileAttributeDefinition() }

    @classmethod
    def name(cls) -> str:
        return "Save to Image File"

    @classmethod
    def category(cls) -> str:
        return "File"

    def run(self, **kwargs) -> dict:
        image = kwargs.get("image")
        if image is None or not isinstance(image, Image.Image):
            raise ValueError("Input is not an image")
        path = kwargs.get("path")
        if path is None:
            raise ValueError("Path is not provided")
        
        image.save(path)

class MoveFileNode(BaseNode):
    def __init__(self):
        super().__init__()

    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {"source": FileAttributeDefinition(), "destination": FileAttributeDefinition()}

    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return { "destination" : FileAttributeDefinition() }

    @classmethod
    def name(cls) -> str:
        return "Move File"

    @classmethod
    def category(cls) -> str:
        return "File"

    def run(self, **kwargs) -> dict:
        source = kwargs["source"]
        destination = kwargs["destination"]
        os.rename(source, destination)
        return {"destination": destination}
    
class MoveFilesNode(ProgressNode):
    def __init__(self):
        super().__init__()

    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {"source": MultiFileAttributeDefinition(), "destination": MultiFileAttributeDefinition()}

    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return { "destination" : MultiFileAttributeDefinition() }

    @classmethod
    def name(cls) -> str:
        return "Move Files"

    @classmethod
    def category(cls) -> str:
        return "File"


    def run(self, **kwargs) -> dict:
        source = kwargs["source"]
        destination = kwargs["destination"]

        if len(source) != len(destination):
            raise ValueError("Source and destination lists must have the same length")

        for i in range(len(source)):
            self.set_progress(0, len(source))
            os.rename(source[i], destination[i])

        self.set_progress(len(source), len(source))

        return {"destination": destination}
    
class CopyFileNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.set_default_input("source", [])
        self.set_default_input("destination", [])

    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {"source": FileAttributeDefinition(), "destination": FileAttributeDefinition()}

    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return { "destination" : FileAttributeDefinition() }

    @classmethod
    def name(cls) -> str:
        return "Copy File"

    @classmethod
    def category(cls) -> str:
        return "File"

    def run(self, **kwargs) -> dict:
        source = kwargs["source"]
        destination = kwargs["destination"]
        with open(source, "rb") as f:
            data = f.read()
        with open(destination, "wb") as f:
            f.write(data)
        return {"destination": destination}

class CopyFilesNode(ProgressNode):
    def __init__(self):
        super().__init__()

    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {"source": MultiFileAttributeDefinition(), "destination": MultiFileAttributeDefinition()}

    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return { "destination" : MultiFileAttributeDefinition() }

    @classmethod
    def name(cls) -> str:
        return "Copy Files"

    @classmethod
    def category(cls) -> str:
        return "File"
    

    def run(self, **kwargs) -> dict:
        source = kwargs["source"]
        destination = kwargs["destination"]

        files = []

        if len(source) != len(destination):
            raise ValueError("Source and destination lists must have the same length")

        for i in range(len(source)):
            self.set_progress(0, len(source))
            with open(source[i], "rb") as f:
                data = f.read()
            with open(destination[i], "wb") as f:
                f.write(data)

            files.append(destination[i])

        self.set_progress(len(source), len(source))

        return {"destination": files}

