from ...graph import BaseNode, AttributeDefinition, BoolenAttributeDefinition, ComboAttributeDefinition

from .anime_aesthetic_classifier import AnimeAestheticClassifier

import dearpygui.dearpygui as dpg

class AnimeAestheticClassifierNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.set_static_input("device", "CPUExecutionProvider")
        self.tagger = None
        self.unload_model_button = None

    @classmethod
    def name(cls) -> str:
        return "Anime Aesthetic Classifier"
    
    @classmethod
    def category(cls) -> str:
        return "Tagger"

    @property
    def static_input_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "device": ComboAttributeDefinition(values_callback=lambda: ["CPUExecutionProvider", "CUDAExecutionProvider"])
        }
    
    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "tagger": AttributeDefinition(type_name="tagger")
        }
    
    def init(self):
        if self.tagger is not None:
            return
        
        device = self.static_inputs["device"]
        self.tagger = AnimeAestheticClassifier(device=device)
        if self.unload_model_button is not None and dpg.does_item_exist(self.unload_model_button):
            dpg.show_item(self.unload_model_button)

    def unload_model(self):
        self.tagger = None
        dpg.hide_item(self.unload_model_button)
    
    def show_custom_ui(self, parent: int | str):
        self.unload_model_button = dpg.add_button(label="Unload Model", callback=self.unload_model, parent=parent, show=False)

    def show_custom_ui(self, parent: int | str):
        return super().show_custom_ui(parent)
    
    def run(self, **kwargs) -> dict[str, object]:
        return {"tagger": self.tagger}