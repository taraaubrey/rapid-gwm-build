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
        
        self._template = self._set_template(_defaults) # this is the specific model type template (ie. specific templated modules)

        if cfg:
            self.modules = self._build_modules_from_cfg()
        else:
            self.modules = None

    def _set_template(self, _default_file:str):
        from yaml import safe_load

        if _default_file:
            with open(_default_file, 'r') as f:
                template = safe_load(f)
            return template
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
    
    def _check_module_kwargs(self, kind, cfg, usr_modname, module): #TODO move out of class
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
        modules = []
        for module_key, module_cfg in module_registry_cfg.items():
            kind, usr_modname = _parse_module_key(module_key)
            usr_modname = usr_modname if usr_modname else kind # name of the module (ie. modflow, mt3d, etc)
        
            #checks
            self._check_unique_module_name(usr_modname)
            self._check_duplicated_allowed(kind)
            self._check_module_kwargs(kind, module_cfg, usr_modname)
            # TODO add check that required in template if model type is set.
            # # check if the module is in the template
            # if kind not in self._template.keys():
            #     raise ValueError(f'Module {kind} not in template.')
            meta = {
                'usr_modname': usr_modname,
                'kind': kind,
                'cfg': module_cfg,
                'template_cfg': self._template[kind],
                'composite': self._template[kind].get('composite', False),
                'parent_module': self._template[kind].get('parent_module', None),
            }
            modules.append(meta)
        return modules
    
    def _build_modules_from_cfg(self):
        logging.debug('Building modules from config file.')

        modules = self.module_meta_from_cfg(self.cfg['modules']) #TODO: this should be moved out of class maybe?
        
        for module_kwargs in modules: 
            # check if the module is a composite module
            if module_kwargs['composite']:
                # create the composite module object
                composite_module = CompositeModule(**module_kwargs)
                self._add_module(composite_module)
            else:
                # create the module object
                module_obj = Module(**module_kwargs)
                self._add_module(module_obj)

                # create composite module if it exists
                parent_module_meta = modules.get(module_kwargs['parent_module'], None)
                if parent_module_meta:
                    # create the composite module object
                    parent_module = CompositeModule(**module_kwargs)
                    parent_module.add_child_module(module_obj)
                    self._add_module(parent_module)

    
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
