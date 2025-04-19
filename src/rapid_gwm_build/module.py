# import logging
import logging

from rapid_gwm_build.utils import inspect_class_defaults

class Module:
    def __init__(
        self,
        kind: str,
        template_cfg:dict, ## template config file (ie. yaml file)
        cfg:dict=None,  ## user cfg file (ie. yaml file)
        usr_modname: str=None,
        **kwargs #TODO these are not used
        ):

        self.kind = kind
        self.name = usr_modname if usr_modname else kind # name of the module (ie. modflow, mt3d, etc)
        self._cmd = template_cfg.get('cmd') # get the command from the config file
        self._special_kwargs = template_cfg.get('special_kwargs', {})
        self._dependencies = template_cfg.get('build_dependancies', None)
        self._cfg = cfg # config file for the module (ie. yaml file)
        self._template_cfg = template_cfg # template config file (ie. yaml file)

        kwargs = inspect_class_defaults(self._cmd) # this will be set to the defaults of the cmd
        self._cmd_kwargs = kwargs['defaults'] #TODO: this should be a setter method for the cmd_kwargs
        
        if cfg:
            extended_funcs = cfg.get('extended_funcs', None)
            if extended_funcs:
                for ext_func, ext_func_kwargs in extended_funcs.items():
                    # check if the extended function is in the cmd_kwargs
                    output = self.call_cmd(ext_func, ext_func_kwargs)
                    if output is not None:
                        # update the cmd_kwargs with the output
                        self.update_cmd_kwargs(output) #TODO: cmd_kwarsgs

        self.output = None #TODO this will need to have some sort of setter method

    def __repr__(self):
        # format of Module(name)
        return f'{self.__class__.__name__}({self.kind})'

    def update_cmd_kwargs(self, kwargs):
        if isinstance(kwargs, dict):
            self._cmd_kwargs.update(kwargs)
        else:   
            raise ValueError(f'kwargs must be a dictionary.')


    def add_params(self, params: dict): # FIXME: old method
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
    

    def call_cmd(self, cmd:str, cmd_kwargs:dict=None): #TODO move out to utils or something
        import importlib

        try:
            module, class_name = cmd.rsplit(".", 1)
            module = importlib.import_module(module)
            func = getattr(module, class_name)
            output = func(**cmd_kwargs)
        except ImportError as e:
            raise ImportError(f"Could not import {cmd}: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
        
        if output is None:
            logging.warning(f'Command {cmd} returned None.')
        return output
    

    def _set_output(self, result):
        self.output = result

    
    def _validate_dependencies(self, module_registry):
        for dep_name, dep_module in self._dependencies.items():
             # check if the dependency is in the list of modules
            if dep_module not in module_registry:
                raise ValueError(f"Dependency '{dep_name}' for module '{self.name}' not found in the simulation.")
                
    
    
    def _build_dependencies(self, module_registry): #TODO add more error handeling here
        if self._dependencies: 
            dep_kwargs = {}
            self._validate_dependencies(module_registry)
            
            # build the dependancies first
            for kwarg, module_type in self._dependencies.items():
                module = module_registry[module_type]

                if module.output is None:
                    # run the dependancy module
                    module.build(module_registry=module_registry)
                    dep_kwargs[kwarg] = module.output
                else:
                    dep_kwargs[kwarg] = module.output
            # update the cmd_kwargs with the dep_kwargs
            self.update_cmd_kwargs(dep_kwargs) #update the cmd_kwargs with the dep_kwargs
        else:
           logging.debug(f'No dependencies for {self.name}')


    def build(self, module_registry=[]):
        self._build_dependencies(module_registry)
            
        # run the command with the parameters
        output = self.call_cmd(self._cmd, self._cmd_kwargs) #TODO: this should be a setter method for the output
        self._set_output(output)




class CompositeModule(Module):
    def __init__(
            self, 
            kind: str, 
            template_cfg: dict, 
            cfg: dict = None, 
            usr_modname: str = None,
            **kwargs):
        super().__init__(kind, template_cfg, cfg, usr_modname)
        self.children = []  # List to hold child modules

    def add_child(self, child_module: Module):
        """Add a child module to this composite module."""
        if not isinstance(child_module, Module):
            raise ValueError("Child must be an instance of Module.")
        self.children.append(child_module)

    def remove_child(self, child_module: Module):
        """Remove a child module from this composite module."""
        self.children.remove(child_module)

    def get_children(self):
        """Return the list of child modules."""
        return self.children

    def build(self, module_registry=[]):
        """Build the composite module and its children."""
        # Build dependencies first
        self._build_dependencies(module_registry)

        # Build child modules
        for child in self.children:
            child.build(module_registry)

        # Run the command for the composite module
        output = self.call_cmd(self._cmd, self._cmd_kwargs)
        self._set_output(output)

    def __repr__(self):
        return f'{self.__class__.__name__}({self.kind}, children={len(self.children)})'