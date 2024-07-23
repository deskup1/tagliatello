from .basic_convert_nodes import (
    ToBooleanNode, 
    ToFloatNode, 
    ToIntegerNode, 
    ToStringNode, 
    JoinStringNode, 
    SplitStringNode,
    ToListNode,
    ToAnyNode,
    SearchAndReplaceNode,
    JoinListsNode,
    FlattenListNode,
    ShuffleListNode,
    ListCountNode,
    ReverseListNode,
    FilterNullListNode,
    FilterNullOrEmptyListNode,
)

def register_nodes():
    return [
        ToBooleanNode, 
        ToFloatNode, 
        ToIntegerNode, 
        ToStringNode, 
        JoinStringNode, 
        SplitStringNode, 
        ToListNode, 
        ToAnyNode,
        SearchAndReplaceNode,
        JoinListsNode,
        FlattenListNode,
        ShuffleListNode,
        ListCountNode,
        ReverseListNode,
        FilterNullListNode,
        FilterNullOrEmptyListNode,
        
        ]