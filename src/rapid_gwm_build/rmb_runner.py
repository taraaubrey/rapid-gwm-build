import networkx as nx
from copy import deepcopy

from .node_engine import NodeBuildEngine
from .build_context import BuildContext

class RMBRunner:
    def __init__(self, graph: nx.DiGraph, mesh_graph: nx.DiGraph, engine: NodeBuildEngine):
        self.graph = graph
        self.mesh_graph = mesh_graph
        
        self.engine = engine
        self.built = {}
        self.build_context = BuildContext()
    
    def run(self):
        
        if not self.build_context.has_mesh():
            self._build_context()
        
        self._run(self.graph)

    
    def _build_context(self):

        # build mesh config nodes
        self._run(self.mesh_graph)

        # set build_context
        mesh_id = 'mesh.config'
        mesh_grid = deepcopy(self.built[mesh_id].data)
        self.build_context.register_mesh(
            mesh_id=mesh_id,
            mesh_grid=mesh_grid)
    
    
    def _run(self, graph: nx.DiGraph):

        for node_id in nx.topological_sort(graph):
            
            if node_id in self.built:
                continue
            
            node = graph.nodes[node_id].get("parsed_node")
            ntype = graph.nodes[node_id].get("ntype")
            dependency_ids = list(graph.predecessors(node_id))

            dependency_results = {
                dep_id: self.built[dep_id]
                for dep_id in dependency_ids
                }
            
            builder = self.engine.get_builder(ntype)

            result = builder.build(
                node, 
                dependencies=dependency_results,
                build_context=self.build_context
                )
            
            graph.nodes[node_id]["build_result"] = result

            self.built[node_id] = result
                
            print('\t\tBuilt node:', node_id, 'with result:', result.success)