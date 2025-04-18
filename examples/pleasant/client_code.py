
# %% create a template modules (this would normally be done based on a template file)
import logging

from rapid_gwm_build import create_simulation
from rapid_gwm_build.utils import set_up_ws, _parse_module_key

# start logging
# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Set the minimum logging level
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Handler for console output
        logging.FileHandler('my_log.log')  # Handler for file output
    ]
)


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
    
    #TODO: validate cfg here first before the rest of the code
    ws_cfg = sim_cfg.get('ws', None)
    module_cfg = sim_cfg.get('modules', None)
    sim_type = sim_cfg.get('sim_type', None)
        
    if cfg.get('name', None):
        name = sim_cfg.get('name')
    else:
        name = sim_name

    ws_path = set_up_ws(ws_cfg, name) #TODO some kind of print statement to say where the workspace is

    #create the simulation object
    sim = create_simulation(name=name, model_type=sim_type, cfg=cfg, ws=ws_path)

    #print(here)
    sim.build()

