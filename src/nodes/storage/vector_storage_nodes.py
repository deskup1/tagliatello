from typing import Any
import os
from ...graph import BaseNode, StringAttributeDefinition, AttributeDefinition, ListAttributeDefinition, IntegerAttributeDefinition, DPG_DEFAULT_INPUT_WIDTH
import chromadb
import uuid
import dearpygui.dearpygui as dpg

class VectorStorage:

    def __init__(self, storage, name):
       
        self.client = chromadb.Client()
        self.storage = self.client.create_collection(name)

        all_keys = storage.all_keys()
        all_values = [storage.get(key) for key in all_keys]

        self.storage.upsert(
            ids=all_keys,
            documents=all_values
        )

    def unload(self):
        self.client.delete_collection(self.storage.name)
        self.storage = None
        self.client = None

    def search(self, query: str, count: int) -> Any:
        results = self.storage.query(n_results=count, query_texts=[query])
        documents = results["documents"][0]
        return documents
    

class VectorStorageNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.set_default_input("storage", None)
        self.vector_storage = None
        self.unload_button = None

    @classmethod
    def name(cls) -> str:
        return "InMemory Vector Storage"
    
    @classmethod
    def category(cls) -> str:
        return "Storage"
    
    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "storage": AttributeDefinition(type_name="storage")
        }
    
    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "vector_storage": AttributeDefinition(type_name="vector_storage")
        }
    
    def run(self, **kwargs) -> dict:
        if self.vector_storage is not None:
            return {"vector_storage": self.vector_storage}
        
        storage = kwargs.get("storage")
        if storage is None:
            raise ValueError("Storage is not provided")
        self.vector_storage = VectorStorage(storage, str(uuid.uuid4()))

        if self.unload_button is not None:
            dpg.show_item(self.unload_button)

        return {"vector_storage": self.vector_storage}
    
    def __unload(self):
        if self.vector_storage is not None:
            self.vector_storage.unload()
            self.vector_storage = None
        if self.unload_button is not None:
            dpg.hide_item(self.unload_button)

    def show_custom_ui(self, parent: int | str):
        dpg.add_button(label="Unload", callback=self.__unload, parent=parent, width=DPG_DEFAULT_INPUT_WIDTH)
        return super().show_custom_ui(parent)
        

class VectorStorageSearchNode(BaseNode):
    def __init__(self):
        super().__init__()
        self.set_default_input("vector_storage", None)
        self.set_default_input("query", "")
        self.set_default_input("count", 1)

    @classmethod
    def name(cls) -> str:
        return "Vector Storage Search"
    
    @classmethod
    def category(cls) -> str:
        return "Storage"
    
    @property
    def input_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "vector_storage": AttributeDefinition(type_name="vector_storage"),
            "query": StringAttributeDefinition(),
            "count": IntegerAttributeDefinition(min_value=1)
        }
    
    @property
    def output_definitions(self) -> dict[str, AttributeDefinition]:
        return {
            "documents": ListAttributeDefinition(value_type=StringAttributeDefinition())
        }
    
    def run(self, **kwargs) -> dict:
        vector_storage = kwargs.get("vector_storage")
        if vector_storage is None:
            raise ValueError("Vector storage is not provided")
        query = kwargs.get("query")
        count = kwargs.get("count")
        results = vector_storage.search(query, count)
        return {"documents": results}


