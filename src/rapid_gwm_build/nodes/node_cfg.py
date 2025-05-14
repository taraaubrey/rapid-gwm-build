from __future__ import annotations
from copy import deepcopy
from abc import ABC, abstractmethod

from rapid_gwm_build.nodes.node_base import NodeCFG
from rapid_gwm_build.nodes.node_types import MeshNode, InputNode, ModuleNode, PipeNode, PipelineNode

class NodeBuilder:
    def __init__(self):
        self._node_type = {
            'mesh': MeshNode,
            'input': InputNode,
            'module': ModuleNode,
            'pipe': PipeNode,
            'pipeline': PipelineNode
        }

    @property
    def node_type(self):
        """
        Returns the node type dictionary.
        """
        return self._node_type
    
    @node_type.getter
    def node_type(self):
        """
        Returns the node type dictionary.
        """
        return self._node_type
    
    def create(
            self,
            node_type: str,
            ncfg: NodeCFG=None,
            **kwargs):
        """
        Factory method to create a NodeCFG instance.
        """
        if isinstance(ncfg, NodeCFG):
            return self._update_from_clone(old_ncfg=ncfg, new_type=node_type, **kwargs)
        elif isinstance(node_type, str):
            Node = self.node_type.get(node_type)
            return Node.create(kwargs=kwargs)
        else:
            raise ValueError(f"Invalid key type: {type(key)}. Expected str or NodeCFG.")

    
    def _update_from_clone(
            self,
            new_type: str,
            old_ncfg: NodeCFG,
            **kwargs):
        """
        Factory method to create a NodeCFG instance from an existing NodeCFG.
        """
        if not isinstance(old_ncfg, NodeCFG):
            raise ValueError(f"Invalid node configuration: {ncfg}. Expected NodeCFG instance.")
        
        if new_type != old_ncfg.type:
            Node = self.node_type.get(new_type)
            new_ncfg = Node.from_node(old_ncfg, kwargs)
        else:
            new_ncfg = deepcopy(old_ncfg)
            new_ncfg.update(**kwargs)

        return new_ncfg
    


