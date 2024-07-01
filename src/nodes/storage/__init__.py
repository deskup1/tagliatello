from .folder_storage_node import FolderStorageNode
from .storage_nodes import SetStorageItem, GetStorageItem

def register_nodes():
    return [FolderStorageNode, SetStorageItem, GetStorageItem]