from .miscellaneous_nodes import DisplayNode, WaitNode
from .file_nodes import CopyFileNode, MoveFileNode, SaveToImageFileNode, CopyFilesNode, MoveFilesNode, SaveToTextFileNode, SaveToTextFilesNode

def register_nodes():
    return [
        DisplayNode, 
        WaitNode, 
        CopyFileNode, 
        CopyFilesNode,
        MoveFileNode,
        MoveFilesNode,
        SaveToTextFileNode,
        SaveToTextFilesNode,
        SaveToImageFileNode
        ]