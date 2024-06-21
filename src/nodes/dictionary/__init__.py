from .basic_dictionary_nodes import JoinDictionaryNode, DictionaryValueNode, FilterDictionarByValueNode, DictionaryItemsNode

def register_nodes():
    return [DictionaryValueNode, JoinDictionaryNode, FilterDictionarByValueNode, DictionaryItemsNode]