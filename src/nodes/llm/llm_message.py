import os
from PIL.Image import Image
import base64
from io import BytesIO

class LlmChatMessage:
    def __init__(self, role: str, text: str, image: str|Image|None = None):
        self.role: str = role
        self.text: str = text
        self.image: str| None = self.__convert_image_to_base64(image)

    def __convert_image_to_base64(self, image: str|Image) -> str|None:
        if image is None or image == "":
            return None
        elif isinstance(image, str):
            if image.startswith("data:image"):
                return image
            elif not os.path.exists(image):
                raise ValueError(f"Image '{image}' does not exist")
            with open(image, "rb") as f:
                return base64.b64encode(f.read()).decode()
        elif isinstance(image, Image):
            with BytesIO() as buffer:
                image.save(buffer, format="PNG")
                return base64.b64encode(buffer.getvalue()).decode()
        else:
            raise ValueError(f"Invalid image type '{type(image)}'")
        
    def __str__(self) -> str:
        return f"{self.role}: {self.text}"
