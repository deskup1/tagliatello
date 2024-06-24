from ...graph import BaseNode, AttributeDefinition, FileAttributeDefinition, ComboAttributeDefinition, IntegerAttributeDefinition

from .hf_aesthetic_classifier import HfPipelineAestheticClassifier
from ...settings import SETTINGS

import dearpygui.dearpygui as dpg

class HfPipelineAestheticClassifierNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.set_static_input("device", "cpu")
        self.set_static_input("model", "cafeai/cafe_aesthetic")
        self.set_static_input("batch_size", 1)
        self.set_static_input("cache_dir", SETTINGS.get("hf_cache_dir"))
        self.tagger = None
        self.unload_model_button = None

    @classmethod
    def name(cls) -> str:
        return "HuggingFace Aesthetic Classifier"
    
    @classmethod
    def category(cls) -> str:
        return "Tagger"

    @property
    def static_input_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "model": ComboAttributeDefinition(values_callback=lambda: ["cafeai/cafe_aesthetic"]),
            "device": ComboAttributeDefinition(values_callback=lambda: ["cpu", "cuda:0"]),
            "batch_size": IntegerAttributeDefinition(min_value=1, max_value=1024),
            "cache_dir": FileAttributeDefinition(directory_selector=True)
        }
    
    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "tagger": AttributeDefinition(type_name="tagger")
        }
    
    def init(self):
        if self.tagger is not None:
            same_model = self.tagger.model_name == self.static_inputs["model"]
            same_device = self.tagger.device == self.static_inputs["device"]
            same_batch_size = self.tagger.batch_size == self.static_inputs["batch_size"]
            if same_model and same_device and same_batch_size:
                return
        
        model = self.static_inputs["model"]
        device = self.static_inputs["device"]
        batch_size = self.static_inputs["batch_size"]
        cache_dir = self.static_inputs["cache_dir"]

        self.tagger = HfPipelineAestheticClassifier(model_name=model, device=device, batch_size=batch_size, cache_dir=cache_dir)
        if self.unload_model_button is not None and dpg.does_item_exist(self.unload_model_button):
            dpg.show_item(self.unload_model_button)

    def unload_model(self):
        if self.tagger is not None:
            self.tagger.unload_model()
            self.tagger = None
            
        dpg.hide_item(self.unload_model_button)
    
    def show_custom_ui(self, parent: int | str):
        self.unload_model_button = dpg.add_button(label="Unload Model", callback=self.unload_model, parent=parent, show=False)
    
    def run(self, **kwargs) -> dict[str, object]:
        return {"tagger": self.tagger}