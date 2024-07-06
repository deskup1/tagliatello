from ...graph import BaseNode, AttributeDefinition, AttributeKind, AnyAttributeDefinition, FloatAttributeDefinition, MultipleAttributeDefinition, StringAttributeDefinition, ListAttributeDefinition, IntegerAttributeDefinition
from ...helpers import pillow_from_any_string
import src.helpers as helpers

import time
import os

import dearpygui.dearpygui as dpg
import filetype

import PIL.Image as Image
import PIL.ImageDraw as ImageDraw

import textwrap

class DisplayNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.__text_tag = None
        self.__file_content_tag = None
        self.__image_tag = None
        self.__texture_tag = None
        
        self.__output_defintions = {"out": AnyAttributeDefinition()}

        self._on_input_connected += self.__on_input_connected
        self._on_input_disconnected += self.__on_input_disconnected
    
    def __on_input_connected(self, input_name: str, output_node: BaseNode, output_name: str):
        if input_name == "in":
            self.__output_defintions["out"] = output_node.output_definitions[output_name].copy()
            self.__output_defintions["out"].kind = AttributeKind.VALUE
            self.refresh_ui()
        
    def __on_input_disconnected(self, input_name: str, _, __):
        if input_name == "in":
            self.__output_defintions["out"] = AnyAttributeDefinition()
            self.refresh_ui()

    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {"in": AnyAttributeDefinition()}
    
    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return self.__output_defintions
    
    @classmethod
    def name(cls) -> str:
        return "Display"
    
    @classmethod
    def category(cls) -> str:
        return "Misceallaneous"
    
    def show_custom_ui(self, parent: int | str):

        dpg.add_text("<deperected>", parent=parent, color=(255, 255, 0, 255))

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
                        self.__show_text(input)
                        
                else:
                    self.__show_text(input)
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
    
class DisplayText(BaseNode):
    def __init__(self):
        super().__init__()
        self.text_id = None

        self.__output_defintions = {"out": AnyAttributeDefinition()}

        self._on_input_connected += self.__on_input_connected
        self._on_input_disconnected += self.__on_input_disconnected

    
    def __on_input_connected(self, input_name: str, output_node: BaseNode, output_name: str):
        if input_name == "in":
            self.__output_defintions["out"] = output_node.output_definitions[output_name].copy()
            self.__output_defintions["out"].kind = AttributeKind.VALUE
            self.refresh_ui()
        
    def __on_input_disconnected(self, input_name: str, _, __):
        if input_name == "in":
            self.__output_defintions["out"] = AnyAttributeDefinition()
            self.refresh_ui()
    
    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {"in": AnyAttributeDefinition()}
    
    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return self.__output_defintions
    
    @classmethod
    def name(cls) -> str:
        return "Display Text"
    
    @classmethod
    def category(cls) -> str:
        return "Misceallaneous"
    
    def show_custom_ui(self, parent: int | str):
        super().show_custom_ui(parent)
        self.text_id = dpg.add_text("<----------------Text-to-display----------------->", parent=parent)

    def refresh_ui(self):
        if self.text_id is not None and dpg.does_item_exist(self.text_id):
            dpg.set_value(self.text_id, "<----------------Text-to-display----------------->")
        return super().refresh_ui()
    
    def run(self, **kwargs) -> dict:
        input = kwargs["in"]
        text = str(input)

        # wrap text to 50 characters
        text = textwrap.fill(text, 50)

        if self.text_id is not None and dpg.does_item_exist(self.text_id):
            # resize to up to 500 characters
            text = text[:497]
            if len(text) > 496:
                text += "..."
            dpg.set_value(self.text_id, text)
        
        return {"out": input}


class DisplayImage(BaseNode):
    def __init__(self):
        super().__init__()
        self.image_id = None
        self.texture_id = None

        self.__output_defintions = {"images": AnyAttributeDefinition()}

        self._on_input_connected += self.__on_input_connected
        self._on_input_disconnected += self.__on_input_disconnected

        self.initial_data = self.DEFAULT_TEXTURE_DATA.copy()

    IMAGE_SIZE = (300, 300)
    DEFAULT_TEXTURE_DATA = []
    
    for y in range(0, IMAGE_SIZE[0]):
        for x in range(0, IMAGE_SIZE[1]):
            # show black and pink checkerboard
            if (x // 30) % 2 == (y // 30) % 2:
                DEFAULT_TEXTURE_DATA.append(0)
                DEFAULT_TEXTURE_DATA.append(0)
                DEFAULT_TEXTURE_DATA.append(0)
                DEFAULT_TEXTURE_DATA.append(255/255)
            else:
                DEFAULT_TEXTURE_DATA.append(255/255)
                DEFAULT_TEXTURE_DATA.append(0)
                DEFAULT_TEXTURE_DATA.append(255/255)
                DEFAULT_TEXTURE_DATA.append(255/255)
    
    def __on_input_connected(self, input_name: str, output_node: BaseNode, output_name: str):
        if input_name == "images":
            self.__output_defintions["images"] = output_node.output_definitions[output_name].copy()
            self.__output_defintions["images"].kind = AttributeKind.VALUE
            self.refresh_ui()
        
    def __on_input_disconnected(self, input_name: str, _, __):
        if input_name == "images":
            self.__output_defintions["images"] = AnyAttributeDefinition()
            self.refresh_ui()
    
    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "images": MultipleAttributeDefinition(
            types=[StringAttributeDefinition(), 
                   ListAttributeDefinition(StringAttributeDefinition()), 
                   AttributeDefinition(type_name="image"), 
                   ListAttributeDefinition(AttributeDefinition(type_name="image") )
                   ])
            }
    
    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return self.__output_defintions
    
    @classmethod
    def name(cls) -> str:
        return "Display Image"
    
    @classmethod
    def category(cls) -> str:
        return "Misceallaneous"
    
    def show_custom_ui(self, parent: int | str):
        super().show_custom_ui(parent)
        with dpg.texture_registry(show=False):
            self.texture_id = dpg.add_dynamic_texture(width=self.IMAGE_SIZE[0], height=self.IMAGE_SIZE[1], default_value=self.initial_data)
        self.image_id = dpg.add_image(self.texture_id, parent=parent, show=False)
    def refresh_ui(self):
        if self.image_id is not None and dpg.does_item_exist(self.image_id):
            dpg.set_value(self.image_id, dpg.generate_uuid())
        return super().refresh_ui()
    

    def show_signle(self, image: str| Image.Image):
        if self.image_id is None or not dpg.does_item_exist(self.image_id):
            return

        dpg.show_item(self.image_id)

        try:
            if isinstance(image, str):
                image = pillow_from_any_string(image)
            elif isinstance(image, Image.Image):
                image = image
            else:
                dpg.hide_item(self.image_id)
                return

            image = helpers.convert_to_thumbnail(image, self.IMAGE_SIZE)
            cv = helpers.convert_pil_to_cv(image)
            dpg_texture = helpers.convert_cv_to_dpg(cv, self.IMAGE_SIZE)
            dpg.set_value(self.texture_id, dpg_texture)
        except:
            dpg.hide_item(self.image_id)
            return

    def show_multiple(self, images: list[str|Image.Image]):
        if self.image_id is None or not dpg.does_item_exist(self.image_id):
            return

        dpg.show_item(self.image_id)

        result_images = []
        for image in images:
            try:
                if isinstance(image, str):
                    image = pillow_from_any_string(image)
                elif isinstance(image, Image.Image):
                    image = image
                else:
                    continue
            except:
                image = None
            if image is not None:
                image = image.convert("RGB")
                result_images.append(image)

        image = helpers.images_thumbnail(result_images, self.IMAGE_SIZE)
        cv = helpers.convert_pil_to_cv(image)
        dpg_texture = helpers.convert_cv_to_dpg(cv, self.IMAGE_SIZE)
        dpg.set_value(self.texture_id, dpg_texture)

    def run(self, **kwargs) -> dict:
        input = kwargs["images"]
        if isinstance(input, list):
            self.show_multiple(input)
        else:
            self.show_signle(input)
        
        return {"images": input}

class ImageThumbnail(BaseNode):
    def __init__(self):
        super().__init__()
        self.set_default_input("image", "")
        self.set_default_input("max_width", 300)
        self.set_default_input("max_height", 300)
    
    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "image": MultipleAttributeDefinition(types=[StringAttributeDefinition(), AttributeDefinition(type_name="image")]),
            "max_width": IntegerAttributeDefinition(min_value=1),
            "max_height": IntegerAttributeDefinition(min_value=1)
        }
    
    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return {"image": AttributeDefinition(type_name="image")}
    
    @classmethod
    def name(cls) -> str:
        return "Image Thumbnail"
    
    @classmethod
    def category(cls) -> str:
        return "Misceallaneous"
    
    def run(self, **kwargs) -> dict:
        image = kwargs["image"]
        max_width = kwargs["max_width"]
        max_height = kwargs["max_height"]

        if isinstance(image, str):
            image = pillow_from_any_string(image)
        elif isinstance(image, Image.Image):
            image = image
        else:
            return {"image": None}

        image = image.copy()
        image.thumbnail((max_width, max_height))

        return {"image": image}
    
class ImagesThumbnail(BaseNode):
    def __init__(self):
        super().__init__()
        self.set_default_input("images", [])
        self.set_default_input("max_width", 300)
        self.set_default_input("max_height", 300)
    
    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "images": MultipleAttributeDefinition(types=[StringAttributeDefinition(), ListAttributeDefinition(StringAttributeDefinition()), AttributeDefinition(type_name="image"), ListAttributeDefinition(AttributeDefinition(type_name="image") )]),
            "max_width": IntegerAttributeDefinition(min_value=1),
            "max_height": IntegerAttributeDefinition(min_value=1)
        }
    
    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return {"images": ListAttributeDefinition(AttributeDefinition(type_name="image"))}
    
    @classmethod
    def name(cls) -> str:
        return "Images Thumbnail"
    
    @classmethod
    def category(cls) -> str:
        return "Misceallaneous"
    
    def run(self, **kwargs) -> dict:
        images = kwargs["images"]
        max_width = kwargs["max_width"]
        max_height = kwargs["max_height"]

        if isinstance(images, list):
            images = [pillow_from_any_string(image) if isinstance(image, str) else image for image in images]
        else:
            images = [pillow_from_any_string(images) if isinstance(images, str) else images]

        images = [image.copy() for image in images]
        for i, image in enumerate(images):
            image.thumbnail((max_width, max_height))
            images[i] = image

        return {"images": images}
    


class DrawBbox(BaseNode):
    def __init__(self):
        super().__init__()

        self.__output_defintions = {
            "images": MultipleAttributeDefinition(
                types=[
                    StringAttributeDefinition(),
                    ListAttributeDefinition(StringAttributeDefinition()),
                    AttributeDefinition(type_name="image"), 
                    ListAttributeDefinition(AttributeDefinition(type_name="image"))]),
            "bboxes": MultipleAttributeDefinition(types=[AttributeDefinition(type_name="bbox"), ListAttributeDefinition(AttributeDefinition(type_name="bbox")), ListAttributeDefinition(ListAttributeDefinition(AttributeDefinition(type_name="bbox")))]),
            "labels": MultipleAttributeDefinition(types=[StringAttributeDefinition(), ListAttributeDefinition(StringAttributeDefinition()), ListAttributeDefinition(ListAttributeDefinition(StringAttributeDefinition()))]),
        }

        self._on_input_connected += self.__on_input_connected
        self._on_input_disconnected += self.__on_input_disconnected

        self.set_default_input("images", [])
        self.set_default_input("bboxes", [])
        self.set_default_input("labels", [])


    def __on_input_connected(self, input_name: str, output_node: BaseNode, output_name: str):
        if input_name == "images":
            self.__output_defintions["images"] = output_node.output_definitions[output_name].copy()
            self.__output_defintions["images"].kind = AttributeKind.VALUE
            self.refresh_ui()
        elif input_name == "bboxes":
            self.__output_defintions["bboxes"] = output_node.output_definitions[output_name].copy()
            self.__output_defintions["bboxes"].kind = AttributeKind.VALUE
            self.refresh_ui()
        elif input_name == "labels":
            self.__output_defintions["labels"] = output_node.output_definitions[output_name].copy()
            self.__output_defintions["labels"].kind = AttributeKind.VALUE
            self.refresh_ui()
        
    def __on_input_disconnected(self, input_name: str, _, __):
        if input_name == "images":
            self.__output_defintions["images"] = MultipleAttributeDefinition(
                types=[
                    StringAttributeDefinition(),
                    ListAttributeDefinition(StringAttributeDefinition()),
                    AttributeDefinition(type_name="image"), 
                    ListAttributeDefinition(AttributeDefinition(type_name="image"))])
            self.refresh_ui()
        elif input_name == "bboxes":
            self.__output_defintions["bboxes"] = MultipleAttributeDefinition(types=[AttributeDefinition(type_name="bbox"), ListAttributeDefinition(AttributeDefinition(type_name="bbox")), ListAttributeDefinition(ListAttributeDefinition(AttributeDefinition(type_name="bbox")))])
            self.refresh_ui()
        elif input_name == "labels":
            self.__output_defintions["labels"] = MultipleAttributeDefinition(types=[StringAttributeDefinition(), ListAttributeDefinition(StringAttributeDefinition()), ListAttributeDefinition(ListAttributeDefinition(StringAttributeDefinition()))])
            self.refresh_ui()
    
    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "images": MultipleAttributeDefinition(types=[
                StringAttributeDefinition(),
                ListAttributeDefinition(StringAttributeDefinition()),
                AttributeDefinition(type_name="image"), 
                ListAttributeDefinition(AttributeDefinition(type_name="image"))]),
            "bboxes": MultipleAttributeDefinition(types=[AttributeDefinition(type_name="bbox"), ListAttributeDefinition(AttributeDefinition(type_name="bbox")), ListAttributeDefinition(ListAttributeDefinition(AttributeDefinition(type_name="bbox")))]),
            "labels": MultipleAttributeDefinition(types=[StringAttributeDefinition(), ListAttributeDefinition(StringAttributeDefinition()), ListAttributeDefinition(ListAttributeDefinition(StringAttributeDefinition()))]),
            }
    
    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return self.__output_defintions
    
    @classmethod
    def name(cls) -> str:
        return "Draw Bounding Box"
    
    @classmethod
    def category(cls) -> str:
        return "Misceallaneous"
    
    def __draw_bbox(self, image: Image.Image, bboxes: list[list[int]], labels: list[str]) -> Image.Image:
        image = image.copy()
        draw = ImageDraw.Draw(image)
        if isinstance(bboxes[0], int):
            bboxes = [bboxes]
            labels = [labels]

        for i in range(len(bboxes)):
            bbox = bboxes[i]
            label = labels[i]
            draw.rectangle(bbox, outline="red", width=2)
            draw.text((bbox[0], bbox[1]), label, fill="red")

        return image
    
    def run(self, **kwargs) -> dict[str, object]:

        images = kwargs["images"]
        bboxes = kwargs["bboxes"]
        labels = kwargs["labels"]


        if isinstance(images, list):
            images = [helpers.pillow_from_any_string(image) if isinstance(image, str) else image for image in images]
        else:
            images = [helpers.pillow_from_any_string(images) if isinstance(images, str) else images]

        if bboxes == None or len(bboxes) == 0:
            bboxes = [0, 0, 1, 1]
        if isinstance(bboxes[0], int):
            bboxes = [bboxes for _ in range(len(images))]
        if len(bboxes) != len(images):
            bboxes = [bboxes]*len(images)

        if labels == None or len(labels) == 0:
            labels = ""
        if isinstance(labels, str):
            labels = [labels for _ in range(len(images))]
        if len(labels) != len(images):
            labels = [labels]*len(images)

        result_images = []
        for i in range(len(images)):
            result_images.append(self.__draw_bbox(images[i], bboxes[i], labels[i]))

        return {"images": result_images, "bboxes": bboxes, "labels": labels}