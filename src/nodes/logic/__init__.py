from .logic_nodes import SwitchNode, IteratorNode, CollectorNode, LoopNode

def register_nodes():
    return [SwitchNode, IteratorNode, CollectorNode, LoopNode]