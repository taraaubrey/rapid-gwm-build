from rapid_gwm_build.simulation import Simulation
from abc import ABC, abstractmethod
import logging
## instructions on how to run mf6 simulation

class SimulationType(ABC):
    def __init__(self, sim:Simulation):
        self.sim = sim # simulation object
    
    @abstractmethod
    def build(self):
        pass # run the simulation
    
    @abstractmethod
    def write(self):
        pass

class MF6Simulation(Simulation, SimulationType):
    """
    extends the Simulation class to add the ability to run the simulation
    """
    _default_file = r'src\rapid_gwm_build\mf6_template.yaml', # HACK: hardcoded for now
    
    def __init__(
            self,
            ws:str,
            name:str=None, # name of the simulation
            model_type:str=None, # type of the simulation (ie. modflow, mt3d, etc)
            cfg:dict=None, # config file for the simulation (ie. yaml file)
            _defaults:str=None, # defaults for the simulation (ie. yaml file)
    ):
        super().__init__(ws, name, model_type, cfg, _defaults) # call the parent class constructor


    def build(self): #TODO: maybe rename to write?
        module_registry = self.modules

        # build the flopy simulation
        if 'sim' not in module_registry.keys():
            logging.info('Builing default gwf package.')
            self.add_module('sim') #TODO add default ws and stuff
        pkg = module_registry['sim']
        pkg.build(module_registry)
        mf6sim = pkg.output

        # check how many gwf packages are in the simulation
        gwfs = {}
        gwf_packages = [m for m in module_registry.values() if m.kind=='gwf'] #TODO if 
        if len(gwf_packages) == 0: # build a default gwf package
            logging.info('Builing "gwf" package from default.')
            self.add_module('gwf') #TODO add default gwf model name
        else:
            for pkg in gwf_packages:
                pkg.build(module_registry)
                gwfs[pkg.name] = pkg.output

                # build the rest of the packages
                gwf_modules = [m for m in module_registry.values() if m.]


        # the rest of the module that are not sim or gwf
        other_packages = [m for m in module_registry.keys() if m not in ['sim'] + gwf_packages]
        for gwf_pkg in gwf_packages:
            gwf = self.modules[gwf_pkg]
            # build the gwf package
            gwf.build(mf6sim)

            # add dis
            dis = self.sim.modules['dis']
            if dis.model_name: # can specify in the cfg if a package is associated with a specific model
                raise ValueError('Model name in dis package does not match gwf package.')

                # add tdis
        # else:
        #     raise ValueError("Simulation module not found in the simulation. Can't build the simulation.")


    def run(self):
        pass
        
    
    def write(self):
        # write the simulation files
        self.sim.write_files()