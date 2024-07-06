from .florence2_model_nodes import Florence2ModelCaptionNode, Florence2ModelNode, Florence2ModelRegionDetectionNode, Florence2ModelCaptionGrounding

def register_nodes():
    return [
        Florence2ModelCaptionNode,
        Florence2ModelNode,
        Florence2ModelRegionDetectionNode,
        Florence2ModelCaptionGrounding
    ]