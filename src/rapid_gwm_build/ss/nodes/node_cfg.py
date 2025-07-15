from __future__ import annotations
from copy import deepcopy
from typing import List

from rapid_gwm_build.nodes.node_base import NodeCFG
from rapid_gwm_build.nodes.ss_node_types import MeshNode, InputNode, ModuleNode, PipeNode, PipelineNode, TemplateNode, PlaceholderNode

class NodeFactory:
    node_type = {
        'mesh': MeshNode,
        'input': InputNode,
        'module': ModuleNode,
        'pipe': PipeNode,
        'pipeline': PipelineNode,
        'template': TemplateNode,
        'placeholder': PlaceholderNode,
    }
    
    @classmethod
    def build_node(
            cls,
            node_type: str,
            attr: List[str] = None,
            **kwargs):
        """
        Simplified factory method to create a NodeCFG instance.
        Removed from_node dependency for cleaner architecture.
        """
        if not isinstance(node_type, str):
            raise ValueError(f"Invalid node_type: {type(node_type)}. Expected str.")
        
        Node = cls.node_type.get(node_type)
        if Node is None:
            raise ValueError(f"Unknown node type: {node_type}")
        
        # Set attribute path directly
        if attr is not None:
            kwargs['attr'] = attr
        
        return Node.create(**kwargs)

    # @classmethod
    # def _update_from_clone(
    #         cls,
    #         new_type: str,
    #         from_node: NodeCFG,
    #         **kwargs):
    #     """
    #     Factory method to create a NodeCFG instance from an existing NodeCFG.
    #     """
    #     if not isinstance(from_node, NodeCFG):
    #         raise ValueError(f"Invalid node configuration: {from_node}. Expected NodeCFG instance.")
        
    #     if new_type != from_node.type:
    #         Node = cls.node_type.get(new_type)
    #         new_ncfg = Node.from_node(from_node, kwargs)
    #     else:
    #         new_ncfg = deepcopy(from_node)
    #         new_ncfg.update(**kwargs)
    #     return new_ncfg
    


