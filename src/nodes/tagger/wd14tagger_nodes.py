from ...graph import BaseNode, AttributeDefinition, BoolenAttributeDefinition, FloatAttributeDefinition, ComboAttributeDefinition, FileAttributeDefinition
from ...settings import SETTINGS
from .wd14tagger import Wd14Tagger

import requests

import dearpygui.dearpygui as dpg

class Wd14TaggerNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.set_static_input("tagger", "SmilingWolf/wd-vit-tagger-v3")
        self.set_static_input("general_threshold", 0.4)
        self.set_static_input("character_threshold", 0.4)
        self.set_static_input("include_rating", True)
        self.set_static_input("device", "CPUExecutionProvider")
        self.set_static_input("cache_dir", SETTINGS.get("hf_cache_dir"))
        self.models = None
        self.tagger = None
        self.unload_model_button = None
    
    def available_models(self):
        if self.models is not None:
            return self.models
        
        url = "https://huggingface.co/api/models"
        params = {
            "author" : "SmilingWolf",
            "search" : "tagger"
        }
        
        try:
            response = requests.get(url, params=params, timeout=5).json()
            self.models = [model["id"] for model in response]
            return self.models
        except Exception as e:
            return ['SmilingWolf/wd-v1-4-vit-tagger', 
                    'SmilingWolf/wd-v1-4-convnext-tagger', 
                    'SmilingWolf/wd-v1-4-convnext-tagger-v2', 
                    'SmilingWolf/wd-v1-4-vit-tagger-v2', 
                    'SmilingWolf/wd-v1-4-swinv2-tagger-v2', 
                    'SmilingWolf/wd-v1-4-convnextv2-tagger-v2', 
                    'SmilingWolf/wd-v1-4-moat-tagger-v2', 
                    'SmilingWolf/wd-vit-tagger-v3', 
                    'SmilingWolf/wd-convnext-tagger-v3', 
                    'SmilingWolf/wd-swinv2-tagger-v3']

    @property
    def static_input_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "tagger": ComboAttributeDefinition(values_callback=self.available_models),
            "general_threshold": FloatAttributeDefinition(min_value=0, max_value=1),
            "character_threshold": FloatAttributeDefinition(min_value=0, max_value=1),
            "include_rating": BoolenAttributeDefinition(),
            "device": ComboAttributeDefinition(values_callback=lambda: ["CPUExecutionProvider", "CUDAExecutionProvider"]),
            "cache_dir": FileAttributeDefinition(directory_selector=True)
        }
    
    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "out": AttributeDefinition(type_name="tagger")
        }
    
    def unload_model(self):
        if self.tagger is not None:
            self.tagger.unload_model()
            self.tagger = None
        dpg.hide_item(self.unload_model_button)
    
    def show_custom_ui(self, parent: int | str) -> int | str | None:
        self.unload_model_button = dpg.add_button(label="Unload Model", callback=self.unload_model, parent=parent, show=False)
    
    @classmethod
    def name(cls) -> str:
        return "WD14 Tagger"
    
    @classmethod
    def category(cls) -> str:
        return "Tagger"
    
    def init(self):
        tagger = self.static_inputs["tagger"]

        if self.tagger is not None:
            same_model = self.tagger.name == tagger
            same_general_threshold = self.tagger.general_treshold == self.static_inputs["general_threshold"]
            same_character_threshold = self.tagger.character_treshold == self.static_inputs["character_threshold"]
            same_device = self.tagger.device == self.static_inputs["device"]
            same_include_rating = self.tagger.include_rating == self.static_inputs["include_rating"]
            if same_model and same_general_threshold and same_character_threshold and same_device and same_include_rating:
                return
            
        general_threshold = self.static_inputs["general_threshold"]
        character_threshold = self.static_inputs["character_threshold"]
        device = self.static_inputs["device"]
        include_rating = self.static_inputs["include_rating"]
        cache_dir = self.static_inputs["cache_dir"]
        self.tagger = Wd14Tagger(
            model_name=tagger, 
            general_treshold=general_threshold, 
            character_treshold=character_threshold, 
            device=device, 
            include_rating=include_rating,
            cache_dir=cache_dir)

    def run(self, **kwargs) -> dict[str, object]:
        return {"out": self.tagger}