
# %% create a template modules (this would normally be done based on a template file)

from rapid_gwm_build.simulation import Simulation

input_yaml = r'examples\pleasant\shellmound.yaml'

# open yaml
import yaml
with open(input_yaml, 'r') as f:
    cfg = yaml.safe_load(f)

# first do replace of cfg with vars
var_kwargs = cfg.get('vars', None)
for vkey, vvalue in var_kwargs.items():
    # replace all ${key} with the value in the config file
    cfg = yaml.safe_load(yaml.dump(cfg).replace(f'${{{vkey}}}', str(vvalue)))


# now we can create the simulation object
sim_kwargs = cfg.get('simulations', None)
for sim_name, sim_cfg in sim_kwargs.items():
    sim = Simulation.from_cfg(name=sim_name, cfg=sim_cfg)

    #print(here)
    sim.

