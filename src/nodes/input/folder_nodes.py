from ...graph import BaseNode, AttributeDefinition, FileAttributeDefinition, StringAttributeDefinition, BoolenAttributeDefinition

import os
import pathlib
import dearpygui.dearpygui as dpg
import hashlib

class InputFolderNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.set_default_input("path", "")
        self.set_default_input("create_folder", False)
        self.__label = None
    
    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "path": FileAttributeDefinition(directory_selector=True),
            "create_folder": BoolenAttributeDefinition()
            }
    
    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return {"path": StringAttributeDefinition()}
    
    @classmethod
    def name(cls) -> str:
        return "Input Folder"
    
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
        create_folder = kwargs.get("create_folder")

        if not os.path.exists(folder):
            if create_folder:
                os.makedirs(folder)
            elif self.__label is not None:
                dpg.set_value(self.__label, f"Folder '{folder}' does not exist")

        
        if self.__label is not None:
            dpg.set_value(self.__label, f"Folder '{folder}'")
        
        return {"path": folder}
    
class InputFoldersNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.set_default_input("paths", [])
        self.set_default_input("create_folders", False)
        self.__label = None
    
    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {"paths": StringAttributeDefinition(list=True),
                "create_folders": BoolenAttributeDefinition()}
    
    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return {"paths": StringAttributeDefinition(list=True)}
    
    @classmethod
    def name(cls) -> str:
        return "Input Folders"
    
    @classmethod
    def category(cls) -> str:
        return "Input"
    
    def show_custom_ui(self, parent: int | str):
        self.__label = dpg.add_text("", parent=parent)
    
    def init(self):
        if self.__label is not None and dpg.does_item_exist(self.__label):
            dpg.set_value(self.__label, "")
    
    def run(self, **kwargs) -> dict:
        folders = kwargs.get("paths")
        valid_folders = []

        for folder in folders:
            if not os.path.exists(folder):
                if kwargs.get("create_folders"):
                    os.makedirs(folder)
                elif self.__label is not None:
                    dpg.set_value(self.__label, f"Folder '{folder}' does not exist")
                    return {"paths": []}
            
            valid_folders.append(folder)
        
        if self.__label is not None:
            dpg.set_value(self.__label, f"{len(valid_folders)} {'folder' if len(valid_folders) == 1 else 'folders'}")
        
        return {"paths": valid_folders}

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
            if file == None or file == "":
                continue

            if not os.path.exists(file):
                raise ValueError(f"File '{file}' does not exist")
            
            copied_file = os.path.join(folder, os.path.basename(file))
            with open(file, "rb") as f:
                with open(copied_file, "wb") as f2:
                    f2.write(f.read())
            copied_files.append(copied_file)
        
        return {"files": copied_files}
    
class FindDuplicateFilesNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.default_inputs = {
            "files": []
        }

    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "files": StringAttributeDefinition(list=True)
        }
    
    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "remaining_files": StringAttributeDefinition(list=True),
            "duplicates": StringAttributeDefinition(list=True)}
    
    @classmethod
    def name(cls) -> str:
        return "Find Duplicate Files"
    
    @classmethod
    def category(cls) -> str:
        return "Input"
    
    def run(self, **kwargs) -> dict:
        files = kwargs.get("files")
        hashes = set()
        duplicates = []
        remaining_files = []
        
        for file in files:
            if not os.path.exists(file):
                raise ValueError(f"File '{file}' does not exist")
            
            # read files in chunks to avoid memory issues
            with open(file, "rb") as f:
                hasher = hashlib.md5()
                while chunk := f.read(4096):
                    hasher.update(chunk)

                file_hash = hasher.hexdigest()

            if file_hash in hashes:
                duplicates.append(file)
            else:
                hashes.add(file_hash)
                remaining_files.append(file)
        
        return {"remaining_files": remaining_files, "duplicates": duplicates}