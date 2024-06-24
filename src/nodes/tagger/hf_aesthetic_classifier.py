import os
from transformers import pipeline, AutoModelForImageClassification
import huggingface_hub
import typing

from ...settings import SETTINGS

class HfPipelineAestheticClassifier:
    def __init__(self, 
                 model_name: str = "cafeai/cafe_aesthetic", 
                 device = "cpu", 
                 labels = ["aesthetic"], 
                 batch_size = 1,
                 cache_dir = SETTINGS.get("hf_cache_dir")
                 ):
        super().__init__()
        self.model_name = model_name
        self.labels = labels
        self.batch_size = batch_size
        self.device_name = device
        self.cache_dir = cache_dir
        self.model = AutoModelForImageClassification.from_pretrained(model_name, cache_dir=cache_dir)
        self.pipeline = pipeline("image-classification", model=model_name, device = device)
    
    def unload_model(self):
        self.pipeline = None
        self.model = None

    def device(self):
        device = self.pipeline.device
        if device == -1:
            return "cpu"
        else:
            return f"gpu:{device}"

    def tags(self,  images: list[str]) -> typing.Generator[dict[str, float], None, None]:
        # split images into batches
        batch_images = []
        for i in range(0, len(images), self.batch_size):
            batch_images.append(images[i:i + self.batch_size])
            
        for batch in batch_images:
            outputs = self.pipeline(batch)

            for output in outputs:
                result = {}

                for items in output:
                    key = items["label"]
                    value = float(items["score"])
                    result[key] = value

                yield result

        return