
import networkx as nx

from rapid_gwm_build.nodes.node import NodeBase
from rapid_gwm_build.pipeline_node import PipelineNode

class NetworkRegistry:
    def __init__(self):
        """Initialize the NetworkRegistry with an empty directed graph."""
        self._graph = nx.DiGraph()

        self._allowed_types = [
            'input',
            'mesh',
            'temporal',
            'template',
            'modules',
            "pipeline",
            'data',
        ]

    def add_node(self, id, node: NodeBase, **kwargs):
        """
        Add a node to the graph with optional attributes.
        :param node: The node identifier (e.g., a string or number).
        :param attributes: Additional attributes to associate with the node.
        """
        ntype = node.ntype
        if ntype not in self._allowed_types:
            raise ValueError(f"Node type '{ntype}' is not allowed. Allowed types are: {self._allowed_types}.")

        self._graph.add_node(id, ntype=ntype, node=node, **kwargs)

    def remove_node(self, node):
        """
        Remove a node from the graph.
        :param node: The node identifier to remove.
        :raises KeyError: If the node does not exist in the graph.
        """
        if node not in self._graph:
            raise KeyError(f"Node '{node}' does not exist in the graph.")
        self._graph.remove_node(node)

    def add_edge(self, source, target, **attributes):
        """
        Add a directed edge between two nodes with optional attributes.
        :param source: The source node.
        :param target: The target node.
        :param attributes: Additional attributes to associate with the edge.
        """
        self._graph.add_edge(source, target, **attributes)

    def remove_edge(self, source, target):
        """
        Remove a directed edge between two nodes.
        :param source: The source node.
        :param target: The target node.
        :raises KeyError: If the edge does not exist in the graph.
        """
        if not self._graph.has_edge(source, target):
            raise KeyError(f"Edge from '{source}' to '{target}' does not exist in the graph.")
        self._graph.remove_edge(source, target)

    def module_registry(self):
        return [data['module'] for node, data in self._graph.nodes(data=True) if data.get('ntype') == 'module' and 'module' in data]
   
    def list_nodes(self, ntype:str=None):
        """
        Get a list of nodes that have a specific label with a given value.
        :param label: The attribute key to filter nodes by.
        :param value: The attribute value to match.
        :return: A list of nodes that match the label and value.
        """
        if ntype:
            return [node for node, attrs in self._graph.nodes(data=True) if attrs.get('ntype') == ntype]
        else:
            return list(self._graph.nodes)

    def get(self, node):
        """
        Get all attributes of a specific node.
        :param node: The node identifier.
        :return: A dictionary of attributes for the node.
        :raises KeyError: If the node does not exist in the graph.
        """
        if node not in self._graph:
            raise KeyError(f"Node '{node}' does not exist in the graph.")
        return self._graph.nodes[node]

    def list_edges(self):
        """
        List all edges in the graph.
        :return: A list of all edges in the graph.
        """
        return list(self._graph.edges)

    def __repr__(self):
        return f"NetworkRegistry({len(self._graph.nodes)} nodes, {len(self._graph.edges)} edges)"
    
    def add_pipeline_node(self, pnode: PipelineNode):
        # assume input nodes are already in the graph
        self.add_node(pnode.name, ntype="pipeline", data=pnode)
        self._graph.add_edges_from([(pnode.name, ikey) for ikey in pnode.inkeys])
        self._graph.add_edges_from([(pnode.name, ikey) for ikey in pnode.outkeys])