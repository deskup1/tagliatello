from ...graph import BaseNode, AttributeDefinition, FileAttributeDefinition, MultiFileAttributeDefinition, FloatAttributeDefinition, ComboAttributeDefinition, StringAttributeDefinition
import os
from PIL import Image

class SaveToTextFileNode(BaseNode):
    def __init__(self):
        super().__init__()

    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {"text": StringAttributeDefinition(), "path": FileAttributeDefinition()}

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
        with open(path, "w") as f:
            f.write(text)
        return {}

class SaveToTextFilesNode(BaseNode):
    def __init__(self):
        super().__init__()

    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {"texts": StringAttributeDefinition(list=True), "paths": MultiFileAttributeDefinition()}

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

        if len(texts) != len(paths):
            raise ValueError("Texts and paths lists must have the same length")

        for i in range(len(texts)):
            with open(paths[i], "w") as f:
                f.write(texts[i])
        return {"paths": paths}
   

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
    
class MoveFilesNode(BaseNode):
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
            os.rename(source[i], destination[i])
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

class CopyFilesNode(BaseNode):
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

        if len(source) != len(destination):
            raise ValueError("Source and destination lists must have the same length")

        for i in range(len(source)):
            with open(source[i], "rb") as f:
                data = f.read()
            with open(destination[i], "wb") as f:
                f.write(data)