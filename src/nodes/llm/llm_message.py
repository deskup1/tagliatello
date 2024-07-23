import os
from PIL import Image
import base64
from io import BytesIO
import re
from ...helpers import convert_base64_to_pil, convert_pil_to_base64, pillow_from_any_string

class LlmChatMessage:
    def __init__(self, role: str, text: str, image: str|Image.Image|None = None):
        self.role: str = role
        self.text: str = text
        self.image: str|Image.Image|None= image

    @property
    def base64_image(self) -> str|None:
        image = self.image
        if isinstance(self.image, str):
            if self.image.startswith("data:image"):
                return self.image
            image = pillow_from_any_string(self.image)
        if image:
            return convert_pil_to_base64(image)

    @property
    def pil_image(self) -> Image.Image|None:
        return pillow_from_any_string(self.image)
        
    def __str__(self) -> str:
        return f"{self.role}: {self.text}"
    
    def __repr__(self) -> str:
      return f"{self.role}: {self.text}"  