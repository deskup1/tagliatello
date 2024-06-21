from .basic_convert_nodes import (
    ToBooleanNode, 
    ToFloatNode, 
    ToIntegerNode, 
    ToStringNode, 
    JoinStringNode, 
    SplitStringNode,
    ToListNode,
    ToAnyNode,
)

def register_nodes():
    return [ToBooleanNode, ToFloatNode, ToIntegerNode, ToStringNode, JoinStringNode, SplitStringNode, ToListNode, ToAnyNode]