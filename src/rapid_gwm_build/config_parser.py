import os
import re
import hashlib
import yaml
from copy import deepcopy

class ConfigParser:
    # Regular expression to match variables like ${variable_name}
    VAR_PATTERN = re.compile(r"\$\{(\w+)\}")

    @classmethod
    def load_yaml(cls, filepath):
        """Load a YAML file and return the parsed content."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Config file not found: {filepath}")
        
        with open(filepath, 'r') as file:
            return yaml.safe_load(file)

    @classmethod
    def substitute_vars(cls, config):
        """Substitute variables in the config using the 'vars' block."""
        vars_ = config.get("vars", {})
        
        def replace(value):
            """Recursively replace variables in strings."""
            if isinstance(value, str):
                return cls.VAR_PATTERN.sub(lambda m: vars_.get(m.group(1), m.group(0)), value)
            elif isinstance(value, dict):
                return {k: replace(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [replace(v) for v in value]
            return value
        
        return replace(deepcopy(config))  # Deepcopy to avoid mutating the original config

    @classmethod
    def make_node_id(cls, param_key, param_value):
        """Generate a unique node ID based on the parameter key and value (e.g., file path)."""
        return f"input_{param_key}_{hashlib.md5(str(param_value).encode()).hexdigest()[:6]}"

    @classmethod
    def _flatten_simulation(cls, sim_name, sim_cfg):
        """Flatten the simulation configuration into node configurations."""
        nodes = {}

        # Track extracted input nodes
        input_nodes = {}

        # Process each module under 'modules'
        for module_name, module_cfg in sim_cfg.get("modules", {}).items():
            new_module_cfg = {}

            # Loop over the parameters in the module configuration
            for key, val in module_cfg.items():
                # If the parameter is a file path, extract it as an input node
                if isinstance(val, str) and (val.endswith(".tif") or val.endswith(".shp")):
                    input_id = cls.make_node_id(key, val)
                    input_nodes[input_id] = {
                        "type": "input",
                        "path": val,
                        "input_type": "raster" if val.endswith(".tif") else "vector"
                    }
                    # Replace the file path with a reference to the input node
                    new_module_cfg[key] = f"@{input_id}"  # Mark it as a reference
                else:
                    # Otherwise, just copy the value
                    new_module_cfg[key] = val

            # Add the module node
            nodes[module_name] = {
                "type": "module",
                "package": module_name.split("-")[0],  # Extract package name (e.g., 'npf' from 'npf-mynpf')
                "parameters": new_module_cfg
            }

        # Add input nodes to the final result
        nodes.update(input_nodes)
        return nodes

    @classmethod
    def parse(cls, config_filepath):
        """Parse the user config and return a normalized structure."""
        config = cls.load_yaml(config_filepath)

        # First, substitute variables (like ${data_dir})
        config = cls.substitute_vars(config)

        all_sims = {}

        # Process each simulation block
        for sim_name, sim_cfg in config.get("simulations", {}).items():
            # Flatten modules and input nodes
            node_cfgs = cls._flatten_simulation(sim_name, sim_cfg)
            all_sims[sim_name] = {
                "sim_type": sim_cfg["sim_type"],  # e.g., 'mf6'
                "mesh": sim_cfg.get("mesh", {}),
                "nodes": node_cfgs  # Extracted nodes (modules + inputs)
            }

        return all_sims
