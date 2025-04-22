# import pathlike
from os import PathLike
import networkx as nx
import logging

from rapid_gwm_build.module_registry import ModuleRegistry
from rapid_gwm_build.module_builder import ModuleBuilder
from rapid_gwm_build.module import Module
from rapid_gwm_build.utils import _parse_module_key

class Simulation:

    def __init__(
            self,
            ws:str|PathLike,
            name:str=None, # name of the simulation
            model_type:str='generic', # type of the simulation (ie. modflow, mt3d, etc)
            cfg:dict=None, # config file for the simulation (ie. yaml file)
            _defaults:str=None, # defaults for the simulation (ie. yaml file)
            #TODO: add path to model executables
    ):
        self.ws = ws
        self.cfg = cfg
        self.name = name
        self.model_type = model_type # type of the simulation (ie. modflow, mt3d, etc)
        self._graph = nx.DiGraph() #TODO: this should be a property of the simulation object
        self._template = self._set_template(_defaults) # this is the specific model type template (ie. specific templated modules)
        
        self.module_registry = ModuleRegistry()
        self.module_builder = ModuleBuilder(
            _templates=self._template['module_templates'],
            _graph=self._graph,
            module_registry=self.module_registry,
            ) #TODO: this should be a property of the simulation object

        
        self._template = self._set_template(_defaults) # this is the specific model type template (ie. specific templated modules)

        if cfg:
            # create modules
            self._create_modules_from_cfg()
        
        logging.debug(f'Created simulation {self.name} with {len(self.module_registry)} modules.')


    def _set_template(self, _default_file:str):
        from rapid_gwm_build.yaml_processor import template_processor

        if _default_file:
            return template_processor.load_and_validate(_default_file) # load the template file and validate it
        else:
            logging.debug('No sim template file.')
            return None

  
    def _create_modules_from_cfg(self):
        logging.debug('Building modules from config file.')

        for module_key, module_cfg in self.cfg['modules'].items():
            self.module_builder.from_cfg(module_key, module_cfg)
    
 

    def build(self, mode='all'):
        for node in nx.topological_sort(self._graph):
            module = self._graph.nodes[node]['module']
            
            for dep_node in self._graph.predecessors(node):
                if dep_node not in self.module_registry.keys():
                    raise ValueError(f'Module {dep_node} not found in the simulation.')
                
                if 'module_dependency' in self._graph.edges[(dep_node, node)].keys():
                    self._resolve_intermodule_dependencies(dep_node, node) #TODO: type of dependency (ie. cmd kwarg/build)
                if 'parameter_dependency' in self._graph.edges[(dep_node, node)].keys():
                    pass

            if mode == 'all':
                module.build()
            if mode == 'update': # this would only build modules that have been changed
                pass
    
    def _resolve_intermodule_dependencies(self, pred_node, node): #TODO GraphManagerClass
        module = self._graph.nodes[node]['module']
        dep_output = self.modules[pred_node].output
        cmd_key = self._graph.edges[(pred_node, node)]['module_dependency']
        module.update_cmd_kwargs({cmd_key: dep_output}) # update the command kwargs with the output of the parent module
    