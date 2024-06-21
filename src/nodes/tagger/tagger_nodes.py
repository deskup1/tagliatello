from ...graph import BaseNode, AttributeDefinition, MultiFileAttributeDefinition    , MultipleAttributeDefinition, FloatAttributeDefinition, DictAttributeDefinition, StringAttributeDefinition
import dearpygui.dearpygui as dpg
import time

class TagImageNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.__last_update = None
        self.__execution_times = []

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

    def show_custom_ui(self, parent: int | str):
        self.progress = dpg.add_progress_bar(default_value=0, overlay="0/0 ETA: 0s", parent=parent, width=150)


    def __skip_median_outliers(self, values: list[float]) -> list[float]:
        values.sort()
        if len(values) < 3:
            return values

        median = values[len(values) // 2]
        std = sum((x - median) ** 2 for x in values) / len(values)
        std = std ** 0.5

        return [x for x in values if abs(x - median) < std]

    def update_progress(self, current: int, total: int):
        progress_float = (float(current) / float(total)) if total != 0 else 0

        if self.__last_update is None:
            self.__last_update = time.time()
            dpg.configure_item(self.progress, overlay=f"{current}/{total} ETA: N/A")
            dpg.set_value(self.progress, progress_float)
            return
        
        if current >= total:
            dpg.configure_item(self.progress, overlay=f"{current}/{total} ETA: Done")
            dpg.set_value(self.progress, 1)
        
   
        self.__execution_times.append(time.time() - self.__last_update)
        self.__last_update = time.time()
        execution_times = self.__skip_median_outliers(self.__execution_times)
        avg_time = sum(execution_times) / len(execution_times)
        remaining_time = avg_time * (total - current)

        dpg.configure_item(self.progress, overlay=f"{current}/{total} ETA: {remaining_time:.2f}s")
        dpg.set_value(self.progress, progress_float)

    
    def run(self, **kwargs) -> dict:
        tagger = kwargs["tagger"]
        images = kwargs["images"]

        tags = []
        # iterate over generator tagger.tags(images) -> dict[str, float]
        for i, tags_dict in enumerate(tagger.tags(images)):
            tags.append(tags_dict)
            self.update_progress(i, len(images))

            if self.output_definitions["tags"].list == False:
                self.update_progress(len(images), len(images))
                return { 
                    "tags" : tags[0], 
                    "tags_string": [str(tag) for tag in tags[0]]
                }
            
        self.update_progress(len(images), len(images))

        return {"tags": tags, "tags_string": [str(tag) for tag in tags], "images": images}
        

