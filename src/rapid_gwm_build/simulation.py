# import pathlike
from os import PathLike
import networkx as nx
import logging

from rapid_gwm_build.network_registry import NetworkRegistry
from rapid_gwm_build.nodes.node_builder import NodeBuilder
# from rapid_gwm_build.module_builder import ModuleBuilder
# from rapid_gwm_build.mesh import Mesh

class Simulation:
    def __init__(
        self,
        # ws: str | PathLike,
        name: str = None,  # name of the simulation
        cfg: dict = None,  # config file for the simulation (ie. yaml file)
        sim_type: str = "generic",  # type of the simulation (ie. modflow, mt3d, etc)
        # cfg: dict = None,  # config file for the simulation (ie. yaml file)
        # _defaults: str = None,  # defaults for the simulation (ie. yaml file)
        # # TODO: add path to model executables
    ):
        self.name = name
        self.cfg = cfg
        self.sim_type = self.cfg.get("sim_type", sim_type)  # type of the simulation (ie. modflow, mt3d, etc)
        self.set_template(self.sim_type) # backend template based on sim_type
        
        self.graph = NetworkRegistry()
        self.nodes = self.graph._graph.nodes
        self.edges = self.graph._graph.edges
        self.name_registry = {}
        self.node_builder = NodeBuilder(self.name_registry)
    

    def set_template(self, sim_type: str):
        from rapid_gwm_build.templates.template_loader import TemplateLoader
        self.template = TemplateLoader.load_template(sim_type)
    
    @classmethod
    def from_config(cls, name, sim_cfg):
        sim = cls(
            name=name,
            cfg=sim_cfg,
        )

        # 1. Build nodes (need to first create all the nodes before adding edges)
        for node_type in sim.cfg['nodes'].keys():

            node_type_cfg = sim.cfg['nodes'].get(node_type, None)
            if node_type_cfg:
                for node_key, node_cfg in node_type_cfg.items():
                    sim._node_from_cfg(node_key, node_cfg)
                    sim._resolve_references(node_key, node_cfg)

        

        return sim
    
    
    def _resolve_references(self, from_nodeid, from_node_cfg):
        params = self._flatten_dict(from_node_cfg)
        for k, v in params.items():
            if str(v).startswith("@"):
                dep_id = v[1:]
                dep_type = dep_id.split(".")[0]

                if dep_id in self.cfg['nodes'][dep_type].keys():
                    dep_cfg = self.cfg['nodes'][dep_type].get(dep_id, None)
                    if dep_cfg:
                        self._node_from_cfg(dep_id, dep_cfg)
                        self.add_edge(dep_id, from_nodeid, parameter_dependency=k)
                else:
                    raise ValueError(f"Dependency {dep_id} not found in the simulation config.")
    
    def _node_from_cfg(self, node_key, node_cfg):
        node_type = node_key.split(".")[0]
        if node_key in self.nodes:
            pass
        else:
            if node_type == 'module':
                kind = node_cfg.get("kind", None)
                module_template = self.template['module_templates'][kind]
                node_cfg['template'] = module_template
            
            self.add_node(id=node_key, **node_cfg)

    
    def add_node(self, id, **kwargs):
        node = self.node_builder.build_node(id, **kwargs)
        self.graph.add_node(id, node=node)

    def add_edge(self, source, target, **kwargs):
        self.graph.add_edge(source, target, **kwargs)


    def _flatten_dict(self, d:dict, id:str=None): #TODO: move to utils
        if not isinstance(d, dict):
            raise TypeError(f"Expected a dictionary, got {type(d).__name__}")
        
        items = []
        for k, v in d.items():
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, id=k).items())
            else:
                if id:
                    k = f"{id}.{k}"
                items.append((k, v))
        return dict(items)



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
