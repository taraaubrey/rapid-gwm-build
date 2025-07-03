import networkx as nx
from typing import List, Dict, Any
import logging

logging.getLogger('matplotlib').setLevel(logging.WARNING)
# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Set the minimum logging level
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),  # Handler for console output
        logging.FileHandler("my_log.log"),  # Handler for file output
    ],
)

from rapid_gwm_build.parsers.config_parser import ConfigParser
from rapid_gwm_build.parsers.node_parser import NodeParser


def create_dependency_graph(all_nodes: List[Dict[str, Any]]) -> nx.DiGraph:
    """
    Create a NetworkX directed graph representing node dependencies.
    
    Args:
        all_nodes: List of node dictionaries from parser
        
    Returns:
        NetworkX DiGraph with nodes and dependency edges
    """
    G = nx.DiGraph()
    
    # First pass: Add all nodes
    node_ids = set()
    for node in all_nodes:
        node_id = node['id']
        node_ids.add(node_id)
        
        # Add node with comprehensive attributes
        G.add_node(
            node_id,
            type=node['type'],
            context_path='.'.join(node.get('context_path', [])),
            config_summary=str(node.get('config', {}))[:100] + "..." if len(str(node.get('config', {}))) > 100 else str(node.get('config', {})),
            schema_validated=node.get('schema_validated', False),
            parsed_at=node.get('parser_metadata', {}).get('parsed_at', 'unknown'),
            **{k: v for k, v in node.get('parser_metadata', {}).items() 
               if k not in ['parsed_at'] and isinstance(v, (str, int, float, bool))}
        )
    
    # Second pass: Add edges with validation
    missing_dependencies = []
    for node in all_nodes:
        node_id = node['id']
        dependencies = node.get('dependencies', [])
        
        for dep_id in dependencies:
            if dep_id in node_ids:
                # Add edge from dependency to dependent node
                G.add_edge(dep_id, node_id, 
                          relationship='depends_on',
                          created_by='parser')
            else:
                missing_dependencies.append((node_id, dep_id))
    
    # Report missing dependencies
    if missing_dependencies:
        print(f"Warning: Found {len(missing_dependencies)} missing dependencies:")
        for node_id, missing_dep in missing_dependencies[:5]:  # Show first 5
            print(f"  {node_id} depends on missing {missing_dep}")
    
    return G


def main():

    input_yaml = r"examples\pakipaki02\pakipaki_v0.yaml"

    # create directory structure
    from pathlib import Path

    # folder structure preprocessing/node_data
    Path("preprocessing").mkdir(parents=True, exist_ok=True)
    Path("preprocessing/node_data").mkdir(parents=True, exist_ok=True)

    
    config = ConfigParser.parse(input_yaml)
    all_sims = {}
    
    # Initialize the refactored parser
    parser = NodeParser(sim_template=config.get("template", {}))

    # Process each simulation block
    sim_cfg = config.get("simulation", {})
    setup = sim_cfg.pop('setup', {})

    print(f"Processing simulation...")
    
    # loop through simulation block and create node_cfgs
    for key, val in sim_cfg.items():
        print(f"  Parsing {key} configuration...")
        
        # Parse config into nodes
        parser.parse_node(node_type=key, config=val)
        
    # Collect all created nodes for this simulation
    all_nodes = parser.get_all_nodes()
    
    print(f"  Total nodes created: {len(all_nodes)}")

    # CREATE THE GRAPH
    print("Creating dependency graph...")
    G = create_dependency_graph(all_nodes)
    
    print(f"Graph created with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
    
    # Graph analysis
    print("\nGraph Analysis:")
    print(f"  - Nodes: {G.number_of_nodes()}")
    print(f"  - Edges: {G.number_of_edges()}")
    print(f"  - Is DAG: {nx.is_directed_acyclic_graph(G)}")
    
    # Find root nodes (no dependencies)
    root_nodes = [n for n in G.nodes() if G.in_degree(n) == 0]
    print(f"  - Root nodes: {len(root_nodes)}")
    
    # Find leaf nodes (nothing depends on them)
    leaf_nodes = [n for n in G.nodes() if G.out_degree(n) == 0]
    print(f"  - Leaf nodes: {len(leaf_nodes)}")
    
    # Topological sort (if it's a DAG)
    if nx.is_directed_acyclic_graph(G):
        build_order = list(nx.topological_sort(G))
        print(f"  - Build order determined: {len(build_order)} steps")
    
    return G, all_nodes


    # # sim.graph.plot()

    # # print(here)
    # # sim.build()
    # sim.build()

    # sim.write()

    # print('done')


if __name__ == "__main__":
    main()