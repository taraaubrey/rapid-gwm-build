from typing import Callable
import networkx as nx


from .config import CONFIG
from .cache import memory
from .node_engine import NodeBuildEngine
from .build_registry import build_registry
from .build_context import build_context

@memory.cache
def execute_node_build(builder: Callable, node: dict) -> dict:
    return builder.build(node)

class RMBRunner:
    def __init__(self, graph: nx.DiGraph, mesh_graph: nx.DiGraph, engine: NodeBuildEngine):
        self.graph = graph
        self.mesh_graph = mesh_graph
        
        self.engine = engine
    
    def run(self):
        
        if not build_context.has_mesh():
            self._register_build_context()
        
        self._compile_graph_node_data(self.graph)

    
    def _register_build_context(self):

        # build mesh config nodes
        self._compile_graph_node_data(self.mesh_graph)

        # set build_context
        mesh_id = 'mesh.config'
        mesh_grid = build_registry.result_from_id(mesh_id).data
        build_context.register_mesh(
            mesh_id=mesh_id,
            mesh_grid=mesh_grid)
    
    
    def _compile_graph_node_data(self, graph: nx.DiGraph):

        for node_id in nx.topological_sort(graph):
            
            if build_registry.has_id(node_id):
                continue
            
            node = graph.nodes[node_id].get("node_data")
            ntype = graph.nodes[node_id].get("ntype")
            
            builder = self.engine.get_builder(ntype)

            if CONFIG.get('cache_nodes', True):
                # Use caching if enabled
                result = execute_node_build(builder, node)
            else:
                # Execute without caching
                result = builder.build(node)
            
            # save to build_registry (important for local fetching in other functions)
            build_registry.register_built_node(node_id, result)
            
            # graph.nodes[node_id]["build_result"] = result

            print('\t\tBuilt node:', node_id, 'with result:', result.success)