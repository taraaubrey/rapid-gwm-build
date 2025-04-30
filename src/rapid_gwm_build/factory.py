from os import PathLike

from rapid_gwm_build.config_parser import ConfigParser
from rapid_gwm_build.simulation import Simulation


def create_simulation(cfg_filepath: PathLike):
    parsed = ConfigParser.parse(cfg_filepath)
    for sim_name, sim_cfg in parsed.items():
        sim = Simulation.from_config(sim_name, sim_cfg) #TODO: for each sim_cfg

        sim

    # # Manually override a node or add one
    # sim.graph.remove_node("npf-mynpf")
    # sim.graph.add_node("npf-mynpf", ModuleNode(...))

    # sim.run()

    return sim
