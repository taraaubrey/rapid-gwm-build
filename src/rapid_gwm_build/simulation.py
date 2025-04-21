# import pathlike
from os import PathLike
import logging

from rapid_gwm_build.module import Module, CompositeModule
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
            'template_cfg': self._template[kind],
            'composite': self._template[kind].get('composite', False),
            'parent_module': self._template[kind].get('parent_module', None),
        }
        return meta

    
    def _create_modules_from_cfg(self):
        logging.debug('Building modules from config file.')

        for module_key, module_cfg in self.cfg['modules'].items():
            if module_key not in self.modules.keys():
                logging.debug(f'Building module {module_key} from config file.')

                module_meta = self.get_module_meta(module_key)
                module_meta['cfg'] = module_cfg # update the cfg with the user config

                # check if the module is a composite module
                if module_meta['composite']:
                    # create the composite module object
                    module = self._create_module(module_meta, composite=True)

                else:
                    module = self._create_module(module_meta)
                    self._build_parent_module(module)


            else:
                logging.debug(f'Module {module_key} already exists in the simulation. Skipping.')

        logging.debug('Finished building modules from config file.')

    def _build_parent_module(self, child_module:Module):
        parent_module_key = child_module._template_cfg['parent_module']

        if parent_module_key:
            # if module object has a parent module, get it from the registry and if not there build it
            if parent_module_key in self.modules.keys():
                logging.debug(f'Getting parent module {parent_module_key} from module registry.')
                parent_module = self.modules[parent_module_key]
            else:
                # create module from defaults
                parent_module_meta = self.get_module_meta(parent_module_key)
                parent_module = self._create_module(parent_module_meta, composite=True)
                # recursive to build parent module if it has a parent module
                self._build_parent_module(parent_module)
            
            # add the module to the parent module
            parent_module.add_child(child_module)

    def build_module_graph(self):
        import networkx as nx
        graph = nx.DiGraph()
        all_items = list(self.modules.values())

        # Add all nodes to the graph
        for item in all_items:
            graph.add_node(item)

        # Add edges based on containment
        for item in all_items:
            if isinstance(item, CompositeModule):
                for contained_item in item.children:
                    graph.add_edge(item, contained_item)

        return graph
    
    def get_node_levels(graph):
        """
        Calculates the level of each node in the graph, where level 0
        consists of nodes with no incoming edges.
        """
        top_level_nodes = [node for node, in_degree in graph.in_degree() if in_degree == 0]
        levels = {}
        queue = [(node, 0) for node in top_level_nodes]
        visited = set(top_level_nodes)

        while queue:
            current_node, level = queue.pop(0)
            levels[current_node] = level
            for successor in graph.successors(current_node):
                if successor not in visited:
                    visited.add(successor)
                    queue.append((successor, level + 1))
        return levels
    
    def _create_module(self, module_meta: dict, composite:bool=False):
        # check if the module is a composite module
        if composite:
            # create the composite module object
            module = CompositeModule(**module_meta)
        else:
            # create the module object
            module = Module(**module_meta)
        self._add_module(module)
        return module
    
    
    def add_module(self, kind:str=None, cfg:dict=None, usr_modname:str=None, module:Module=None): #TODO API to add module manually
        usr_modname = usr_modname if usr_modname else kind # name of the module (ie. modflow, mt3d, etc)
        
        #checks
        self._check_unique_module_name(usr_modname)
        self._check_duplicated_allowed(kind)
        self._check_module_kwargs(kind, cfg, usr_modname, module)

        # add a module to the simulation
        if not isinstance(module, Module):
            if self._template['composite']:
                # check if the module is a composite module
                module = CompositeModule(kind=kind, cfg=cfg, template_cfg=self._template[kind], usr_modname=usr_modname) # create the module object
            module = Module(kind=kind, cfg=cfg, template_cfg=self._template[kind], usr_modname=usr_modname) # create the module object
            
        # add the module to the simulation & necessary composite modules
        self._add_module(module)
        
        # if parent module
        if self.cfg['parent_module']:
            parent_module = self.modules.get(self.cfg['parent_module'], None)
            if parent_module:
                # check if the module is a composite module
                if isinstance(parent_module, CompositeModule):
                    parent_module.add_child_module(module)
                else:
                    raise ValueError(f'Parent module {self.cfg["parent_module"]} is not a valid parent module.')
            else:
                raise ValueError(f'Parent module {self.cfg["parent_module"]} is not in the module registry. Please add this module first.')


    def _add_to_composite(self, module):
                #also add to composite module if its a child module
        if self._template['parent_module']:
            # find parent kind
            parent_name = self.cfg.get('parent_module', None) if not None else self._template['parent_module']
            
            parent_module = self.modules.get(parent_name, None)
            if parent_module:
                # check if the module is a composite module
                if isinstance(parent_module, CompositeModule):
                    parent_module.add_child_module(module)
                else:
                    raise ValueError(f'Parent module {parent_name} is not a composite module.')
            else:
                raise ValueError(f'Parent module {parent_name} is not in the module registry.')

    # FIXME: old method
    def to_pickle(self, pickle_dir:str):
        import os
        import pickle
        # pickle the simulation object
        with open(os.path.join(pickle_dir, f'{self.name}.pkl'), 'wb') as f:
            pickle.dump(self, f)
        print(f'Pickled {self.name} to {pickle_dir}')
