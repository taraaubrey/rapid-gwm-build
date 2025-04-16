

from rapid_gwm_build.utils import inspect_class_defaults

# example Module class
class Module:
    def __init__(
            self,
            kind:str, # type of the module (ie. modflow, mt3d, etc)
            name:str=None, # name of the module
            cmd:str=None, # command to run/build module (ie. flopy.mf6.ModflowGwf)
            cmd_kwargs:dict={}, # dictionary of user input variables
            # ModuleTemplate class which we can inherit from
            dependencies:dict=None, # dict of other module required (ie. dis) -> Module type
            special_kwargs=None, # special keys that can also be specified in the config file (ie. conductivity, elevation, etc)
            extended_funcs:dict=None,
            cfg:dict=None, # config file for the module (ie. yaml file)
            **kwargs):
        self.kind = kind
        self.name = name
        
        self._cmd = cmd
        self._cmd_kwargs = cmd_kwargs
        self._special_kwargs = special_kwargs
        self._dependencies = dependencies
        self._cfg = cfg # config file for the module (ie. yaml file)

        if extended_funcs:
            for ext_func, ext_func_kwargs in extended_funcs.items():
                # check if the extended function is in the cmd_kwargs
                self._call_extended_func(ext_func, ext_func_kwargs)

        self.output = None #TODO this will need to have some sort of setter method

    def __repr__(self):
        # format of Module(name)
        return f'{self.__class__.__name__}({self.kind})'

    @classmethod
    def from_cfg(
        cls, 
        kind: str, 
        cfg:dict, 
        usr_modname: str, 
        template_cfg:dict):
        cmd = template_cfg.get('cmd') # get the command from the config file
        dependancies = template_cfg.get('dependancies', None)
        special_kwargs = template_cfg.get('special_kwargs', {})
        extended_funcs = cfg.pop('extended_funcs', None)
        
        cmd_kwargs = inspect_class_defaults(cmd) # this will be set to the defaults of the cmd

        # check that keys in the cfg are in either the cmd_kwargs or special_kwargs
        for key in cfg.keys():
            if key not in cmd_kwargs['defaults'].keys() and \
                key not in cmd_kwargs['required'] and \
                    key not in special_kwargs:
                raise ValueError(f'Invalid key {key} in {usr_modname} config file.')

        module = cls(
            kind=kind,
            name=usr_modname,
            cmd=cmd,
            cmd_kwargs=cmd_kwargs,
            dependancies=dependancies,
            special_kwargs=special_kwargs, #TODO: maybe remove in place of extended_funcs
            extended_funcs=extended_funcs, #HACK: maybe remove in place of extended_funcs
            cfg = cfg,
        )
        return module

    def _call_extended_func(self, cmd:str, kwargs):
        output = self.call_cmd(cmd, kwargs)
        if output is not None:
            # update the cmd_kwargs with the output
            self._cmd_kwargs['defaults'].update(output) #TODO: cmd_kwarsgs 
        else:
            raise ValueError(f'Invalid extended function {cmd}')

    # FIXME: old method
    def add_params(self, params: dict):
        # check if the key is in the cmd defaults
        # check if the key is in the special methods dict
        # update the cmd defaults with the new values
        for key, value in params.items():
            if key in self.cmd_kwargs.keys():
                
                # special logic for special methods
                if key in self.special_methods.keys():
                    # call special method
                    print(f'Calling special method for {key} with values {value}')
                else:
                    # set the parameter value
                    print(f'{key}:{value} is not a valid adjustable parameter for {self.name}')
    
    # FIXME: old method
    def build(self):
        self._build_dependencies()

        # run the command with the parameters
        print(f'Running {self.name}')
        print(f'Running {self.cmd} with parameters {self.cmd_kwargs}')
        # here you would call the cmd function with the cmd_kwargs as arguments
        # for example: self.cmd(**self.cmd_kwargs)
        result = self.call_cmd()
        self._set_output(self.cmd, self.cmd_kwargs, result) #TODO

    def _build_dependancies(self):
        if self.dependencies:
            print(f'Building "{self.kind}": "{self.name}" dependencies...')

            # run the dependancies first
            for cmd_kwarg, dep_module in self.dependencies.items():
                # first check if previously ran; also check if any of the cmd_kwargs have been changed
                if dep_module.output is not None:
                    self.sim_dependencies[cmd_kwarg] = dep_module.output # update the cmd_kwargs with the dependancy values
                else:
                    # run the dependancy module
                    dep_module.build()
                self.dependencies[cmd_kwarg] = dep_module.output # update the cmd_kwargs with the dependancy values

                if cmd_kwarg in self.cmd_defaults.keys():
                    # update the cmd_kwargs with the dependancy values
                    self.cmd_kwargs[cmd_kwarg] = dep_module.output

    def call_cmd(self, cmd:str, cmd_kwargs:dict=None): #TODO move out to utils or something
        import importlib

        try:
            module, class_name = cmd.rsplit(".", 1)
            module = importlib.import_module(module)
            func = getattr(module, class_name)
            return func(**cmd_kwargs)
        except ImportError as e:
            raise ImportError(f"Could not import {cmd}: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
    

    # FIXME: old method
    def _set_output(self, cmd, cmd_kwargs, result):
        output = {
            'cmd': cmd,
            'cmd_kwargs': cmd_kwargs,
            'result': result
        }
        self.output = result