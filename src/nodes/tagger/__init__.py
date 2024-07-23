from .wd14tagger_nodes import Wd14TaggerNode
from .tagger_nodes import TagImageNode
from .anime_aesthetic_classifier_nodes import AnimeAestheticClassifierNode
from .hf_aesthetic_classifier_nodes import HfPipelineAestheticClassifierNode
from .tags_nodes import JoinTagsNode, FindCaretFilesNode, FilterFilesByTagNode, LoadTagsFromFilesNode, ConvertTagsToStringNode, LoadTagsFromStringsNode, FilterTagsByValueNode


def register_nodes():
    return [
        Wd14TaggerNode, 
        TagImageNode, 
        AnimeAestheticClassifierNode, 
        HfPipelineAestheticClassifierNode,
        JoinTagsNode, FindCaretFilesNode, 
        FilterFilesByTagNode, 
        LoadTagsFromFilesNode, 
        ConvertTagsToStringNode,
        LoadTagsFromStringsNode,
        FilterTagsByValueNode
        ]