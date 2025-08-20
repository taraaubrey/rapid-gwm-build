# %% create a template modules (this would normally be done based on a template file)
import logging

from rapid_gwm_build import create_simulation
from rapid_gwm_build.parsers.config_parser import ConfigParser

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Set the minimum logging level
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),  # Handler for console output
        logging.FileHandler("my_log.log"),  # Handler for file output
    ],
)
# create directory structure
from pathlib import Path

# folder structure preprocessing/node_data
Path("preprocessing").mkdir(parents=True, exist_ok=True)
Path("preprocessing/node_data").mkdir(parents=True, exist_ok=True)

input_yaml = r"examples\pakipaki\pakipaki_v1.yaml"

sim = create_simulation(input_yaml)


# sim.graph.plot()

# print(here)
# sim.build()
sim.build()

sim.write()

print('done')