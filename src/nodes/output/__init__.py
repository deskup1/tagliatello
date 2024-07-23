from .miscellaneous_nodes import DisplayNode, WaitNode, DisplayText, DisplayImage, DrawBbox, ImagesThumbnail, ImageThumbnail, SetVariable, GetVariable, ButtonsNode
from .file_nodes import CopyFileNode, MoveFileNode, SaveToImageFileNode, CopyFilesNode, MoveFilesNode, SaveToTextFileNode, SaveToTextFilesNode, LoadTextFileNode, LoadTextFilesNode

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
        SaveToImageFileNode,
        DisplayText,
        DisplayImage,
        DrawBbox,
        ImagesThumbnail,
        ImageThumbnail,
        SetVariable,
        GetVariable,
        ButtonsNode,
        LoadTextFilesNode,
        LoadTextFileNode,
        ]