from .folder_storage_node import FolderStorageNode
from .storage_nodes import SetStorageItem, GetStorageItem
from .vector_storage_nodes import VectorStorageNode, VectorStorageSearchNode

def register_nodes():
    return [FolderStorageNode, SetStorageItem, GetStorageItem, VectorStorageNode, VectorStorageSearchNode]