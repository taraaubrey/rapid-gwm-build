# import pathlike
from os import PathLike
from pathlib import Path
import networkx as nx
import logging

from rapid_gwm_build.network_registry import NetworkRegistry
from rapid_gwm_build.ss.node_builder import NodeBuilder
from rapid_gwm_build.nodes.node_base import NodeCFG
from rapid_gwm_build import utils
# from rapid_gwm_build.module_builder import ModuleBuilder
# from rapid_gwm_build.mesh import Mesh

class Simulation:
    def __init__(
        self,
        # ws: str | PathLike,
        name: str = None,  # name of the simulation
        cfg: dict = None,  # config file for the simulation (ie. yaml file)
        sim_type: str = "generic",  # type of the simulation (ie. modflow, mt3d, etc)
        ref_dir: str | PathLike = None,  # output directory for the simulation
        derived_dir: str | PathLike = None,  # output directory for the simulation
        # cfg: dict = None,  # config file for the simulation (ie. yaml file)
        # _defaults: str = None,  # defaults for the simulation (ie. yaml file)
        # # TODO: add path to model executables
    ):
        self.name = name
        self.cfg = cfg
        
        self.ref_dir = ref_dir if isinstance(ref_dir, Path) else Path(ref_dir)
        self.derived_dir = derived_dir if isinstance(derived_dir, Path) else Path(derived_dir)
        
        self.sim_type = self.cfg.get("sim_type", sim_type)  # type of the simulation (ie. modflow, mt3d, etc)
        self.set_template(self.sim_type) # backend template based on sim_type
        
        self.graph = NetworkRegistry()
        self.edges = self.graph._graph.edges
        self.name_registry = {} #TODO: clean this up, use graph registry instead
        self.node_builder = NodeBuilder(self.name_registry)
    

    @property
    def nodes(self):
        return {n_id: data['node'] for n_id, data in self.graph._graph.nodes.data()}
    
    def set_template(self, sim_type: str):
        from rapid_gwm_build.templates.template_loader import TemplateLoader
        self.template = TemplateLoader.load_template(sim_type)
    
    @classmethod
    def from_config(cls, name, sim_cfg, ref_dir=None, derived_dir=None):
        sim = cls(
            name=name,
            cfg=sim_cfg,
            ref_dir=ref_dir,
            derived_dir=derived_dir,
        )

        for node_id, node in sim_cfg['nodes'].items():
            sim._new_node(node)

    
        return sim
    
    def _resolve_references(self, node):
        if node.dependencies:
            for dep_id in node.dependencies:

                if dep_id not in self.nodes.keys() and dep_id not in self.cfg['nodes'].keys():
                    raise ValueError(f"Node {dep_id} not found in the simulation.")
                
                #get node from self.nodes
                node_list = [node_id for node_id in self.nodes.keys()]
                dep_nodeid = utils.match_nodeid(dep_id, node_list)

                if not dep_nodeid:
                    dep_cfg = self.cfg['nodes'].get(dep_id, None)
                    self._new_node(dep_cfg)
                    
                
                self.add_edge(dep_id, node.id)

        else:
            logging.debug(f"Node {node.id} has no dependencies.")
            pass
                    
    
    def _new_node(self, ncfg: NodeCFG):
        self._node_from_cfg(ncfg)
        self._resolve_references(ncfg)


    def _node_from_cfg(self, ncfg):
        
        if ncfg.id in [n_id for n_id in self.nodes.keys()]:
            pass
        else:
            if ncfg.type == 'module':
                module_template = self.template['module_templates'][ncfg.module_type]
                ncfg.template = module_template
            
            self.add_node(ncfg)
    

    def add_node(self, ncfg: NodeCFG=None):
        if isinstance(ncfg, NodeCFG):
            self.graph.add_node(ncfg)
        elif isinstance(ncfg, dict):
            raise NotImplementedError("Node configuration dictionary not implemented yet.") #TODO: implement this
            self.graph.add_node(ncfg.id, ncfg=ncfg)


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

    
    def build(self, mode="all"): #TODO move to GraphClass
        
        
        for nodeid in nx.topological_sort(self.graph._graph):
            node = self.nodes[nodeid]
            if node.type == 'module':
                args = {}
                for dep_id in self.graph._graph.predecessors(nodeid):
                    if dep_id not in self.nodes.keys():
                        raise ValueError(f"Module {dep_id} not found in the simulation.")

                    elif not self.nodes[dep_id].data:
                        self.nodes[dep_id].resolve(sim_nodes=self.nodes, ref_dir=self.ref_dir, derived_dir=self.derived_dir)
                    
                    args[dep_id] = self.nodes[dep_id].data

                if mode == "all":
                    node.resolve(args)
                if mode == "update":  # this would only build modules that have been changed
                    pass
                
                if node.id != 'module.sim':
                    node.data.set_all_data_external()
                logging.debug(f"Node {nodeid} built.")
        logging.debug(f"Simulation {self.name} built.")

    def write(self):
        pass
        ins = self.template['write']

        for i, call_dict in ins.items():
            func = call_dict.get('func', None)
            args = call_dict.get('args', None)

            ref_func = []
            for i in func:
                # resolve the references in the input dictionary
                if i.startswith("@"):
                    node_id = i[1:]
                    node_list = [i for i in self.nodes.keys()]
                    ref_id = utils.match_nodeid(node_id, node_list)
                    
                    ref_node = self.nodes.get(ref_id)
                    ref_func.append(ref_node.data)
                else:
                    ref_func.append(i)
            
            func = getattr(ref_func[0], ref_func[1])
            func(**(args or {}))


