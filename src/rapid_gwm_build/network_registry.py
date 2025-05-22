
import networkx as nx

from rapid_gwm_build.nodes.node_base import NodeCFG
from rapid_gwm_build.pipes.pipeline_node import PipelineNode

class NetworkRegistry:
    def __init__(self):
        """Initialize the NetworkRegistry with an empty directed graph."""
        self._graph = nx.DiGraph()

        self._allowed_types = [
            'input',
            'mesh',
            'temporal',
            'template',
            'module',
            "pipe",
            'data',
        ]

    
    @property
    def subgraph(self):
        module_nodes = [n_id for n_id, data in self._graph.nodes.data() if data['node'].type == 'module']
        
        def get_adj_nodes(in_list, master_nodes):
            
            for n_id in in_list:
                adj_nodes = list(self._graph.predecessors(n_id))
                master_nodes.extend(adj_nodes)
                master_nodes = get_adj_nodes(adj_nodes, master_nodes)
            return master_nodes
        
        master_nodes = get_adj_nodes(module_nodes, module_nodes)

        # get unique
        subset_nodes = list(dict.fromkeys(master_nodes))
        return self._graph.subgraph(subset_nodes)

    
    def plot(self, subgraph=False, **kwargs):
        from matplotlib import pyplot as plt

        if subgraph:
            G = self.subgraph
        else:
            G = self._graph

        node_colors = {
            "input": "yellow",
            "mesh": "purple",
            "module": "lightblue",
            "pipe": "pink",
            "template": "orange",
            "pipeline": "lightgreen",
            'placeholder': "gray",}
        line_color = {
            True: 0.5,
        }

        pos = nx.planar_layout(G)  # positions for all nodes

        color_list = []
        template_list = []
        for node in G.nodes(data=True):
            color_list.append(node_colors.get(node[1]['node'].type, "gray"))
            template_list.append(line_color.get(node[1]['node'].istemplate(), 1))
        labels = {node: data['node'].name for node, data in G.nodes(data=True)}

        nx.draw_networkx(
            G,
            pos=pos,
            with_labels=False,
            node_color=color_list,
            alpha=template_list,
        )
        nx.draw_networkx_labels(G, pos=pos, labels=labels, font_size=8, font_color="black")
        plt.show()
    
    def add_node(self, ncfg: NodeCFG):
        """
        Add a node to the graph with optional attributes.
        :param node: The node identifier (e.g., a string or number).
        :param attributes: Additional attributes to associate with the node.
        """
        self._graph.add_node(ncfg.id, node=ncfg)

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