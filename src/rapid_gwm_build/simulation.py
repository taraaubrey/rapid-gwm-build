# import pathlike
from os import PathLike
import networkx as nx
import logging

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
        self.modules = {}
        self._graph = nx.DiGraph() #TODO: this should be a property of the simulation object
        
        self._template = self._set_template(_defaults) # this is the specific model type template (ie. specific templated modules)

        if cfg:
            self._create_modules_from_cfg()
        
        logging.debug(f'Created simulation {self.name} with {len(self.modules)} modules.')


    def _set_template(self, _default_file:str):
        from rapid_gwm_build.yaml_processor import template_processor

        if _default_file:
            return template_processor.load_and_validate(_default_file) # load the template file and validate it
        else:
            logging.debug('No sim template file.')
            return None
        

    def _add_module(self, module:Module):

        self.modules[module.name]=module #TODO more checks: add the module to the simulation

    def _check_unique_module_name(self, name:str): #TODO move out of class
        if name in [m for m in self.modules.keys()]:
            raise ValueError(f'Module {name} already exists in the simulation. Are you sure you want to add it? Make sure to use a different name if multiples of the same package.')
    
    def _check_duplicated_allowed(self, kind:str): #TODO move out of class
        if kind in [m.kind for m in self.modules.values()]:
            duplicates_allowed = self._template.get(module.kind).get('duplicates_allowed')
            if duplicates_allowed==False:
                raise ValueError(f'Only one "{kind}" allowed. Remove this module or set duplicates_allowed to True in the template file.')
    
    def _check_module_kwargs(self, kind, cfg, usr_modname, module=None): #TODO move out of class; positionals etc need to adjust
        if module:
            if not isinstance(module, Module):
                raise ValueError(f'Module must be of type Module.')
        elif not isinstance(cfg, dict|None):
            raise ValueError(f'Config must be a dictionary.')
        elif kind is None and cfg is None:
            raise ValueError(f'Must have either "module" or "kind" and "cfg" to add a module to the simulation.')
        elif kind not in self._template.keys():
            raise ValueError(f'Invalid module type {kind}.')
        else:
            pass
  
    def module_meta_from_cfg(self, module_registry_cfg:dict):
        modules = {}
        for module_key, module_cfg in module_registry_cfg.items():
            meta = self.get_module_meta(module_key)
            meta['cfg'] = module_cfg # update the cfg with the user config
            usr_modname = meta['usr_modname']
            modules[usr_modname] = meta
        return modules
    
    def get_module_meta(self, module_key:str):
        module_templates = self._template['module_templates']
        kind, usr_modname = _parse_module_key(module_key)
        usr_modname = usr_modname if usr_modname else kind # name of the module (ie. modflow, mt3d, etc)
    
        #checks
        self._check_unique_module_name(usr_modname)
        self._check_duplicated_allowed(kind)
        # TODO add check that required in template if model type is set.
        # # check if the module is in the template
        # if kind not in self._template.keys():
        #     raise ValueError(f'Module {kind} not in template.')
        meta = {
            'usr_modname': usr_modname,
            'kind': kind,
            'template_cfg': module_templates[kind],
            'parent_module': module_templates[kind].get('parent_module', None),
        }
        return meta

    
    def _create_modules_from_cfg(self):
        logging.debug('Building modules from config file.')

        for module_key, module_cfg in self.cfg['modules'].items():
            if module_key in self._graph.nodes():
                logging.debug(f'Module {module_key} already exists in the graph. Skipping.')
                continue
            else:
                module_meta = self.get_module_meta(module_key)
                module_meta['cfg'] = module_cfg # update the cfg with the user config
                module = self._create_module(module_meta)

                self._build_parent_module(module)

        logging.debug('Finished building modules from config file.')

    def _build_parent_module(self, child_module:Module):
        dependencies = child_module._template_cfg['build_dependencies']

        if dependencies: #TODO what if the user specified a dependancy in the cfg (ie. model is this dependancy)
            for dep_kind in dependencies.keys():
                module_registry = self.modules
                dep_modules = [m for m in module_registry.values() if m.kind == dep_kind]
                if len(dep_modules) > 1:
                    raise ValueError(f'{child_module.name} cannot be linked to a required dependancy module "{dep_kind}" because there is more than one.')
                elif len(dep_modules) == 1:
                        logging.debug (f'Automatically finding dependancy module {dep_kind} for {child_module.name}.')
                        dep_module = [m for m in module_registry.values() if m.kind == dep_kind][0]
                elif len(dep_modules) == 0:
                    logging.debug (f'Building default {dep_kind} for {child_module.name}.')
                    # create the module from the template
                    dep_module_meta = self.get_module_meta(dep_kind)
                    dep_module = self._create_module(dep_module_meta)
                    # recursive to build parent module if it has a parent module
                    self._build_parent_module(dep_module)
            
                # add
                cmd_key = child_module._dependencies.get(dep_kind)
                self._graph.add_edge(dep_module.name, child_module.name, module_dependency=cmd_key) # add the module to the graph

    
    def get_node_levels(self): #TODO remove maybe? maybe more a util
        """
        Calculates the level of each node in the graph, where level 0
        consists of nodes with no incoming edges.
        """
        top_level_nodes = [node for node, in_degree in self._graph.in_degree() if in_degree == 0]
        levels = {}
        queue = [(node, 0) for node in top_level_nodes]
        visited = set(top_level_nodes)

        while queue:
            current_node, level = queue.pop(0)
            levels[current_node] = level
            for successor in self._graph.successors(current_node):
                if successor not in visited:
                    visited.add(successor)
                    queue.append((successor, level + 1))
        return levels
    
    def _create_module(self, module_meta: dict):
        module = Module(**module_meta)
        self._add_module(module)
        self._graph.add_node(module.name, module=module) # add the module to the graph
        return module
    

    # FIXME: old method
    def to_pickle(self, pickle_dir:str):
        import os
        import pickle
        # pickle the simulation object
        with open(os.path.join(pickle_dir, f'{self.name}.pkl'), 'wb') as f:
            pickle.dump(self, f)
        print(f'Pickled {self.name} to {pickle_dir}')

    def build(self, mode='all'):
        for node in nx.topological_sort(self._graph):
            module = self._graph.nodes[node]['module']
            
            for pred_node in self._graph.predecessors(node):
                if pred_node not in self.modules.keys():
                    raise ValueError(f'Module {pred_node} not found in the simulation.')
                
                dep_output = self.modules[pred_node].output
                cmd_key = self._graph.edges[(pred_node, node)]['module_dependency']
                module.update_cmd_kwargs({cmd_key: dep_output}) # update the command kwargs with the output of the parent module
            
            if mode == 'all':
                module.build()
            if mode == 'update': # this would only build modules that have been changed
                pass
    
    