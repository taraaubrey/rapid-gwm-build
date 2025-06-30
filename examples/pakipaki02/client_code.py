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

from rapid_gwm_build.parsers.config_parser import ConfigParser
from rapid_gwm_build.simulation import Simulation

def main():

    input_yaml = r"examples\pakipaki02\pakipaki_v0.yaml"

    # create directory structure
    from pathlib import Path

    # folder structure preprocessing/node_data
    Path("preprocessing").mkdir(parents=True, exist_ok=True)
    Path("preprocessing/node_data").mkdir(parents=True, exist_ok=True)

    parsed = ConfigParser.parse(input_yaml)
    
    for sim_name, sim_cfg in parsed.items():
        # set working directory
        ref_dir = Path(sim_cfg['ws']) / 'ref_data'
        derived_dir = Path(sim_cfg['ws']).parent /'derived_data'
        
        # create the dir
        ref_dir.mkdir(parents=True, exist_ok=True)
        derived_dir.mkdir(parents=True, exist_ok=True)

        sim = Simulation.from_config(sim_name, sim_cfg, ref_dir=ref_dir, derived_dir=derived_dir) #TODO: for each 



    # sim.graph.plot()

    # print(here)
    # sim.build()
    sim.build()

    sim.write()

    print('done')


if __name__ == "__main__":
    main()