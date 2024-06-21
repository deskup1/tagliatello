from .wd14tagger_nodes import Wd14TaggerNode
from .tagger_nodes import TagImageNode
from .anime_aesthetic_classifier_nodes import AnimeAestheticClassifierNode
from .tags_nodes import JoinTagsNode, FindCaretFilesNode, FilterFilesByTagNode, LoadTagsFromFilesNode, ConvertTagsToStringNode


def register_nodes():
    return [Wd14TaggerNode, TagImageNode, AnimeAestheticClassifierNode, JoinTagsNode, FindCaretFilesNode, FilterFilesByTagNode, LoadTagsFromFilesNode, ConvertTagsToStringNode]