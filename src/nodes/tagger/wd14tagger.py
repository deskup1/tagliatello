import PIL.Image
import numpy as np
import huggingface_hub
import onnxruntime as rt
import cv2
import pandas as pd
import numpy as np
from PIL import Image
import io
import pandas as pd
from typing import Generator


def _make_square(img, target_size):
    old_size = img.shape[:2]
    desired_size = max(old_size)
    desired_size = max(desired_size, target_size)

    delta_w = desired_size - old_size[1]
    delta_h = desired_size - old_size[0]
    top, bottom = delta_h // 2, delta_h - (delta_h // 2)
    left, right = delta_w // 2, delta_w - (delta_w // 2)

    color = [255, 255, 255]
    new_im = cv2.copyMakeBorder(
        img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color
    )
    return new_im


def _smart_resize(img, size):
    # Assumes the image has already gone through make_square
    if img.shape[0] > size:
        img = cv2.resize(img, (size, size), interpolation=cv2.INTER_AREA)
    elif img.shape[0] < size:
        img = cv2.resize(img, (size, size), interpolation=cv2.INTER_CUBIC)
    return img

def _load_model(model_repo: str, model_filename: str, device = "CPUExecutionProvider") -> rt.InferenceSession:
    path = huggingface_hub.hf_hub_download(repo_id=model_repo, filename=model_filename)
    return rt.InferenceSession(path, providers=[device])

def _load_labels(model_repo: str, label_filename: str) -> list[str]:
    path = huggingface_hub.hf_hub_download(model_repo, label_filename )
    df = pd.read_csv(path)
    tag_names = df["name"].tolist()
    rating_indexes = list(np.where(df["category"] == 9)[0])
    general_indexes = list(np.where(df["category"] == 0)[0])
    character_indexes = list(np.where(df["category"] == 4)[0])
    return tag_names, rating_indexes, general_indexes, character_indexes


def _predict(
    image: PIL.Image.Image,
    model: rt.InferenceSession,
    general_threshold: float,
    character_threshold: float,
    tag_names: list[str],
    rating_indexes: list[np.int64],
    general_indexes: list[np.int64],
    character_indexes: list[np.int64],
):
    
    _, height, width, _ = model.get_inputs()[0].shape

    # Alpha to white
    image = image.convert("RGBA")
    new_image = PIL.Image.new("RGBA", image.size, "WHITE")
    new_image.paste(image, mask=image)
    image = new_image.convert("RGB")
    image = np.asarray(image)

    # PIL RGB to OpenCV BGR
    image = image[:, :, ::-1]

    image = _make_square(image, height)
    image = _smart_resize(image, height)
    image = image.astype(np.float32)
    image = np.expand_dims(image, 0)

    input_name = model.get_inputs()[0].name
    label_name = model.get_outputs()[0].name
    probs = model.run([label_name], {input_name: image})[0]

    labels = list(zip(tag_names, probs[0].astype(float)))

    # First 4 labels are actually ratings: pick one with argmax
    ratings_names = [labels[i] for i in rating_indexes]
    rating = dict(ratings_names)

    # Then we have general tags: pick any where prediction confidence > threshold
    general_names = [labels[i] for i in general_indexes]
    general_res = [x for x in general_names if x[1] > general_threshold]
    general_res = dict(general_res)

    # Everything else is characters: pick any where prediction confidence > threshold
    character_names = [labels[i] for i in character_indexes]
    character_res = [x for x in character_names if x[1] > character_threshold]
    character_res = dict(character_res)

    b = dict(sorted(general_res.items(), key=lambda item: item[1], reverse=True))
    a = (
        ", ".join(list(b.keys()))
        .replace("_", " ")
        .replace("(", "\(")
        .replace(")", "\)")
    )
    c = ", ".join(list(b.keys()))

    return (a, c, rating, character_res, general_res)

class Wd14Tagger:
    def __init__(self, model_name: str = 'SmilingWolf/wd-vit-tagger-v3', general_treshold = 0.1, character_treshold = 0.1, device = "CPUExecutionProvider", include_rating = True):
        self.labels = _load_labels(model_name, "selected_tags.csv")
        self.model = _load_model(model_name, "model.onnx", device)
        self.name = model_name
        self.general_treshold = general_treshold
        self.character_treshold = character_treshold
        self.include_rating = include_rating

    def __convert_image(self, image):
        if isinstance(image, str):
            image = Image.open(image).convert("RGB")
        elif isinstance(image, bytes):
            image = Image.open(io.BytesIO(image)).convert("RGB")
        elif isinstance(image, Image.Image):
            image = image.convert("RGB")
        elif isinstance(image, np.ndarray):
            image = Image.fromarray(image).convert("RGB")
        else:
            raise ValueError("image must be a path, bytes, PIL.Image.Image or np.ndarray")
        return image
    
    def device(self):
        return self.model.get_providers()[0]
    
    def __find_highest_rating(self, ratings: dict[str, float]) -> dict[str, float]:
        if len(ratings) == 0:
            raise ValueError("No ratings found")
        
        rating, value = max(ratings.items(), key=lambda x: x[1])
        return {
            rating: value
        }
        


    def tags(self, images) -> Generator[dict, None, None]:
        if isinstance(images, list):
            images = [self.__convert_image(image) for image in images]
        else:
            images = [self.__convert_image(images)]

        try:

            for image in images:
                result = _predict(image, self.model, self.general_treshold, self.character_treshold, self.labels[0], self.labels[1], self.labels[2], self.labels[3])
                yield {
                    **self.__find_highest_rating(result[2]),
                    **result[3],
                    **result[4]
                }

            return
        except Exception as e:
            raise ValueError(f"Error while tagging image: {e}")
