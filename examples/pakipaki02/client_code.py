import networkx as nx
from typing import List, Dict, Any
import logging

logging.getLogger('matplotlib').setLevel(logging.WARNING)
logging.getLogger('rasterio').setLevel(logging.WARNING)
logging.getLogger('fiona').setLevel(logging.WARNING)
logging.getLogger('gridit').setLevel(logging.WARNING)
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
from rapid_gwm_build.nodes.parse.node_parser import NodeParser
from rapid_gwm_build.graph_builder import GraphBuilder
from rapid_gwm_build.node_engine import NodeBuildEngine
from rapid_gwm_build.rmb_runner import RMBRunner

from rapid_gwm_build.nodes.builders import discover_builders
from rapid_gwm_build.registries import BUILDER_REGISTRY

def main():

    from rapid_gwm_build.config import CONFIG
    # set cache enabled to False
    CONFIG['cache_enabled'] = False

    input_yaml = r'examples/pakipaki02/pakipaki02.yaml'

    # create directory structure
    from pathlib import Path

    # folder structure preprocessing/node_data
    Path("preprocessing").mkdir(parents=True, exist_ok=True)
    Path("preprocessing/node_data").mkdir(parents=True, exist_ok=True)

    config = ConfigParser.parse(input_yaml)
    
    # Initialize the refactored parser
    parser = NodeParser(sim_template=config.get("template", {}))

    # Process each simulation block
    sim_cfg = config.get("simulation", {})
    setup = sim_cfg.pop('setup', {})

    print(f"\tPrepping: Processing simulation...")
    
    # loop through simulation block and create node_cfgs
    for key, val in sim_cfg.items():
        print(f"\t\tParsing {key} configuration...")
        
        # Parse config into nodes
        parser.parse_node(node_type=key, config=val)
        
    # Collect all created nodes for this simulation
    all_nodes = parser.get_all_nodes()
    print(f"\t\tTotal nodes created: {len(all_nodes)}")

    # CREATE THE GRAPH
    print("\tBuild stage 1: Creating dependency graph...")
    graphbuilder = GraphBuilder(all_nodes)
    G = graphbuilder.build()
    sG = graphbuilder.get_subgraph(ntype='module')
    cG = graphbuilder.get_subgraph(ntype='mesh_config')
    
    print(f"\tBuild stage 2: Creating model files...")
    # the registry on how to build out each node
    engine = NodeBuildEngine(registry=BUILDER_REGISTRY)
    # handles orchestration of the build
    runner = RMBRunner(graph=sG, mesh_graph=cG, engine=engine)
    runner.run()
    

    return

if __name__ == "__main__":
    main()