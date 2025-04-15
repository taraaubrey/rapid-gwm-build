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



# %% create a template modules (this would normally be done based on a template file)

from rapid_gwm_build.simulation import Simulation

simple_freyburg = r'notebooks\simple_freyburg\simple freyburg.yaml'

# open yaml
import yaml
with open(simple_freyburg, 'r') as f:
    cfg = yaml.safe_load(f)


# first do replace of cfg with vars
var_kwargs = cfg.get('vars', None)
for vkey, vvalue in var_kwargs.items():
    # replace all ${key} with the value in the config file
    cfg = yaml.safe_load(yaml.dump(cfg).replace(f'${{{vkey}}}', str(vvalue)))

sim_kwargs = cfg.get('simulations', None)
for sim_name, sim_cfg in sim_kwargs.items():
    sim = Simulation.from_cfg(name=sim_name, cfg=sim_cfg)


# sim.write_files()

# sim.pickle()
