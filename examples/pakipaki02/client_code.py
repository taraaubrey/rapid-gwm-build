# %% create a template modules (this would normally be done based on a template file)
import logging

from rapid_gwm_build import create_simulation
from rapid_gwm_build.parsers.config_parser import ConfigParser

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
from rapid_gwm_build.simulation import Simulation

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
    
    # Dictionary to store all nodes for this simulation
    sim_nodes = {}
    
    # loop through simulation block and create node_cfgs
    for key, val in sim_cfg.items():
        print(f"  Parsing {key} configuration...")
        
        # Use the refactored parser - much cleaner!
        parser.parse_node(node_type=key, config=val)
        
    # Collect all created nodes for this simulation
    all_nodes = parser.get_all_nodes()
    sim_nodes = {node.ref_id: node for node in all_nodes}
    
    print(f"  Total nodes created for {sim_name}: {len(sim_nodes)}")
    
    # Store simulation configuration
    all_sims[sim_name] = {
        "sim_type": sim_cfg["sim_type"],  # e.g., 'mf6'
        "ws": sim_cfg["ws"],  # Working directory
        "nodes": sim_nodes  # All created nodes with dependencies
    }
    
    # Clear parser for next simulation
    parser.clear_all_nodes()


        #     if node_type == 'mesh':
        #         NodeParser.parse_mesh(type_cfg)
        #     elif node_type == 'modules':
        #         NodeParser.parse_modules(type_cfg)
        #     elif node_type == 'pipes':
        #         NodeParser.parse_pipe(**type_cfg)

        # return {n.id: n for n in node_manager.nodes}


        
    #     # Flatten modules and input nodes
    #     node_cfgs = cls._get_node_cfg(sim_cfg)
    #     all_sims[sim_name] = {
    #         "sim_type": sim_cfg["sim_type"],  # e.g., 'mf6'
    #         "ws": sim_cfg["ws"],  # Working directory
    #         "nodes": node_cfgs  # Extracted nodes (modules + inputs)
    #     }
    # # for sim_name, sim_cfg in parsed.items():
    #     # set working directory
    #     ref_dir = Path(sim_cfg['ws']) / 'ref_data'
    #     derived_dir = Path(sim_cfg['ws']).parent /'derived_data'
    #     # create the dir
    #     ref_dir.mkdir(parents=True, exist_ok=True)
    #     derived_dir.mkdir(parents=True, exist_ok=True)

    #     sim = Simulation.from_config(sim_name, sim_cfg, ref_dir=ref_dir, derived_dir=derived_dir) #TODO: for each 



    # # sim.graph.plot()

    # # print(here)
    # # sim.build()
    # sim.build()

    # sim.write()

    # print('done')


if __name__ == "__main__":
    main()