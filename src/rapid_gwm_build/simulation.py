# import pathlike
from os import PathLike
import networkx as nx
import logging

from rapid_gwm_build.network_registry import NetworkRegistry
from rapid_gwm_build.nodes.node_builder import NodeBuilder
from rapid_gwm_build.nodes.node_cfg import NodeCFG
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
        self.name_registry = {} #TODO: clean this up, use graph registry instead
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

        for node in sim_cfg['nodes']:
            sim._new_node(node)
        
        # #build order of the simulation
        # build_order = ["mesh", "pipes", "module"]
        # for node_type in build_order:

        #     if node_type == "mesh":
        #         mesh_cfg = sim.cfg['nodes'].get("mesh", None)
        #         if mesh_cfg:
        #             sim._new_node('mesh', mesh_cfg)

        #     else:
        #         node_type_cfg = sim.cfg['nodes'].get(node_type, None)
        #         if node_type_cfg:
        #             for node_key, node_cfg in node_type_cfg.items():
        #                 sim._new_node(node_key, node_cfg)

    
        return sim
    
    def _resolve_references(self, node):
        if node.dependencies:
            for dep_id in node.dependencies:
                
                #get node from self.nodes
                node_list = [dat['node'] for id, dat in self.nodes.items()]
                dep_node = utils.match_nodeid(dep_id, node_list)

                if dep_node:
                    self.add_edge(dep_id, node.id)
                else:
                    raise NotImplementedError(f"Dependency {dep_id} not implemented yet.")
        else:
            logging.debug(f"Node {node.id} has no dependencies.")
            pass
                    
    
    def _new_node(self, ncfg: NodeCFG):
        self._node_from_cfg(ncfg)
        self._resolve_references(ncfg)


    def _find_default_id(self, dep_id):
        dep_type = dep_id.split(".")[0]
        mkind = dep_id.split('.')[1]

        # flag to match node based on the type (ie. module.gwf, module.sim)
        sim_filter = [n for n in self.nodes if n.startswith(f"{dep_type}.{mkind}.")]
        # in sim?
        if len(sim_filter) == 0:
            #in cfg?
            cfg_filter = [n for n in self.cfg['nodes'][dep_type] if n.startswith(f"{dep_type}.{mkind}.")]
        
            if len(cfg_filter) == 0:
                # can you make a default node here?
                if self.template['module_templates'][mkind]['default_build']['allowed']:
                    dep_id = f"{dep_type}.{mkind}."
                    self._new_node(f"{dep_type}.{mkind}.default")
                    return dep_id
                else:
                    raise ValueError(f"Default node not found for {dep_id}. Please specify a unique name.")
            elif len(cfg_filter) == 1:
                dep_id = cfg_filter[0]
                dep_cfg = self.cfg['nodes'][dep_type].get(dep_id, None)
                self._new_node(dep_id, dep_cfg)
                return dep_id
            else:
                raise ValueError(f"Multiple nodes found for {dep_id}. Please specify a unique name.")
        elif len(sim_filter) == 1:
            return sim_filter[0]
        else:
            raise ValueError(f"Multiple nodes found for {dep_id}. Please specify a unique name.")
    
    def _node_from_cfg(self, ncfg):
        
        if ncfg.id in self.nodes:
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
        # source = utils.match_nodeid(source, self.nodes)
        # # make sure source and target are in the graph
        # if source not in self.nodes or target not in self.nodes:
        #     raise ValueError(f"Source {source} or target {target} not found in the graph.")
        
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
            if self.nodes[nodeid].get('ntype') == 'module':
                node_data = self.nodes[nodeid].get('node')
                args = {}
                for dep_node in self.graph._graph.predecessors(nodeid):
                    if dep_node not in self.graph._graph.nodes:
                        raise ValueError(f"Module {dep_node} not found in the simulation.")

                    elif self.nodes[dep_node].get('node').data:
                        args[dep_node] = self.nodes[dep_node].get('node').data
                    else:
                        # build the node first
                        self.nodes[dep_node].get('node').build()
                        args[dep_node] = self.nodes[dep_node].get('node').data

                if mode == "all":
                    output = node_data.build(args)
                if mode == "update":  # this would only build modules that have been changed
                    pass
            
            logging.debug(f"Node {nodeid} built.")

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
                    id = i[1:]
                    id = utils.match_nodeid(id, self.nodes)
                    
                    i_output = self.nodes[id]['node'].data
                    ref_func.append(i_output)
                else:
                    ref_func.append(i)
            
            func = getattr(ref_func[0], ref_func[1])
            func(**(args or {}))


