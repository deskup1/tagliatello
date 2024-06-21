import os
import onnxruntime as rt
import numpy as np
import cv2
import PIL.Image as pilimg
from huggingface_hub import hf_hub_download

import typing

def _predict(model: rt.InferenceSession, img: np.ndarray):
    img = img.astype(np.float32) / 255
    s = 768
    h, w = img.shape[:-1]
    h, w = (s, int(s * w / h)) if h > w else (int(s * h / w), s)
    ph, pw = s - h, s - w
    img_input = np.zeros([s, s, 3], dtype=np.float32)
    img_input[ph // 2:ph // 2 + h, pw // 2:pw // 2 + w] = cv2.resize(img, (w, h))
    img_input = np.transpose(img_input, (2, 0, 1))
    img_input = img_input[np.newaxis, :]
    pred = model.run(None, {"img": img_input})[0].item()
    return pred

class AnimeAestheticClassifier():
    def __init__(self, device = "CPUExecutionProvider"):
        super().__init__()
        self.repo_id = "skytnt/anime-aesthetic"
        anime_aesthetic_path = hf_hub_download(repo_id=self.repo_id, filename="model.onnx")
        self.anime_aesthetic = rt.InferenceSession(anime_aesthetic_path, providers=[device])

    def device(self):
        return self.anime_aesthetic.get_providers()[0]

    def tags(self, images: list[str] | str) -> typing.Generator[dict[str, float], None, None]:

        if type(images) == str:
            images = [images]
        
        for image_path in images:
            img = np.array(pilimg.open(image_path).convert('RGB'))
            pred = _predict(self.anime_aesthetic, img)
            
            if isinstance(images, list):
                yield {"aesthetic": pred}
            else:
                return {"aesthetic": pred}