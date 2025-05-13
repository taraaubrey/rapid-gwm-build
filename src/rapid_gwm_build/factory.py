import os
from pathlib import Path

from rapid_gwm_build.parsers.config_parser import ConfigParser
from rapid_gwm_build.simulation import Simulation


def create_simulation(cfg_filepath: os.PathLike):
    parsed = ConfigParser.parse(cfg_filepath)
    for sim_name, sim_cfg in parsed.items():
        # set working directory
        ref_dir = Path(sim_cfg['ws']) / 'ref_data'
        derived_dir = Path(sim_cfg['ws']).parent /'derived_data'
        
        # create the dir
        ref_dir.mkdir(parents=True, exist_ok=True)
        derived_dir.mkdir(parents=True, exist_ok=True)

        sim = Simulation.from_config(sim_name, sim_cfg, ref_dir=ref_dir, derived_dir=derived_dir) #TODO: for each sim_cfg

        sim

    # # Manually override a node or add one
    # sim.graph.remove_node("npf-mynpf")
    # sim.graph.add_node("npf-mynpf", ModuleNode(...))

    # sim.run()

    return sim
