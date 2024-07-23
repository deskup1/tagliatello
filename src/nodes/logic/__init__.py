from .logic_nodes import SwitchNode, IteratorNode, CollectorNode, LoopNode, IfElseNode, IsNullNode, IsNullOrEmptyNode, ConnectorNode, ReplaceNode, WaitForAllInputs

def register_nodes():
    return [SwitchNode, IteratorNode, CollectorNode, LoopNode, IfElseNode, IsNullNode, IsNullOrEmptyNode, ConnectorNode, ReplaceNode, WaitForAllInputs]