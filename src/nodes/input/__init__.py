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
)
from .folder_nodes import FilesFromFolderNode, MoveFilesToFolderNode, CopyFilesToFolderNode
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
            CopyFilesToFolderNode
            ]
            