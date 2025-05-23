# %% create a template modules (this would normally be done based on a template file)
import logging

from rapid_gwm_build import create_simulation

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Set the minimum logging level
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),  # Handler for console output
        logging.FileHandler("my_log.log"),  # Handler for file output
    ],
)


input_yaml = r"examples\pakipaki\pakipaki_v0.yaml"

sim = create_simulation(input_yaml)

# sim.graph.plot()

# print(here)
sim.build()

sim.write()

print('done')