import sys

from transformers import AutoModelForCausalLM, AutoProcessor
from accelerate.utils import release_memory
import gc

if __name__ == "__main__":
    sys.path.append("")
    from src.helpers import pillow_from_any_string
    from src.settings import SETTINGS
else:
    from ...helpers import pillow_from_any_string
    from ...settings import SETTINGS

# pillow
from PIL import Image
from typing import Generator
import torch

class Florence2Model:
    def __init__(self, model: str = "microsoft/Florence-2-large", cache_dir: str = None, device: str = "cpu", precision: str = "fp16"):
        if cache_dir is None:
            cache_dir = SETTINGS.get("hf_cache_dir")
        self.model_name = model
        self.dtype = {"bf16": torch.bfloat16, "fp16": torch.float16, "fp32": torch.float32}[precision]
        self.model = AutoModelForCausalLM.from_pretrained(model, trust_remote_code=True, cache_dir=cache_dir, device_map=device).to(self.dtype).eval()
        self.processor = AutoProcessor.from_pretrained(model, trust_remote_code=True, cache_dir=cache_dir)
        self.device = device
        self.cache_dir = cache_dir
        self.precision = precision


    def unload_model(self):
        self.model, self.processor = release_memory(self.model, self.processor)
        gc.collect()
        torch.cuda.empty_cache()

    def __run_batch(self, 
                    task_prompt: str,
                    text_input: str|list[str],
                    images: list[Image.Image], 
                    max_new_tokens: int = 1024, 
                    num_beams : int = 3,
                    ) -> list[str]:
        
        prompt = task_prompt
        if text_input != "" and text_input is not None:
            if isinstance(text_input, list):
                prompt = [task_prompt + " " + text for text in text_input]
            else:
                prompt = task_prompt + " " + text_input
        
        inputs = self.processor(text=prompt, images=images, return_tensors="pt").to(self.dtype).to(self.device)
        generated_ids = self.model.generate(
            input_ids =inputs["input_ids"],
            pixel_values=inputs["pixel_values"],
            max_new_tokens=max_new_tokens,
            early_stopping=False,
            do_sample=False,
            num_beams=num_beams
        )

        generated_texts = self.processor.batch_decode(generated_ids, skip_special_tokens=False)
        parsed_answers = []
        for i, generated_text in enumerate(generated_texts):
            parsed_answer = self.processor.post_process_generation(
                generated_text,
                task=task_prompt,
                image_size=(images[i].width, images[i].height)
            )
            # get only entries from dict, convert to list and strip
            parsed_answers.append(parsed_answer)

        return parsed_answers

    def run(self, 
             task_prompt: str = "<OD>",
             text_input: str|list[str] = "",
             images: list[str|Image.Image] = [],
             num_beams: int = 3,
             max_new_tokens: int = 1024,
             batch_size: int = 1
             ) -> Generator[list[str], None, None]:
        
        # convert images to pillow image
        parsed_images = []
        for i, image in enumerate(images):
            if isinstance(image, str):
                parsed_images.append(pillow_from_any_string(image).convert("RGB"))
            elif isinstance(image, Image.Image):
                parsed_images.append(image.convert("RGB"))
            else:
                raise ValueError(f"Invalid image type at index {i}")
                
        # converd parsed_images to batch
        batch_images = []
        batch_inputs = []
        for i in range(0, len(parsed_images), batch_size):
            batch_images.append(parsed_images[i:i + batch_size])
            if isinstance(text_input, str):
                batch_inputs.append(text_input)
            else:
                batch_inputs.append(text_input[i:i + batch_size])

        for i, batch in enumerate(batch_images):
            yield self.__run_batch(
                task_prompt=task_prompt,
                text_input=batch_inputs[i],
                images=batch,
                num_beams=num_beams,
                max_new_tokens=max_new_tokens
            )

if __name__ == "__main__":
    model = Florence2Model(device="cuda")
    image = Image.open("screenshots/screenshot1.png")
    result = model.run(images=[image,image], task_prompt="<CAPTION>")

    for i, result in enumerate(result):
        print(f"Result {i}: {result}")

    model.unload_model()