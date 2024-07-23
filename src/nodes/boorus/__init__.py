from .get_wiki import DanbooruWikiNode
from .booru_download import BooruDownloadNode

def register_nodes():
    return [
        DanbooruWikiNode,
        BooruDownloadNode
    ]