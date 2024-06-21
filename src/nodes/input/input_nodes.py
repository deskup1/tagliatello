from ...graph import (
    BaseNode, 
    AttributeDefinition, 
    IntegerAttributeDefinition, 
    FloatAttributeDefinition,
    StringAttributeDefinition,
    FileAttributeDefinition,
    MultiFileAttributeDefinition,
    BoolenAttributeDefinition
)

import os
import cv2
import base64

class IntegerNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.set_default_output("out", 0)
    
    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return {"out": IntegerAttributeDefinition()}
    
    @classmethod
    def name(cls) -> str:
        return "Input Integer"
    
    @classmethod
    def category(cls) -> str:
        return "Input"

    def run(self, **kwargs) -> dict:
        return {"out": int(self.default_outputs.get("out", 0))}
    
class FloatNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.set_default_output("out", 0.0)
    
    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return {"out": FloatAttributeDefinition()}
    
    @classmethod
    def name(cls) -> str:
        return "Input Float"
    
    @classmethod
    def category(cls) -> str:
        return "Input"

    def run(self, **kwargs) -> dict:
        return {"out": float(self.default_outputs.get("out", 0.0))}
    
class StringNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.set_default_output("out", "")

    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return {"out": StringAttributeDefinition()}
    
    @classmethod
    def name(cls) -> str:
        return "Input String"
    
    @classmethod
    def category(cls) -> str:
        return "Input"

    def run(self, **kwargs) -> dict:
        return {"out": str(self.default_outputs.get("out", ""))}
    
class StringListNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.set_default_output("out", [])
    
    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return {"out": StringAttributeDefinition(list=True)}
    
    @classmethod
    def name(cls) -> str:
        return "Input String List"
    
    @classmethod
    def category(cls) -> str:
        return "Input"

    def run(self, **kwargs) -> dict:
        return {"out": self.default_outputs.get("out", [])}

class BoolenNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.set_default_output("out", False)
    
    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return {"out": BoolenAttributeDefinition()}
    
    @classmethod
    def name(cls) -> str:
        return "Input Boolean"
    
    @classmethod
    def category(cls) -> str:
        return "Input"

    def run(self, **kwargs) -> dict:
        return {"out": bool(self.default_outputs.get("out", False))}    

class FileNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.set_default_output("path", "")
    
    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return {"path": FileAttributeDefinition()}
    
    @classmethod
    def name(cls) -> str:
        return "Input File"
    
    @classmethod
    def category(cls) -> str:
        return "Input"
    
    @classmethod
    def create(cls, **kwargs):
        return FileNode()

    def run(self, **kwargs) -> dict:
        return {"path": self.default_outputs.get("path", "")}
    
class MultiFileNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.set_default_output("paths", [])
    
    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return {"paths": MultiFileAttributeDefinition()}
    
    @classmethod
    def name(cls) -> str:
        return "Input Files"
    
    @classmethod
    def category(cls) -> str:
        return "Input"
    
    @classmethod
    def create(cls, **kwargs):
        return MultiFileNode()

    def run(self, **kwargs) -> dict:
        return {"paths": self.default_outputs.get("paths", [])}

    
class CounterNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.default_inputs = {"start": 0, "step": 1}
        self.counter = None
    
    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {"start": IntegerAttributeDefinition(),
                "step": IntegerAttributeDefinition()}
    
    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return {"out": IntegerAttributeDefinition()}
    
    @property
    def cache(self) -> bool:
        return False

    @classmethod
    def name(cls) -> str:
        return "Counter"
    
    @classmethod
    def category(cls) -> str:
        return "Input"
    
    def init(self):
        self.counter = None

    def run(self, **kwargs) -> dict:

        if self.counter is None:
            self.counter = kwargs["start"]
            return {"out": self.counter}

        step = kwargs["step"]
        self.counter += step

        return {"out": self.counter}
    
class RangeNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.default_inputs = {"start": 0, "stop": 10, "step": 1}
        self.range = None
    
    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {"start": IntegerAttributeDefinition(),
                "stop": IntegerAttributeDefinition(),
                "step": IntegerAttributeDefinition()}
    
    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return {"out": IntegerAttributeDefinition(list=True)}
    

    @classmethod
    def name(cls) -> str:
        return "Range"
    
    @classmethod
    def category(cls) -> str:
        return "Input"
    
    def initialize(self):
        self.range = None

    def run(self, **kwargs) -> dict:

        if self.range is None:
            self.range = list(range(kwargs["start"], kwargs["stop"], kwargs["step"]))
            return {"out": self.range}

        return {"out": self.range}
    
class FilePathNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.set_default_input("folder", "")
        self.set_default_input("base_name", "")
        self.set_default_input("extension", "")

        self.file_path = None
    
    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {"folder": FileAttributeDefinition(directory_selector=True),
                "base_name": StringAttributeDefinition(),
                "extension": StringAttributeDefinition()}
    
    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return {"path": FileAttributeDefinition()}
    
    @classmethod
    def name(cls) -> str:
        return "File Path"
    
    @classmethod
    def category(cls) -> str:
        return "Input"
    
    def run(self, **kwargs) -> dict[str, object]:
        folder = kwargs["folder"]
        base_name = kwargs["base_name"]
        extension = kwargs["extension"]

        self.file_path = os.path.join(folder, f"{base_name}.{extension}")

        return {"path": self.file_path}
    
class SplitFilePathNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.set_default_input("path", "")
    
    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {"path": FileAttributeDefinition()}
    
    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "folder": FileAttributeDefinition(directory_selector=True),
            "base_name": StringAttributeDefinition(),
            "extension": StringAttributeDefinition()
        }
    
    @classmethod
    def name(cls) -> str:
        return "Split File Path"
    
    @classmethod
    def category(cls) -> str:
        return "Input"
    
    def run(self, **kwargs) -> dict[str, object]:
        path = kwargs["path"]
        folder, file_name = os.path.split(path)
        base_name, extension = os.path.splitext(file_name)

        return {
            "folder": folder,
            "base_name": base_name,
            "extension": extension
        }
    
class Base64ImageNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.set_default_input("path", "")
        self.set_default_input("max_width", 512)
        self.set_default_input("max_height", 512)
    
    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "path": FileAttributeDefinition(allowed_extensions=["Images (*.png *.jpg *.jpeg *.bmp *.tiff *.webp *.ico){.png,.jpg,.jpeg,.bmp,.tiff,.webp,.ico}", ".*"]),
            "max_width": IntegerAttributeDefinition(min_value=1),
            "max_height": IntegerAttributeDefinition(min_value=1)
            }
    
    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return {"image": StringAttributeDefinition()}
    
    @classmethod
    def name(cls) -> str:
        return "Base64 Image"
    
    @classmethod
    def category(cls) -> str:
        return "Input"
    
    
    def run(self, **kwargs) -> dict:
        
        # load image
        path = kwargs["path"]
        max_width = kwargs["max_width"]
        max_height = kwargs["max_height"]

        if not os.path.exists(path):
            raise ValueError(f"File {path} does not exist")
        
        image = cv2.imread(path)
        if image is None:
            raise ValueError(f"Failed to load image {path}")
        
        # resize image
        height, width = image.shape[:2]
        if height > max_height or width > max_width:
            scale = min(max_width / width, max_height / height)
            image = cv2.resize(image, (0, 0), fx=scale, fy=scale)

        # encode image to base64
        _, buffer = cv2.imencode(".png", image)
        image_base64 = base64.b64encode(buffer).decode("utf-8")

        image_base64 = f"data:image/png;base64,{image_base64}"
        return {"image": image_base64}

