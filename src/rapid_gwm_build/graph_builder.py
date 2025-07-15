from typing import Set
from .nodes.node_data import NodeData
import networkx as nx

class GraphBuilder:
    def __init__(self, node_data: Set[NodeData]):
        """Initialize the NetworkRegistry with an empty directed graph."""
        self.node_data = node_data
        self.graph = nx.DiGraph()
   
    @property
    def node_ids(self):
        """Get a list of node IDs in the graph."""
        return [node.id for node in self.node_data]
    
    def plot(self, subgraph=False, **kwargs):
        from matplotlib import pyplot as plt
        if subgraph:
            G = self.get_subgraph()
        else:
            G = self.graph

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
    
    
    def build(self) -> nx.DiGraph:
        self._add_nodes()
        self._add_edges()
        self._validate()
        
        return self.graph
    
    def _add_nodes(self):
        for node in self.node_data:
            self._add_node(node)
    
    def _add_node(self, node=None):
        if not isinstance(node, NodeData):
            raise TypeError("Node must be an instance of NodeData.")

        node_id = node.get("id")
        node_type = node.get("node_type")

        if self.graph.has_node(node.id):
            raise ValueError(f"Node with id '{node_id}' already exists in the graph.")
        if not node_id:
            raise ValueError(f"Node '{node_id}' is missing required fields: 'id'.")
        if not node_type:
            raise ValueError(f"Node '{node_id}' is missing required fields: 'node_type'.")
        
        self.graph.add_node(node_id, node_data=node, ntype=node_type)
        
    
    def _add_edges(self):
        for node in self.node_data:
            dependencies = node.get("dependencies", [])
            for dep_id in dependencies:
                if dep_id not in self.node_ids:
                    raise ValueError(f"Missing dependency '{dep_id}' for node '{node.id}'")
                self.graph.add_edge(dep_id, node.id)

    def _validate(self):
        if not nx.is_directed_acyclic_graph(self.graph):
            raise ValueError(f"Graph contains cycles:\n{list(nx.simple_cycles(self.graph))}")


    def __repr__(self):
        return f"GraphBuilder({len(self._graph.nodes)} nodes, {len(self._graph.edges)} edges)"
      
    def get_subgraph(self, ntype='module'):
        # get all module type nodes
        module_ids = [
            node_id for node_id, data in self.graph.nodes(data=True) if (data.get("node_data")) and (data.get('ntype') == ntype)
            ]
        
        ancestor_ids = set()
        for node_id in module_ids:
            # get all descendants of the module node
            ancestor_ids.update(nx.ancestors(self.graph, node_id))

        subgraph_ids = ancestor_ids.union(module_ids)

        return self.graph.subgraph(subgraph_ids).copy()