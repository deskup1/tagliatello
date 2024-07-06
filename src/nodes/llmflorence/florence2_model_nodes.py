from ...graph import BaseNode, ComboAttributeDefinition, AttributeDefinition, FileAttributeDefinition, IntegerAttributeDefinition, MultiFileAttributeDefinition, ListAttributeDefinition, StringAttributeDefinition, MultipleAttributeDefinition
from .florence2_model import Florence2Model
from ...settings import SETTINGS
from ..progress_node import ProgressNode
import dearpygui.dearpygui as dpg


class Florence2ModelNode(BaseNode):

    @classmethod
    def name(cls) -> str:
        return "Florence 2 Model"
    
    @classmethod
    def category(cls) -> str:
        return "Florence VLM"
    
    def __init__(self):
        super().__init__()
        self.set_static_input("model", "microsoft/Florence-2-large")
        self.set_static_input("device", "cpu")
        self.set_static_input("cache_dir", SETTINGS.get("hf_cache_dir"))
        self.set_static_input("precision", "fp16")
        self.model = None
        self.unload_model_button = None

    @property
    def static_input_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "model": ComboAttributeDefinition(values_callback=lambda: ["microsoft/Florence-2-large", "microsoft/Florence-2-base", "microsoft/Florence-2-large-ft", "microsoft/Florence-2-base-ft"]),
            "device": ComboAttributeDefinition(values_callback=lambda: ["cpu", "cuda:0"]),
            "precision": ComboAttributeDefinition(values_callback=lambda: ["fp16", "bf16", "fp32"]),
            "cache_dir": FileAttributeDefinition(directory_selector=True)
        }
    
    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "model": AttributeDefinition(type_name="florence2_vlm")
        }
    
    def init(self):
        model = self.static_inputs["model"]
        device = self.static_inputs["device"]
        cache_dir = self.static_inputs["cache_dir"]
        precision = self.static_inputs["precision"]

        if self.model is not None:
            same_model = self.model.model_name == model
            same_device = self.model.device == device
            same_cache_dir = self.model.cache_dir == cache_dir
            same_precision = self.model.precision == precision
            if same_model and same_device and same_cache_dir and same_precision:
                return
            self.unload_model()

        self.model = Florence2Model(model=model, device=device, cache_dir=cache_dir, precision=precision)
        if self.unload_model_button is not None and dpg.does_item_exist(self.unload_model_button):
            dpg.show_item(self.unload_model_button)

    def unload_model(self):
        if self.model is not None:
            self.model.unload_model()
            self.model = None
            if self.unload_model_button is not None and dpg.does_item_exist(self.unload_model_button):
                dpg.hide_item(self.unload_model_button)

    def show_custom_ui(self, parent: int | str) -> int | str | None:
        self.unload_model_button = dpg.add_button(label="Unload Model", callback=self.unload_model, parent=parent, show=False)
        return self.unload_model_button
    
    def run(self, **kwargs) -> dict:
        return {"model": self.model}


class Florence2ModelBaseNode(ProgressNode):

    @classmethod
    def name(cls) -> str:
        raise NotImplementedError("Abstract method")
    
    @classmethod
    def category(cls) -> str:
        return "Florence VLM"
    
    def __init__(self):
        super().__init__()
        self.set_default_input("model", None)
        self.set_default_input("images", [])
        self.set_default_input("num_beams", 3)
        self.set_default_input("max_new_tokens", 1024)
        self.set_default_input("batch_size", 1)


    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "model": AttributeDefinition(type_name="florence2_vlm"),
            "images": MultiFileAttributeDefinition(),
            "num_beams": IntegerAttributeDefinition(min_value=1, max_value=16),
            "max_new_tokens": IntegerAttributeDefinition(min_value=1, max_value=8192),
            "batch_size": IntegerAttributeDefinition(min_value=1, max_value=64),
        }
    
    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        raise NotImplementedError("Abstract method")
    
    def run(self, **kwargs) -> dict:
        raise NotImplementedError("Abstract method")

class Florence2ModelCaptionNode(Florence2ModelBaseNode):

    def __init__(self):
        super().__init__()
        self.set_default_input("type", "<CAPTION>")

    @classmethod
    def name(cls) -> str:
        return "Florence 2 Model Caption"

    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            **super().input_definitions,
            "type": ComboAttributeDefinition(values_callback= lambda: ["<CAPTION>", "<DETAILED_CAPTION>", "<MORE_DETAILED_CAPTION>", "<OCR>"])
        }

    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "model": AttributeDefinition(type_name="florence2_vlm"),
            "images": MultiFileAttributeDefinition(),
            "captions": ListAttributeDefinition(StringAttributeDefinition()),
        }
    
    def run(self, **kwargs) -> dict:
        images = kwargs["images"]
        model: Florence2Model = kwargs["model"]
        num_beams = kwargs["num_beams"]
        max_new_tokens = kwargs["max_new_tokens"]
        batch_size = kwargs["batch_size"]
        type = kwargs["type"]

        self.set_progress(0, len(images))
        captions = []

        # iterate over generator
        for batch_captions in model.run(task_prompt=type, images=images, num_beams=num_beams, max_new_tokens=max_new_tokens, batch_size=batch_size):
            batch_captions = [caption[type].strip() for caption in batch_captions]
            captions.extend(batch_captions)
            self.set_progress(len(captions), len(images))

        return {"images": images, "captions": captions, "model": model}

class Florence2ModelRegionDetectionNode(Florence2ModelBaseNode):

    def __init__(self):
        super().__init__()
        self.set_default_input("type", "<OD>")

    @classmethod
    def name(cls) -> str:
        return "Florence 2 Model Region Detection"

    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            **super().input_definitions,
            "type": ComboAttributeDefinition(values_callback = lambda: ["<OD>", "<REGION_PROPOSAL>", "<DENSE_REGION_CAPTION>", "<OCR_WITH_REGION>"])
        }

    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "model": AttributeDefinition(type_name="florence2_vlm"),
            "images": MultiFileAttributeDefinition(),
            "bboxes": ListAttributeDefinition(ListAttributeDefinition(AttributeDefinition(type_name="bbox"))),
            "bboxes_labels": ListAttributeDefinition(ListAttributeDefinition(StringAttributeDefinition()))
        }
    
    def run(self, **kwargs) -> dict:
        images = kwargs["images"]
        model: Florence2Model = kwargs["model"]
        num_beams = kwargs["num_beams"]
        max_new_tokens = kwargs["max_new_tokens"]
        batch_size = kwargs["batch_size"]
        type = kwargs["type"]

        self.set_progress(0, len(images))
        detections = []

        # iterate over generator
        for batch_detections in model.run(task_prompt=type, images=images, num_beams=num_beams, max_new_tokens=max_new_tokens, batch_size=batch_size):
            detections.extend(batch_detections)
            self.set_progress(len(detections), len(images))

        # convert to bbox format
        bboxes = []
        bboxes_labels = []

        for detection in detections:
            bboxes.append(detection[type]["bboxes"])
            bboxes_labels.append(detection[type]["labels"])


        return {"images": images, "bboxes": bboxes, "bboxes_labels": bboxes_labels, "model": model}

class Florence2ModelCaptionGrounding(Florence2ModelBaseNode):
    
    def __init__(self):
        super().__init__()
        self.set_default_input("captions", [])
        self.set_default_input("type", "<CAPTION_TO_PHRASE_GROUNDING>")

    @classmethod
    def name(cls) -> str:
        return "Florence 2 Model Caption Grounding"
    
    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            **super().input_definitions,
            'captions': MultipleAttributeDefinition(types = [StringAttributeDefinition(), ListAttributeDefinition(StringAttributeDefinition())]),
            "type": ComboAttributeDefinition(values_callback=lambda:["<CAPTION_TO_PHRASE_GROUNDING>"])
        }
    
    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "model": AttributeDefinition(type_name="florence2_vlm"),
            "images": MultiFileAttributeDefinition(),
            "captions": ListAttributeDefinition(StringAttributeDefinition()),
            "bboxes": ListAttributeDefinition(ListAttributeDefinition(AttributeDefinition(type_name="bbox"))),
            "bboxes_labels": ListAttributeDefinition(ListAttributeDefinition(StringAttributeDefinition()))
        }
    
    def run(self, **kwargs) -> dict:
        images = kwargs["images"]
        model: Florence2Model = kwargs["model"]
        num_beams = kwargs["num_beams"]
        max_new_tokens = kwargs["max_new_tokens"]
        batch_size = kwargs["batch_size"]
        captions = kwargs["captions"]
        type = kwargs["type"]

        # join type with caption
        if isinstance(captions[0], str) or len(captions) == 1:
            if len(captions) == 1:
                captions = captions[0]
        elif len(images) != len(captions):
            raise ValueError("Captions and images must have the same length")

        self.set_progress(0, len(images))
        detections = []

        # iterate over generator
        for batch_detections in model.run(task_prompt=type, text_input=captions, images=images, num_beams=num_beams, max_new_tokens=max_new_tokens, batch_size=batch_size):
            detections.extend(batch_detections)
            self.set_progress(len(detections), len(images))

        bboxes = []
        bboxes_labels = []

        for detection in detections:
            bboxes_labels.append(detection[type].get("labels", []))
            bboxes.append(detection[type].get("bboxes", []))

        return {"images": images, "captions": captions, "bboxes": bboxes, "bboxes_labels": bboxes_labels, "model": model}