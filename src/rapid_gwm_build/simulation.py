# import pathlike
from os import PathLike
import networkx as nx
import logging

from rapid_gwm_build.network_registry import NetworkRegistry
from rapid_gwm_build.node_builder import NodeBuilder
# from rapid_gwm_build.module_builder import ModuleBuilder
# from rapid_gwm_build.mesh import Mesh

class Simulation:
    def __init__(
        self,
        # ws: str | PathLike,
        name: str = None,  # name of the simulation
        sim_type: str = "generic",  # type of the simulation (ie. modflow, mt3d, etc)
        # cfg: dict = None,  # config file for the simulation (ie. yaml file)
        # _defaults: str = None,  # defaults for the simulation (ie. yaml file)
        # # TODO: add path to model executables
    ):
        self.name = name
        self.sim_type = sim_type  # type of the simulation (ie. modflow, mt3d, etc)
        self.template = None # backend template based on sim_type
        self.graph = NetworkRegistry()
        self.name_registry = {}
        self.node_builder = NodeBuilder(self.name_registry{})
        
        # self.ws = ws
        # self.cfg = cfg
        # self.mesh = None
        
        
        # self.module_builder = ModuleBuilder(
        #     templates=self._template["module_templates"],
        #     graph=self.graph,
        # )  
        
        # if cfg:
        #     # load input nodes


        #     if cfg.get("mesh", None):
        #         # create mesh
        #         self.mesh = Mesh.from_cfg(cfg.get("mesh", None))
        #         self.graph.add_node(
        #             'core.2Dmesh', ntype='core', mesh=self.mesh)

        #     # create modules
        #     self._create_modules_from_cfg()

    def set_template(self, sim_type: str):
        from rapid_gwm_build.template_loader import TemplateLoader
        self.template = TemplateLoader.load_template(sim_type)
    
    @classmethod
    def from_config(cls, sim_cfg):
        sim = cls(
            name=sim_cfg["name"],
            sim_type=sim_cfg["sim_type"]
        )
        sim.set_template(sim.sim_type)

        # 1. Build inputs
        for input_name, input_cfg in sim_cfg.get("inputs", {}).items():
            sim.add_node(input_name, type="input", **input_cfg)

        # 2. Build modules
        for mod_id, mod_cfg in sim_cfg.get("modules", {}).items():
            package, user_name = mod_id.split("-")
            sim.add_node(user_name, type="module", package=package, parameters=mod_cfg)

        return sim
    
    def add_node(self, name: str, ntype: str, **kwargs):
        if ntype:
            node_id, node = self.node_builder.build_node(name, ntype, **kwargs)
        else:
            raise ValueError(f"Unknown node type: {ntype}")

        self.graph.add_node(node_id, data=node)


    # def _create_modules_from_cfg(self):
    #     logging.debug("Building modules from config file.")

    #     for module_key, module_cfg in self.cfg["modules"].items():
    #         self.module_builder.from_cfg(module_key, module_cfg)

    
    # def build(self, mode="all"): #TODO move to GraphClass
    #     for node in nx.topological_sort(self.graph):
    #         module = self.graph.nodes[node]["module"]

    #         for dep_node in self.graph.predecessors(node):
    #             if dep_node not in self.module_registry.keys():
    #                 raise ValueError(f"Module {dep_node} not found in the simulation.")

    #             if "module_dependency" in self.graph.edges[(dep_node, node)].keys():
    #                 self._resolve_intermodule_dependencies(
    #                     dep_node, node
    #                 )  # TODO: type of dependency (ie. cmd kwarg/build)
    #             if "parameter_dependency" in self.graph.edges[(dep_node, node)].keys():
    #                 pass

    #         if mode == "all":
    #             module.build()
    #         if mode == "update":  # this would only build modules that have been changed
    #             pass

    # def _resolve_intermodule_dependencies( #TODO move to GraphClass
    #     self, pred_node, node
    # ):  # TODO GraphManagerClass
    #     module = self.graph.nodes[node]["module"]
    #     dep_output = self.modules[pred_node].output
    #     cmd_key = self.graph.edges[(pred_node, node)]["module_dependency"]
    #     module.update_cmd_kwargs(
    #         {cmd_key: dep_output}
    #     )  # update the command kwargs with the output of the parent module




# ## class Simulation:
#     def __init__(self, config=None):
#         self.graph = nx.DiGraph()
#         self.config = config or {}
#         if config:
#             self._build_initial_nodes()

#     def _build_initial_nodes(self):
#         for node_cfg in self.config.get("nodes", []):
#             self.add_node(node_cfg)

#     def add_node(self, node_cfg):
#         node = NodeBuilder.build(node_cfg)
#         self.graph.add_node(node.name, data=node)

#     def modify_node(self, name, new_cfg):
#         # Optionally update config/state
#         self.graph.remove_node(name)
#         self.add_node(new_cfg)

#     def to_config(self):
#         # Export current state to config dict
#         return {
#             "sim_type": self.config.get("sim_type"),
#             "nodes": [data["data"].to_dict() for _, data in self.graph.nodes(data=True)]
#         }
