# from .folder_nodes import FilesFromFolderNode
# from .input_nodes import IntegerNode, FloatNode, StringNode, BooleanNode, ImageNode, CounterNode
from .input_nodes import (
    CounterNode, 
    FileNode, 
    MultiFileNode,
    IntegerNode,
    FloatNode,
    BoolenNode,
    StringNode,
    StringListNode,
    RangeNode,
    FilePathNode,
    SplitFilePathNode,
    Base64ImageNode,
)
from .folder_nodes import FilesFromFolderNode, MoveFilesToFolderNode, CopyFilesToFolderNode, InputFolderNode, InputFoldersNode
def register_nodes():
    return [CounterNode, 
            FileNode, 
            MultiFileNode, 
            IntegerNode, 
            FloatNode, 
            StringNode, 
            StringListNode, 
            BoolenNode,
            FilesFromFolderNode,
            RangeNode,
            FilePathNode,
            SplitFilePathNode,
            MoveFilesToFolderNode,
            CopyFilesToFolderNode,
            InputFoldersNode,
            InputFolderNode,
            Base64ImageNode
            ]
            