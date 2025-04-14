# import pathlike
from os import PathLike

from rapid_gwm_build.module import Module
from rapid_gwm_build.utils import set_up_ws

class Simulation:
    _default_files = {
            'mf6': r'src\rapid_gwm_build\mf6_template.yaml', # HACK: hardcoded for now
        }

    def __init__(
            self,
            ws:str|PathLike,
            name:str=None, # name of the simulation
            model_type:str=None, # type of the simulation (ie. modflow, mt3d, etc)
            cfg:dict=None, # config file for the simulation (ie. yaml file)
            modules:list[Module]=[],
    ):
        self.ws = ws
        self.cfg = None
        self.name = name
        self.model_type = model_type
        self.modules = {}
        
        # this is the specific model type template (ie. specific templated modules)
        self._template = self._get_template(model_type) # get the template for the simulation

        # add modules to the simulation
        if len(modules) > 0:
            for module in modules:
                self._add_module(module) # add the module to the simulation

    @classmethod
    def from_cfg(cls, cfg:dict, name:str=None):
    
        #TODO: validate cfg here first before the rest of the code
        ws_cfg = cfg.get('ws', None)
        module_cfg = cfg.get('modules', None)
        model_type = cfg.get('model_type', None)
        
        if cfg.get('name', None) is not None:
            name = cfg['name']
        if model_type not in cls._default_files.keys():
            raise ValueError(f'Invalid model type {model_type}')

        ws_path = set_up_ws(ws_cfg, name) #TODO some kind of print statement to say where the workspace is

        sim = cls(name=name, model_type=model_type, cfg=cfg, ws=ws_path)

        # add modules to the simulation
        for module, module_cfg in module_cfg.items():
            # parse module key
            kind, usr_modname = _parse_module_key(module)
            sim.add_module(kind=kind, cfg=module_cfg, usr_modname=usr_modname)
        
        return sim

    def _add_module(self, module:Module):

        self.modules[module.name]=module #TODO more checks: add the module to the simulation

    def _check_unique_module_name(self, name:str):
        if name in [m for m in self.modules.keys()]:
            raise ValueError(f'Module {name} already exists in the simulation. Are you sure you want to add it? Make sure to use a different name if multiples of the same package.')
    
    def _check_duplicated_allowed(self, kind:str):
        if kind in [m.kind for m in self.modules.values()]:
            duplicates_allowed = self._template.get(module.kind).get('duplicates_allowed')
            if duplicates_allowed==False:
                raise ValueError(f'Only one "{kind}" allowed. Remove this module or set duplicates_allowed to True in the template file.')
    
    def _check_module_kwargs(self, kind, cfg, usr_modname, module):
        if module:
            if not isinstance(module, Module):
                raise ValueError(f'Module must be of type Module.')
        elif not isinstance(cfg, dict):
            raise ValueError(f'Config must be a dictionary.')
        elif kind is None and cfg is None:
            raise ValueError(f'Must have either "module" or "kind" and "cfg" to add a module to the simulation.')
        elif kind not in self._template.keys():
            raise ValueError(f'Invalid module type {kind}.')
        else:
            pass
        
    def add_module(self, kind:str=None, cfg:dict=None, usr_modname:str=None, module:Module=None):
        #checks
        self._check_unique_module_name(usr_modname)
        self._check_duplicated_allowed(kind)
        self._check_module_kwargs(kind, cfg, usr_modname, module)

        # add a module to the simulation
        if isinstance(module, Module):
            self._add_module(module)
        else:
            if usr_modname is None:
                usr_modname = kind
            mod = Module.from_cfg(kind=kind, cfg=cfg, usr_modname=usr_modname, template_cfg=self._template[kind])
            
            # add the module to the simulation
            self._add_module(mod)

    def _get_template(self, model_type:str):
        from yaml import safe_load
        template_path = self._default_files.get(model_type, None)
        with open(template_path, 'r') as f:
            template = safe_load(f)
        return template


    def to_pickle(self, pickle_dir:str):
        import os
        import pickle
        # pickle the simulation object
        with open(os.path.join(pickle_dir, f'{self.name}.pkl'), 'wb') as f:
            pickle.dump(self, f)
        print(f'Pickled {self.name} to {pickle_dir}')


    def write(
            self,
            run_modules: str = 'all', # flag to run all the modules or a specific module
            write_toplevel=True, # if True, the top level module is the only module to write (ie. modflow sim writes files)
            ):
        
        # run the modules (order doesn't matter as modules have their own dependencies)
        for module in self.modules:
            if run_modules == 'all':
                module.run()
            else:
                print('Not implemented yet')
        
        # write the simulation files
        if write_toplevel:
            # get top level module (ie. module with no dependencies)
            for module in self.modules:
                if module.sim_dependencies is None:
                    # write the module files
                    module.output.write_simulation() #HACK hardcoded to floopy write for now; will need to be more dynamic in the future
                    break


def _parse_module_key(key:str):
    if '.' in key:
        kind = key.split('.')[0]
        usr_modname = key.split('.')[1]
    else:
        kind = key
        usr_modname = key
    return kind, usr_modname