from __future__ import annotations
from copy import deepcopy

from rapid_gwm_build.nodes.node_base import NodeCFG
from rapid_gwm_build.nodes.node_types import MeshNode, InputNode, ModuleNode, PipeNode, PipelineNode, TemplateNode, PlaceholderNode

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

    # @property
    # def node_type(self):
    #     """
    #     Returns the node type dictionary.
    #     """
    #     return self._node_type
    
    # @node_type.getter
    # def node_type(self):
    #     """
    #     Returns the node type dictionary.
    #     """
    #     return self._node_type
    
    @classmethod
    def build_node(
            cls,
            node_type: str,
            from_node: NodeCFG=None,
            **kwargs):
        """
        Factory method to create a NodeCFG instance.
        """
        if isinstance(from_node, NodeCFG):
            return cls._update_from_clone(from_node=from_node, new_type=node_type, **kwargs)
        elif isinstance(node_type, str):
            Node = cls.node_type.get(node_type)
            return Node.create(**kwargs)
        else:
            raise ValueError(f"Invalid key type: {type(key)}. Expected str or NodeCFG.")

    @classmethod
    def _update_from_clone(
            cls,
            new_type: str,
            from_node: NodeCFG,
            **kwargs):
        """
        Factory method to create a NodeCFG instance from an existing NodeCFG.
        """
        if not isinstance(from_node, NodeCFG):
            raise ValueError(f"Invalid node configuration: {from_node}. Expected NodeCFG instance.")
        
        if new_type != from_node.type:
            Node = cls.node_type.get(new_type)
            new_ncfg = Node.from_node(from_node, kwargs)
        else:
            new_ncfg = deepcopy(from_node)
            new_ncfg.update(**kwargs)

        return new_ncfg
    


