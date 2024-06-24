from ...graph import AttributeDefinition, MultiFileAttributeDefinition, FloatAttributeDefinition, DictAttributeDefinition, StringAttributeDefinition
from ..progress_node import ProgressNode

class TagImageNode(ProgressNode):
    def __init__(self):
        super().__init__()
        self.__output_definitions = {
            "images": MultiFileAttributeDefinition(),
            "tags": DictAttributeDefinition(StringAttributeDefinition(), FloatAttributeDefinition(), list=True),
            "tags_string": StringAttributeDefinition(list=True),
        }

    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "tagger": AttributeDefinition(type_name="tagger"),
            "images": MultiFileAttributeDefinition()
        }
    
    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return self.__output_definitions
    
    @classmethod
    def name(cls) -> str:
        return "Tag Images"
    
    @classmethod
    def category(cls) -> str:
        return "Tagger"
    
    def init(self):
        pass

    def run(self, **kwargs) -> dict:
        tagger = kwargs["tagger"]
        images = kwargs["images"]

        tags = []

        self.set_progress(0, len(images))

        for i, tags_dict in enumerate(tagger.tags(images)):
            tags.append(tags_dict)

            if self.output_definitions["tags"].list == False:
                self.set_progress(len(images), len(images))
                return { 
                    "tags" : tags[0], 
                    "tags_string": [str(tag) for tag in tags[0]]
                }
            
            self.set_progress(i+1, len(images))
            
        self.set_progress(len(images), len(images))

        return {"tags": tags, "tags_string": [str(tag) for tag in tags], "images": images}
