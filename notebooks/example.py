# %% [markdown]
# vars:
#     - simulations:
#         sim_a:
#             filename: sim_a.pkl
# 
# stages:
#     build_modules:
#         foreach:
#             sim_a:
#                 kwargs: sim_a.yaml
#                 params: sim_a_params.yaml
#                 dependancies: None
#             gwf_a:
#                 kwargs: gwf.yaml
#                 params: gwf_params.yaml
#                 dependancies: sim_a.pkl
#             dis:
#                 kwargs: dis.yaml
#                 params: dis_params.yaml
#                 dependancies: gwf_a.pkl
#         do:
#             cmd: python build_modules.py simulations.sim_a.filename ${key} ${item.kwargs}
#             params: ${item.params}
#             dependancies: ${item.dependancies}
#             output: ${key}.pkl

# %% [markdown]
# # dis_a_params.yaml
# # sample parameters file generated for dis_a
# 
# stress_period_data:
#     elevation: dem.tif # timeseries input {0: dem.tif}
#     conductivity: 1.0 # timeseries input {0: 1.0, 1: 2.0}

# %% gwm-kit code
#get expected defaults and datatypes from flopy

def inspect_class_defaults(cls_path:str) -> dict:
    import importlib
    import inspect
    
    try:
        # Try to import the class from the specified path
        module_name, class_name = cls_path.rsplit(".", 1)
        module = importlib.import_module(module_name)
        inspect_class = getattr(module, class_name)
        print(f"Inspecting {inspect_class.__name__} class")
    except ImportError as e:
        # Handle the case where the import fails
        raise ImportError(f"Could not import {cls_path}: {e}")

    signature = inspect.signature(inspect_class.__init__)

    defaults = {}
    expected_types = {}
    for name, param in signature.parameters.items():
        if name != 'self':
            defaults[name] = param.default # can also checkout param.annotation or param.kind
    return defaults
# print("Expected types:")
# print(expected_types)

class Simulation:
    def __init__(
            self,
            name:str,
            model_type:str=None, # type of the simulation (ie. modflow, mt3d, etc)
            modules: list=[],
    ):
        self.name = name
        self.model_type = model_type
        self.modules = modules

    def add_module(self, module):
        # add the module to the simulation
        self.modules.append(module)

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
        

# example Module class
class Module:
    def __init__(
            self,
            modtype:str, # type of the module (ie. modflow, mt3d, etc)
            name:str=None, # name of the module
            cmd_kwargs:dict={}, # dictionary of user input variables
            # ModuleTemplate class which we can inherit from
            sim_dependencies:dict=None, # dict of other module required (ie. dis) -> Module type
            param_dict=None, # dictionary of adjustable parameter names
            special_methods=None, # special methods to format params
            cmd=None, # command to run/build module
            **kwargs):
        self.modtype = modtype
        self.name = name
        self.sim_dependencies = sim_dependencies
        self.param_dict = param_dict
        self.special_methods = special_methods
        self.cmd = cmd
        self.cmd_kwargs = cmd_kwargs
        # TODO: set when cmd is being set
        self.cmd_defaults = inspect_class_defaults(self.cmd) # this will be set to the defaults of the cmd function (ie. flopy.mf6.ModflowGwfdrn)

        self.output = None #TODO this will need to have some sort of setter method

    def validate_cmd_kwargs(self, cmd_kwargs: dict):
        # check if cmd_kwargs are in the cmd_defaults
        for key in cmd_kwargs.keys():
            if key in self.cmd_defaults.keys():
                # check if the key is in the special methods dict
                pass
            else:
                print(f'{key} is not a input for {self.cmd}')

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
    
    def run(self):
        # first run dependancies
        if self.sim_dependencies:
            self.run_dependancies()

        # run the command with the parameters
        print(f'Running {self.name}')
        print(f'Running {self.cmd} with parameters {self.cmd_kwargs}')
        # here you would call the cmd function with the cmd_kwargs as arguments
        # for example: self.cmd(**self.cmd_kwargs)
        result = self.call_cmd()
        self._set_output(self.cmd, self.cmd_kwargs, result) #TODO

    def run_dependancies(self):
        # run the dependancies first
        for cmd_kwarg, dep_module in self.sim_dependencies.items():
            # first check if previously ran; also check if any of the cmd_kwargs have been changed
            if dep_module.output is not None:
                print(f'{dep_module.name} already ran')
                self.sim_dependencies[cmd_kwarg] = dep_module.output # update the cmd_kwargs with the dependancy values
            else:
                # run the dependancy module
                dep_module.run()
            self.sim_dependencies[cmd_kwarg] = dep_module.output # update the cmd_kwargs with the dependancy values

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




# %% create a template modules (this would normally be done based on a template file)
sim = Module(
    modtype='sim',
    name = 'test_sim',
    sim_dependencies=None,
    cmd='flopy.mf6.MFSimulation',
    cmd_kwargs={
        'sim_ws': r'notebooks\data\models'}
)

tdis = Module(
    modtype='tdis',
    name = 'test_tdis',
    sim_dependencies={'simulation': sim}, # TODO referencing a module; in the future will need to be some sort of ModuleManager class to get the module
    cmd='flopy.mf6.ModflowTdis'
)

ims = Module(
    modtype='ims',
    name = 'test_ims',
    sim_dependencies={'simulation': sim},
    cmd='flopy.mf6.ModflowIms'
)

gwf = Module(
    modtype='gwf',
    name='test_gwf',
    sim_dependencies={'simulation': sim},
    cmd='flopy.mf6.ModflowGwf'
)

drn = Module(
    modtype = 'drn',
    name = 'test_drn',
    sim_dependencies={'model': gwf},
    param_dict={'stress_period_data': ['conductivity', 'elevation', 'mask']},
    cmd='flopy.mf6.ModflowGwfdrn',
    special_methods={'stress_period_data': 'get_stress_period_data function'},
)

# %% DVC param.yaml

# these would be inputs from the params file in dvc
## v0.0.1
dis_botm_params = {
    'stress_period_data': r'examples\session_a\experiment_a\mf6_monthly_model_files_1lyr_newstress\freyberg6.dis_botm_layer1.txt',
}

## v0.0.2
# params = {
#     'stress_period_data': {
#         'conductivity': 0.1,
#         'elevation': 10.0,
#         'mask': [1, 2, 3] # cellid
#     },
#     'save_flows': True,
# }

# %% 

mysim = Simulation(
    name='test_sim',
    model_type='mf6',
    modules=[sim, tdis, ims, gwf, drn]
)

mysim.write()

pickle_dir = r'notebooks\data\models'
mysim.pickle(pickle_dir)

# %%


# %%



