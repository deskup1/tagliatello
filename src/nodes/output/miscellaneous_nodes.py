from ...graph import BaseNode, AttributeDefinition, AnyAttributeDefinition, FloatAttributeDefinition, ComboAttributeDefinition, StringAttributeDefinition

import src.helpers as helpers

import time
import os

import dearpygui.dearpygui as dpg
import filetype

import PIL.Image as Image

class DisplayNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.__text_tag = None
        self.__file_content_tag = None
        self.__image_tag = None
        self.__texture_tag = None

    
    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {"in": AnyAttributeDefinition()}
    
    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return {"out": AnyAttributeDefinition()}
    
    @classmethod
    def name(cls) -> str:
        return "Display"
    
    @classmethod
    def category(cls) -> str:
        return "Misceallaneous"
    
    def show_custom_ui(self, parent: int | str):

        texture_data = []
        for y in range(0, 150):
            for x in range(0, 150):
                # show black and pink checkerboard
                if (x // 30) % 2 == (y // 30) % 2:
                    texture_data.append(0)
                    texture_data.append(0)
                    texture_data.append(0)
                    texture_data.append(255/255)
                else:
                    texture_data.append(255/255)
                    texture_data.append(0)
                    texture_data.append(255/255)
                    texture_data.append(255/255)


        with dpg.texture_registry(show=False):
            self.__texture_tag = dpg.add_dynamic_texture(width=150, height=150, default_value=texture_data)

        self.__image_tag = dpg.add_image(self.__texture_tag, parent=parent, show=False)
        self.__text_tag = dpg.add_text("[No input]", parent=parent)
        self.__file_content_tag = dpg.add_input_text(multiline=True, parent=parent, width=200, height=200, show=False, readonly=True)

    
    def init(self):
        self.__show_text("[No input]")

    def __get_file_details(self, file_path: str) -> dict:
        file_name = os.path.basename(file_path)
        path = os.path.dirname(file_path)
        file_size = os.path.getsize(file_path)
        return f"File: {file_name}\nPath: {path}\nSize: {file_size} bytes"
    
    def __get_txt_file_content(self, file_path: str) -> str:
        content = ""
        with open(file_path, "r") as f:
            content = f.read(513)
        
        if len(content) > 512:
            content = content[:512] + "..."

        return content
        
    def __show_text(self, any):
        if self.__text_tag is None:
            return
        
        to_display = str(any)
        if len(to_display) > 256:
            to_display = to_display[:256] + "..."

        # split by lines up to 30 characters
        lines = [to_display[i:i+30] for i in range(0, len(to_display), 30)]
        to_display = "\n".join(lines)


        dpg.set_value(self.__text_tag, to_display) 
        dpg.show_item(self.__text_tag)
        dpg.hide_item(self.__file_content_tag)
        dpg.hide_item(self.__image_tag)

    def _show_directory(self, dir_path: str):
        dpg.show_item(self.__text_tag)
        dpg.hide_item(self.__file_content_tag)
        dpg.hide_item(self.__image_tag)

        path = os.path.dirname(dir_path)
        files = len(os.listdir(dir_path))

        dpg.set_value(self.__text_tag, f"Directory: {dir_path}\nPath: {path}\nFiles: {files}")

    def _show_file(self, file_path: str):
        dpg.show_item(self.__text_tag)
        dpg.hide_item(self.__file_content_tag)
        dpg.hide_item(self.__image_tag)

        dpg.set_value(self.__text_tag, self.__get_file_details(file_path))

    def _show_txt_file(self, file_path: str):
        dpg.show_item(self.__file_content_tag)
        dpg.show_item(self.__text_tag)
        dpg.hide_item(self.__image_tag)

        dpg.set_value(self.__text_tag, self.__get_file_details(file_path))
        dpg.set_value(self.__file_content_tag, self.__get_txt_file_content(file_path))

    def _show_image(self, image_path: str):
        dpg.show_item(self.__text_tag)
        dpg.hide_item(self.__file_content_tag)
        dpg.show_item(self.__image_tag)

        image = Image.open(image_path)
        image = helpers.convert_to_thumbnail(image)
        cv = helpers.convert_pil_to_cv(image)
        dpg_texture = helpers.convert_cv_to_dpg(cv)
        dpg.set_value(self.__texture_tag, dpg_texture)

        dpg.set_value(self.__text_tag, "Image file: " + image_path)

    def _show_images(self, image_paths: list[str]):
        dpg.show_item(self.__text_tag)
        dpg.hide_item(self.__file_content_tag)
        dpg.show_item(self.__image_tag)

        images = [Image.open(image_path) for image_path in image_paths]

        # limit to 16 images
        images = images[:16]

        image = helpers.images_thumbnail(images)
        cv = helpers.convert_pil_to_cv(image)
        dpg_texture = helpers.convert_cv_to_dpg(cv)
        dpg.set_value(self.__texture_tag, dpg_texture)
        dpg.set_value(self.__text_tag, f"Images: {len(image_paths)}")

    def _show_base64_image(self, base64_image: str):
        dpg.show_item(self.__text_tag)
        dpg.hide_item(self.__file_content_tag)
        dpg.show_item(self.__image_tag)

        image = helpers.convert_base64_to_pil(base64_image)
        image = helpers.convert_to_thumbnail(image)
        cv = helpers.convert_pil_to_cv(image)
        dpg_texture = helpers.convert_cv_to_dpg(cv)
        dpg.set_value(self.__texture_tag, dpg_texture)


    def _show_base64_images(self, base64_images: list[str]):
        dpg.show_item(self.__text_tag)
        dpg.hide_item(self.__file_content_tag)
        dpg.show_item(self.__image_tag)

        images = [helpers.convert_base64_to_pil(base64_image) for base64_image in base64_images]

        # limit to 16 images
        images = images[:16]

        image = helpers.images_thumbnail(images)
        cv = helpers.convert_pil_to_cv(image)
        dpg_texture = helpers.convert_cv_to_dpg(cv)
        dpg.set_value(self.__texture_tag, dpg_texture)
        dpg.set_value(self.__text_tag, f"Images: {len(base64_images)}")
    
    def run(self, **kwargs) -> dict:
        input = kwargs.get("in")

        if isinstance(input, str):
            if os.path.isfile(input):
                text_file_extensions = [
                    ".txt", ".log", ".md", ".py", ".json", ".xml", ".csv", ".tsv", ".html", 
                    ".css", ".js", ".c", ".cpp", ".h", ".hpp", ".java", ".php", ".sh",
                    ".bat", ".ps1", ".yaml", ".yml", ".ini", ".cfg", ".conf", ".config"]
                if os.path.splitext(input)[1] in text_file_extensions:
                    self._show_txt_file(input)
                elif filetype.is_image(input):
                    self._show_image(input)
                else:
                    self._show_file(input)

            elif os.path.isdir(input):
                self._show_directory(input)

            elif input.startswith("data:image"):
                self._show_base64_image(input)

            else:
                self.__show_text(input)
        elif isinstance(input, list):
            # if all are strings
            if all(isinstance(i, str) for i in input):
                # if all starts with data:image
                if all(i.startswith("data:image") for i in input):
                    self._show_base64_images(input)

                # if all are files
                elif all(os.path.isfile(i) for i in input):
                    image_extensions = [".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp", ".ico"]
                    if all(os.path.splitext(i)[1] in image_extensions for i in input):
                        self._show_images(input)
                        
                else:
                    self._show_images(input)
            else:
                self.__show_text(input)
        else:
            self.__show_text(input)
            
        return {"out": input}

class WaitNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.set_default_input("seconds", 1)

    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {"seconds": FloatAttributeDefinition(min_value=0), "in": AnyAttributeDefinition()}
    
    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return {"out": AnyAttributeDefinition()}
    
    @classmethod
    def name(cls) -> str:
        return "Wait"
    
    @classmethod
    def category(cls) -> str:
        return "Misceallaneous"
    
    def run(self, **kwargs) -> dict:
        seconds = kwargs["seconds"]
        input = kwargs["in"]
        time.sleep(seconds)
        return {"out": input}

class ConsoleLogsNode(BaseNode):
    def __init__(self):
        super().__init__()

    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {"logs": StringAttributeDefinition()}
    
    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return { "logs" : StringAttributeDefinition( list=True) }
    
    @classmethod
    def name(cls) -> str:
        return "Console Logs"
    
    @classmethod
    def category(cls) -> str:
        return "Misceallaneous"
    
    def run(self, **kwargs) -> dict:
        return {}
    

class DebugComboBoxNode(BaseNode):
    def __init__(self):
        super().__init__()
    
    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {"options": ComboAttributeDefinition(lambda: ["Option 1", "Option 2", "Option 3"])}
    
    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return {"selected": AnyAttributeDefinition()}
    
    @classmethod
    def name(cls) -> str:
        return "Debug Combo Box"
    
    @classmethod
    def category(cls) -> str:
        return "Misceallaneous"
    
    def run(self, **kwargs) -> dict[str, object]:
        return {"selected": self.default_inputs.get("options", "")}