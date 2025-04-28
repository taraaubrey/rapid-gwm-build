from os import PathLike

from rapid_gwm_build.config_parser import ConfigParser
from rapid_gwm_build.simulation import Simulation


def create_simulation(name: str, cfg_filepath: PathLike, sim_type: str = "mf6"):
    parsed = ConfigParser.parse(cfg_filepath)
    sim = Simulation.from_config(parsed["test_sim_v1"]) #TODO: for each sim_cfg

    # # Manually override a node or add one
    # sim.graph.remove_node("npf-mynpf")
    # sim.graph.add_node("npf-mynpf", ModuleNode(...))

    # sim.run()

    return sim
