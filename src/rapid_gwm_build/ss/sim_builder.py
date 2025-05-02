from rapid_gwm_build.simulation import Simulation

class SimulationBuilder:
    def __init__(self, cfg):
        self.cfg = cfg

    @classmethod
    def from_config(cls, name, sim_cfg):
        cls = cls(config=sim_cfg)
        
        sim = Simulation(
            name=name,
            sim_type=sim_cfg["sim_type"]
        )

        # 1. Build nodes (need to first create all the nodes before adding edges)
        for node_type in sim_cfg['nodes'].keys():

            node_type_cfg = sim_cfg['nodes'].get(node_type, None)
            if node_type_cfg:
                for node_key, node_cfg in node_type_cfg.items():
                    sim._node_from_cfg(node_key, node_cfg)

                    params = sim._flatten_dict(node_cfg)
                    for k, v in params.items():
                        if str(v).startswith("@"):
                            dep_id = v[1:]
                            dep_type = dep_id.split(".")[0]

                            if dep_id in sim_cfg['nodes'][dep_type].keys():
                                dep_cfg = sim_cfg['nodes'][dep_type].get(dep_id, None)
                                if dep_cfg:
                                    sim._node_from_cfg(dep_id, dep_cfg)
                                    sim.add_edge(dep_id, node_key, parameter_dependency=k)
                            else:
                                raise ValueError(f"Dependency {dep_id} not found in the simulation config.")
