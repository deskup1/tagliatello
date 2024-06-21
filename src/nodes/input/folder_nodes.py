from ...graph import BaseNode, AttributeDefinition, FileAttributeDefinition, StringAttributeDefinition, BoolenAttributeDefinition

import os
import pathlib
import dearpygui.dearpygui as dpg

class FilesFromFolderNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.default_inputs = {
            "path": "",
            "allowed_extensions": [],
            "recursive": False
        }
        self.__label = None
    
    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "path": FileAttributeDefinition(directory_selector=True),
            "allowed_extensions": StringAttributeDefinition(list=True),
            "recursive": BoolenAttributeDefinition()
        }
    
    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return {"files": StringAttributeDefinition(list=True)}
    
    @classmethod
    def name(cls) -> str:
        return "Files From Folder"
    
    @classmethod
    def category(cls) -> str:
        return "Input"
    

    def show_custom_ui(self, parent: int | str):
        self.__label = dpg.add_text("", parent=parent)

    def init(self):
        if self.__label is not None and dpg.does_item_exist(self.__label):
            dpg.set_value(self.__label, "")
    
    def run(self, **kwargs) -> dict:
        folder = kwargs.get("path")
        allowed_extensions = kwargs.get("allowed_extensions")
        recursive = kwargs.get("recursive")
        files_in_folder = []

        if not os.path.exists(folder):
            if self.__label is not None:
                dpg.set_value(self.__label, f"Folder '{folder}' does not exist")
            return {"files": []}
        
        if recursive:
            for root, _, files in os.walk(folder):
                for file in files:
                    if len(allowed_extensions) == 0 or pathlib.Path(file).suffix in allowed_extensions:
                        files_in_folder.append(os.path.join(root, file))

        else:
            for file in os.listdir(folder):
                if len(allowed_extensions) == 0 or pathlib.Path(file).suffix in allowed_extensions:
                    files_in_folder.append(os.path.join(folder, file))

        if self.__label is not None:
            dpg.set_value(self.__label, f"{len(files_in_folder)} {'file' if len(files_in_folder) == 1 else 'files'}")

        return {"files": files_in_folder}
    
class MoveFilesToFolderNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.default_inputs = {
            "files": [],
            "folder": ""
        }

    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "files": StringAttributeDefinition(list=True),
            "folder": FileAttributeDefinition(directory_selector=True)
        }
    
    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return {"files": StringAttributeDefinition(list=True)}
    
    @classmethod
    def name(cls) -> str:
        return "Move Files To Folder"
    
    @classmethod
    def category(cls) -> str:
        return "Output"
    
    def run(self, **kwargs) -> dict:
        files = kwargs.get("files")
        folder = kwargs.get("folder")
        moved_files = []

        if not os.path.exists(folder):
            raise ValueError(f"Folder '{folder}' does not exist")
        
        for file in files:
            if not os.path.exists(file):
                raise ValueError(f"File '{file}' does not exist")
            
            moved_file = os.path.join(folder, os.path.basename(file))
            os.rename(file, moved_file)
            moved_files.append(moved_file)
        
        return {"files": moved_files}
    
class CopyFilesToFolderNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.default_inputs = {
            "files": [],
            "folder": ""
        }

    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "files": StringAttributeDefinition(list=True),
            "folder": FileAttributeDefinition(directory_selector=True)
        }
    
    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return {"files": StringAttributeDefinition(list=True)}
    
    @classmethod
    def name(cls) -> str:
        return "Copy Files To Folder"
    
    @classmethod
    def category(cls) -> str:
        return "Output"
    
    def run(self, **kwargs) -> dict:
        files = kwargs.get("files")
        folder = kwargs.get("folder")
        copied_files = []

        if not os.path.exists(folder):
            raise ValueError(f"Folder '{folder}' does not exist")
        
        for file in files:
            if not os.path.exists(file):
                raise ValueError(f"File '{file}' does not exist")
            
            copied_file = os.path.join(folder, os.path.basename(file))
            with open(file, "rb") as f:
                with open(copied_file, "wb") as f2:
                    f2.write(f.read())
            copied_files.append(copied_file)
        
        return {"files": copied_files}