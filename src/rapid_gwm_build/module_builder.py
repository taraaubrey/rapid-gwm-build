import networkx as nx

from rapid_gwm_build.utils import _parse_module_key
from rapid_gwm_build.module import (
    Module,
    StressModule,
    SpatialDiscretizationModule,
    TemporalDiscretizationModule,
)
import logging

class ModuleBuilder:
    def __init__(
            self,
            _graph:nx.DiGraph=None,
            _templates:dict=None, # template config file (ie. yaml file)
            module_registry:dict=None,
    ):
        self.module_types = {
            'simple': Module,
            'StressModule': StressModule,
            'SpatialDiscretizationModule': SpatialDiscretizationModule,
            'TemporalDiscretizationModule': TemporalDiscretizationModule,
        }
        self._graph = _graph
        self._templates = _templates
        self.module_registry = module_registry #TODO: this should be a property of the simulation object
    

    def _check_duplicated_allowed(self, kind:str): #TODO move to Template class
        if kind in [m.kind for m in self.module_registry.values()]:
            duplicates_allowed = self._template.get(kind).get('duplicates_allowed')
            if duplicates_allowed==False:
                raise ValueError(f'Only one "{kind}" allowed. Remove this module or set duplicates_allowed to True in the template file.')
    
    def _get_module_meta(self, module_key:str):
        module_registry = self.module_registry
        kind, usr_modname = _parse_module_key(module_key)
        usr_modname = usr_modname if usr_modname else kind # name of the module (ie. modflow, mt3d, etc)
    
        #checks
        module_registry._check_unique_module_name(usr_modname)
        self._check_duplicated_allowed(kind)

        meta = {
            'usr_modname': usr_modname,
            'kind': kind,
            'template_cfg': self._templates[kind],
            'parent_module': self._templates[kind].get('parent_module', None),
        }
        return meta
    
    def _create_module(self, module_type:str, module_meta: dict) -> Module:
        builder = self.module_types.get(module_type)
        module = builder(**module_meta, _graph=self._graph) 
        self._graph.add_node(module.name, type='module', module=module) # add the module to the graph
        self.module_registry.add(module.name, module) # add the module to the registry
        return module
    
    
    def from_cfg(self, module_key: str, module_cfg: dict):
        if module_key in self._graph.nodes():
            logging.debug(f'Module {module_key} already exists in the graph. Skipping.')
        else:
            module_meta = self._get_module_meta(module_key)
            module_meta['cfg'] = module_cfg # update the cfg with the user config
            module = self._create_module('simple', module_meta) #HACK hardcoded to simple for now

            self._build_parent_module(module)
        logging.debug('Finished building modules from config file.')


    def _build_parent_module(self, child_module:Module):
        dependencies = child_module._template_cfg['build_dependencies']

        if dependencies: #TODO what if the user specified a dependancy in the cfg (ie. model is this dependancy)
            for dep_kind in dependencies.keys():
                dep_modules = [m for m in self.module_registry.values() if m.kind == dep_kind]
                if len(dep_modules) > 1:
                    raise ValueError(f'{child_module.name} cannot be linked to a required dependancy module "{dep_kind}" because there is more than one.')
                elif len(dep_modules) == 1:
                        logging.debug (f'Automatically finding dependancy module {dep_kind} for {child_module.name}.')
                        dep_module = [m for m in self.module_registry.values() if m.kind == dep_kind][0]
                elif len(dep_modules) == 0:
                    logging.debug (f'Building default {dep_kind} for {child_module.name}.')
                    # create the module from the template
                    dep_module_meta = self._get_module_meta(dep_kind)
                    dep_module = self._create_module('simple', dep_module_meta)
                    # recursive to build parent module if it has a parent module
                    self._build_parent_module(dep_module)
            
                # add
                cmd_key = child_module._dependencies.get(dep_kind)
                self._graph.add_edge(dep_module.name, child_module.name, module_dependency=cmd_key) # add the module to the graph