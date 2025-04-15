

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
            cfg:dict=None, # config file for the module (ie. yaml file)
            **kwargs):
        self.kind = kind
        self.name = name
        
        self._cmd = cmd
        self._cmd_kwargs = cmd_kwargs
        self._special_kwargs = special_kwargs
        self._dependencies = dependencies
        self._cfg = cfg # config file for the module (ie. yaml file)

        self.output = None #TODO this will need to have some sort of setter method

    def __repr__(self):
        # format of Module(name)
        return f'{self.__class__.__name__}({self.kind})'

    @classmethod
    def from_cfg(cls, kind: str, cfg:dict, usr_modname: str, template_cfg:dict):
        cmd = template_cfg.get('cmd') # get the command from the config file
        cmd_kwargs = inspect_class_defaults(cmd) # this will be set to the defaults of the cmd

        dependancies = template_cfg.get('dependancies', None)
        special_kwargs = template_cfg.get('special_kwargs', [])

        # check that keys in the cfg are in either the cmd_kwargs or special_kwargs
        for key in cfg.keys():
            if key not in cmd_kwargs['defaults'] and \
                key not in cmd_kwargs['required'] and \
                    key not in special_kwargs:
                raise ValueError(f'Invalid key {key} in {usr_modname} config file.')

        module = cls(
            kind=kind,
            name=usr_modname,
            cmd=cmd,
            cmd_kwargs=cmd_kwargs,
            dependancies=dependancies,
            special_kwargs=special_kwargs,
            cfg = cfg,
        )
        return module


    # def validate_cmd_kwargs(self, cmd_kwargs: dict):
    #     # check if cmd_kwargs are in the cmd_defaults
    #     for key in cmd_kwargs.keys():
    #         if key in self.cmd_defaults.keys():
    #             # check if the key is in the special methods dict
    #             pass
    #         else:
    #             print(f'{key} is not a input for {self.cmd}')

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

    def call_cmd(self):
        import importlib

        try:
            module, class_name = self.cmd.rsplit(".", 1)
            module = importlib.import_module(module)
            cls = getattr(module, class_name)
            return cls(**self.cmd_kwargs)
        except ImportError as e:
            raise ImportError(f"Could not import {self.cmd}: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
    

    def _set_output(self, cmd, cmd_kwargs, result):
        output = {
            'cmd': cmd,
            'cmd_kwargs': cmd_kwargs,
            'result': result
        }
        self.output = result