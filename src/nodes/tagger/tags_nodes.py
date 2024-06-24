from ...graph import BaseNode, AttributeDefinition, BoolenAttributeDefinition, StringAttributeDefinition, DictAttributeDefinition, FloatAttributeDefinition, ComboAttributeDefinition
import os


class FindCaretFilesNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.set_default_input("caret_file_extension", ".txt")
        self.set_default_input("on_missing_files", "error")

    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "files": StringAttributeDefinition(list=True),
            "caret_file_extension": StringAttributeDefinition(),
            "on_missing_files": ComboAttributeDefinition(lambda: ["error", "skip", "empty"], allow_custom=False)
        }
    
    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "files": StringAttributeDefinition(list=True),
            "caret_files": StringAttributeDefinition(list=True)
        }
    
    @classmethod
    def name(cls) -> str:
        return "Find Caret Files"
    
    @classmethod
    def category(cls) -> str:
        return "Tags"
    
    def run(self, **kwargs) -> dict[str, object]:
        files = kwargs["files"]
        caret_file_extension = kwargs["caret_file_extension"]

        if len(caret_file_extension) != 0 and caret_file_extension[0] != ".":
            caret_file_extension = "." + caret_file_extension

        on_missing_files = kwargs["on_missing_files"]

        # get directories of files and find files with the same name but with caret_file_extension
        caret_files = []
        other_files = []
        for file in files:
            directory = os.path.dirname(file)
            basename = os.path.basename(file)
            file_name, _ = os.path.splitext(basename)
            caret_file = os.path.join(directory, file_name + caret_file_extension)
            if os.path.exists(caret_file):
                other_files.append(file)
                caret_files.append(caret_file)
            elif on_missing_files == "error":
                raise ValueError(f"Missing caret file for {file}")
            elif on_missing_files == "skip":
                continue
            elif on_missing_files == "empty":
                other_files.append(file)
                caret_files.append("")

        return {
            "files": other_files,
            "caret_files": caret_files
        }

class JoinTagsNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.set_default_input("value_mode", "max")
        self.set_default_input("position", "after")
        self.set_default_input("tags1", [])
        self.set_default_input("tags2", [])

    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "tags1": DictAttributeDefinition(key_type=StringAttributeDefinition(), value_type=FloatAttributeDefinition(), list=True),
            "tags2": DictAttributeDefinition(key_type=StringAttributeDefinition(), value_type=FloatAttributeDefinition(), list=True),
            "value_mode": ComboAttributeDefinition(lambda: ["sum", "max", "min", "average", "replace", "skip"], allow_custom=False),
            "position": ComboAttributeDefinition(lambda: ["before", "after", "alphabetical desc", "alphabetical asc", "value desc", "value asc"])
        }
    
    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "tags": DictAttributeDefinition(key_type=StringAttributeDefinition(), value_type=FloatAttributeDefinition(), list=True)
        }
    
    @classmethod
    def name(cls) -> str:
        return "Join Tags"
    
    @classmethod
    def category(cls) -> str:
        return "Tags"
    
    def run(self, **kwargs) -> dict[str, object]:
            
            tags_list1 = kwargs.get("tags1", [])
            tags_list2 = kwargs.get("tags2", [])

            if not isinstance(tags_list1, list) or not isinstance(tags_list2, list):
                raise ValueError("Tags must be a list of dictionaries")

            if len(tags_list1) != len(tags_list2):
                raise ValueError("Tags lists must have the same length")
        

            value_mode = kwargs.get("value_mode", "sum")
            position = kwargs.get("position", "after")
    
            tags_list = []


            tags = zip(tags_list1, tags_list2)

            for tags1, tags2 in tags:
                tags = {}
                for tag, value in tags1.items():
                    if tag in tags2:
                        if value_mode == "sum":
                            tags[tag] = value + tags2[tag]
                        elif value_mode == "max":
                            tags[tag] = max(value, tags2[tag])
                        elif value_mode == "min":
                            tags[tag] = min(value, tags2[tag])
                        elif value_mode == "average":
                            tags[tag] = (value + tags2[tag]) / 2
                        elif value_mode == "replace":
                            tags[tag] = tags2[tag]
                        elif value_mode == "skip":
                            continue
                    else:
                        if position == "before":
                            tags = {tag: value, **tags}
                        else:
                            tags[tag] = value

                tags_list.append(tags)

            asc = position.endswith("asc")
            if position.startswith("alphabetical"):
                tags_list = sorted(tags_list, key=lambda x: list(x.keys())[0], reverse=asc)
            elif position.startswith("value"):
                tags_list = sorted(tags_list, key=lambda x: list(x.values())[0], reverse=asc)

            return {
                "tags": tags_list
            }
    
class ConvertTagsToStringNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.set_default_input("normalize_tags", True)
        self.set_default_input("keep_values", False)
        self.set_default_input("sort_mode", "value desc")

    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "tags": DictAttributeDefinition(key_type=StringAttributeDefinition(), value_type=FloatAttributeDefinition(), list=True),
            "normalize_tags": BoolenAttributeDefinition(),
            "keep_values": BoolenAttributeDefinition(),
            "sort_mode": ComboAttributeDefinition(lambda: ["none", "alphabetical desc", "alphabetical asc", "value desc", "value asc"], allow_custom=False)
        }
    
    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "tags_string": StringAttributeDefinition(list=True)
        }
    
    @classmethod
    def name(cls) -> str:
        return "Convert Tags To String"
    
    @classmethod
    def category(cls) -> str:
        return "Tags"
    
    def __normalize_tag(self, tag: str) -> str:
            return tag.replace("_", " ").replace("(", "\(").replace(")", "\)")
    
    def __parse_tag(self, tag: tuple[str, float], normalize = True, keep_values = True) -> str:
        if normalize:
            tag = self.__normalize_tag(tag[0])
        else:
            tag = tag[0]

        if keep_values:
            return f"({tag}:{tag[1]})"
        return tag


    def run(self, **kwargs) -> dict[str, object]:
            
        tags_list: list[dict] = kwargs.get("tags", [])
        sort_mode = kwargs.get("sort_mode", "value desc")
        sort, mode = sort_mode.split(" ")

        normalize_tags = kwargs.get("normalize_tags", True)
        keep_values = kwargs.get("keep_values", False)

        tags_string = []
        for tags in tags_list:
            tags = list(tags.items())
            if sort == "alphabetical":
                tags = sorted(tags, key=lambda x: x[0], reverse=mode == "desc")
            elif sort == "value":
                tags = sorted(tags, key=lambda x: x[1], reverse=mode == "desc")
            tags_string.append(", ".join([self.__parse_tag(tag, normalize_tags, keep_values) for tag in tags]))

        return {
            "tags_string": tags_string
        }

class LoadTagsFromFilesNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.set_default_input("on_missing_files", "error")
        self.set_default_input("normalize_tags", True)
        self.set_default_input("default_value", 1)
        self.set_default_input("files", [])

    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "files": StringAttributeDefinition(list=True),
            "on_missing_files": ComboAttributeDefinition(lambda: ["error", "skip", "empty"], allow_custom=False),
            "normalize_tags": BoolenAttributeDefinition(),
            "default_value": FloatAttributeDefinition(),
        }
    
    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "files": StringAttributeDefinition(list=True),
            "tags": DictAttributeDefinition(key_type=StringAttributeDefinition(), value_type=FloatAttributeDefinition(), list=True)
        }
    
    @classmethod
    def name(cls) -> str:
        return "Load Tags From Files"
    
    @classmethod
    def category(cls) -> str:
        return "Tags"
    
    def __normalize_tag(self, tag: str) -> str:
        if self.static_inputs["normalize_tags"]:
            return tag.replace("_", " ").replace("(", "\(").replace(")", "\)")
        return tag


    def __parse_tag(self, tag: str, default_value = 1.0) -> tuple[str, float]:

        tag = tag.strip()

        if not tag.startswith("(") or not tag.endswith(")"):
            return tag, default_value
        
        # drop '(' and ')' if are present
        while tag.startswith("(") and tag.endswith(")"):
            tag = tag[1:-1]
            default_value *= 1.2

        # if ends with :float_str, extract the float and use it as value
        if tag.endswith(":"):
            return self.__normalize_tag(tag[:-1]), default_value
        
        if ":" in tag:
            tag, value = tag.split(":")
            try:
                value = float(value)
            except ValueError:
                value = default_value

            return tag, self.__normalize_tag(value)
    
    def run(self, **kwargs) -> dict[str, object]:

        files = kwargs.get("files", [])
        files_tags = []

        on_missing_files = kwargs.get("on_missing_files", "error")
        other_files = []

        default_value = kwargs.get("default_value", 1.0)

        for file in files:
            if not os.path.exists(file):
                if on_missing_files == "error":
                    raise ValueError(f"Missing file: {file}")
                elif on_missing_files == "skip":
                    continue
                elif on_missing_files == "empty":
                    other_files.append(file)
                    files_tags.append({})
                    continue
            else:
                other_files.append(file)

            with open(file, "r") as f:
                # split by new line and by comma
                tags = f.read().split("\n")
                tags = [tag.split(",") for tag in tags]
                # flatten the list
                tags = [tag for sublist in tags for tag in sublist]
                tags = [self.__parse_tag(tag, default_value) for tag in tags]
            
            files_tags.append(dict(tags))

        return {
            "files": other_files,
            "tags": files_tags
        }
                

class FilterFilesByTagNode(BaseNode):
    def __init__(self):

        super().__init__()

        self.set_default_input("tag_key", "tag")
        self.set_default_input("tag_value", 0)
        self.set_default_input("filter_mode", "less")


    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "images": StringAttributeDefinition(list=True),
            "tags": DictAttributeDefinition(key_type=StringAttributeDefinition(), value_type=FloatAttributeDefinition(), list=True),
            "tag_key": StringAttributeDefinition(),
            "tag_value": FloatAttributeDefinition(),
            "filter_mode": ComboAttributeDefinition(lambda: ["greater", "less", "equal", "not equal"], allow_custom=False)
        }
    
    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "remaining_images": StringAttributeDefinition(list=True),
            "remaining_images_tags": DictAttributeDefinition(key_type=StringAttributeDefinition(), value_type=FloatAttributeDefinition(), list=True),
            "filtered_images": StringAttributeDefinition(list=True),
            "filtered_images_tags": DictAttributeDefinition(key_type=StringAttributeDefinition(), value_type=FloatAttributeDefinition(), list=True)
        }
    
    @classmethod
    def name(cls) -> str:
        return "Filter Files By Tag"
    
    @classmethod
    def category(cls) -> str:
        return "Tags"
    
    def run(self, **kwargs) -> dict[str, object]:

        images = kwargs.get("images", [])
        tags = kwargs.get("tags", {})

        if len(images) != len(tags):
            raise ValueError("Images and tags must have the same length")

        tag_key = kwargs.get("tag_key", "tag")
        tag_value = kwargs.get("tag_value", 0)
        filter_mode = kwargs.get("filter_mode", "less")

        remaining_images = []
        remaining_images_tags = []
        filtered_images = []
        filtered_images_tags = []

        for image, tag in zip(images, tags):
            if tag_key not in tag:
                raise ValueError(f"Tag key {tag_key} not found in tags")

            if filter_mode == "greater" and tag[tag_key] > tag_value:
                filtered_images.append(image)
                filtered_images_tags.append(tag)
            elif filter_mode == "less" and tag[tag_key] < tag_value:
                filtered_images.append(image)
                filtered_images_tags.append(tag)
            elif filter_mode == "equal" and tag[tag_key] == tag_value:
                filtered_images.append(image)
                filtered_images_tags.append(tag)
            elif filter_mode == "not equal" and tag[tag_key] != tag_value:
                filtered_images.append(image)
                filtered_images_tags.append(tag)
            else:
                remaining_images.append(image)
                remaining_images_tags.append(tag)

        return {
            "remaining_images": remaining_images,
            "remaining_images_tags": remaining_images_tags,
            "filtered_images": filtered_images,
            "filtered_images_tags": filtered_images_tags
        }
