
import networkx as nx

class GraphBuilder:
    def __init__(self, node_list):
        """Initialize the NetworkRegistry with an empty directed graph."""
        self.node_list = node_list
        self.graph = nx.DiGraph()

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
        for node in self.node_list:
            self._add_node(node)
    
    def _add_node(self, node=None, node_id=None, ntype=None):
        if node_id and ntype and not node:
            self.graph.add_node(node_id)
        elif not node:
            raise ValueError("Either 'node' or 'node_id' must be provided.")
        else:
            node_id = node.get("id")
            node_type = node.get("type")

            if self.graph.has_node(node_id):
                raise ValueError(f"Node with id '{node_id}' already exists in the graph.")
            
            self.graph.add_node(node_id, parsed_node=node, ntype=node_type)
        
    def _add_edges(self):
        for node in self.node_list:
            dependencies = node.get("dependencies", [])
            for dep_id in dependencies:
                if dep_id not in [node['id'] for node in self.node_list]:
                    raise ValueError(f"Missing dependency '{dep_id}' for node '{node['id']}'")
                self.graph.add_edge(dep_id, node['id'])

    def _validate(self):
        if not nx.is_directed_acyclic_graph(self.graph):
            raise ValueError("Graph contains cycles.")


    def __repr__(self):
        return f"GraphBuilder({len(self._graph.nodes)} nodes, {len(self._graph.edges)} edges)"
      
    def get_subgraph(self, ntype='module'):
        # get all module type nodes
        module_ids = [
            node_id for node_id, data in self.graph.nodes(data=True) if (data.get("parsed_node")) and (data.get('ntype') == ntype)
            ]
        
        ancestor_ids = set()
        for node_id in module_ids:
            # get all descendants of the module node
            ancestor_ids.update(nx.ancestors(self.graph, node_id))

        subgraph_ids = ancestor_ids.union(module_ids)

        return self.graph.subgraph(subgraph_ids).copy()