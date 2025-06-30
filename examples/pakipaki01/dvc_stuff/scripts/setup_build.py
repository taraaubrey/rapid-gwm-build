import argparse
from rapid_gwm_build import create_simulation

def main(config, out_dir, graph_name):
    sim = create_simulation(config)

    # create output directory if it doesn't exist
    import os
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    node_list = sim.build_dvc_inputs(dvc_dir=out_dir, graph_name=graph_name)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True, help='Path to config file')
    parser.add_argument('--out_dir', required=True, help='Output directory')
    parser.add_argument('--graph_name', required=True, help='Output graph')
    args = parser.parse_args()
    
    main(args.config, args.out_dir, args.graph_name)