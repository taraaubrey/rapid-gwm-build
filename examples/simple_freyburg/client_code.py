# %% create a template modules (this would normally be done based on a template file)
import logging
import yaml

from rapid_gwm_build.templates.config_parser import ConfigParser

from rapid_gwm_build import create_simulation
from rapid_gwm_build.utils import set_up_ws

# start logging
# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Set the minimum logging level
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),  # Handler for console output
        logging.FileHandler("my_log.log"),  # Handler for file output
    ],
)


input_yaml = r"examples\simple_freyburg\freyburg_1lyr_stress.yaml"

sim = create_simulation(input_yaml)

# sim.graph.plot()

# print(here)
sim.build()

sim.write()
