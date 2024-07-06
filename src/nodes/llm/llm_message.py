import os
from PIL import Image
import base64
from io import BytesIO
import re
from ...helpers import convert_base64_to_pil

class LlmChatMessage:
    def __init__(self, role: str, text: str, image: str|Image.Image|None = None):
        self.role: str = role
        self.text: str = text
        self.image: str|Image.Image|None= image

    @property
    def base64_image(self) -> str|None:
        self.__convert_image_to_base64(self.image)

    @property
    def pil_image(self) -> Image.Image|None:
        self.__convert_to_pil_image(self.image)

    def __convert_to_pil_image(self, image: str|Image.Image) -> Image.Image | None:
        if image is None or image == "":
            return None
        elif isinstance(image, str):
            if image.startswith("data:image"):
                return convert_base64_to_pil(image)
            elif not os.path.exists(image):
                raise ValueError(f"Image '{image}' does not exist")
            return Image.open(image)
        elif isinstance(image, Image.Image):
            return image
        else:
            raise ValueError(f"Invalid image type '{type(image)}'")

    def __convert_image_to_base64(self, image: str|Image.Image) -> str|None:
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
