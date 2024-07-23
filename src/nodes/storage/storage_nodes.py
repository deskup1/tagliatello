from typing import Any
import os
from ...graph import BaseNode, StringAttributeDefinition, AttributeDefinition, FileAttributeDefinition


class SetStorageItem(BaseNode):

    def __init__(self):
        super().__init__()
        self.set_default_input("storage", "")
        self.set_default_input("key", "")
        self.set_default_input("value", "")

    @classmethod
    def name(cls):
        return "Set Storage Item"
    
    @classmethod
    def category(cls):
        return "Storage"
    
    @property
    def input_definitions(self):
        return {
            "storage": AttributeDefinition(type_name="storage"),
            "key": StringAttributeDefinition(),
            "value": StringAttributeDefinition()
        }
    
    @property
    def output_definitions(self):
        return {
            "storage": AttributeDefinition(type_name="storage"),
            "key": StringAttributeDefinition(),
            "value": StringAttributeDefinition()
        }
    
    def run(self, storage, key, value):
        storage[key] = value
        return {
            "storage": storage,
            "key": key,
            "value": value
        }
    
class GetStorageItem(BaseNode):

    def __init__(self):
        super().__init__()
        self.set_default_input("storage", "")
        self.set_default_input("key", "")

    @classmethod
    def name(cls):
        return "Get Storage Item"
    
    @classmethod
    def category(cls):
        return "Storage"
    
    @property
    def input_definitions(self):
        return {
            "storage": AttributeDefinition(type_name="storage"),
            "key": StringAttributeDefinition()
        }
    
    @property
    def output_definitions(self):
        return {
            "storage": AttributeDefinition(type_name="storage"),
            "key": StringAttributeDefinition(),
            "value": StringAttributeDefinition(),
        }
    
    def run(self, **kwargs):
        storage = kwargs.get("storage")
        key = kwargs.get("key")
        value = storage.get(key)
        return {
            "storage": storage,
            "key": key,
            "value": value
        }