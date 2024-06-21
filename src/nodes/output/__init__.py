from .miscellaneous_nodes import DisplayNode, WaitNode, ConsoleLogsNode, DebugComboBoxNode
from .file_nodes import CopyFileNode, MoveFileNode, SaveToImageFileNode, CopyFilesNode, MoveFilesNode, SaveToTextFileNode, SaveToTextFilesNode

def register_nodes():
    return [
        DisplayNode, 
        WaitNode, 
        ConsoleLogsNode, 
        DebugComboBoxNode, 
        CopyFileNode, 
        CopyFilesNode,
        MoveFileNode,
        MoveFilesNode,
        SaveToTextFileNode,
        SaveToTextFilesNode,
        SaveToImageFileNode
        ]