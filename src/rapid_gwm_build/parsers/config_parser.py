import os
import re
import hashlib
import yaml
from copy import deepcopy

from rapid_gwm_build.ss.node_builder import NodeBuilder
from rapid_gwm_build.parsers.node_parser import NodeParser

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
    def substitute_config(cls, config):
        return cls.recursive_substitute(config, config)
    
    @staticmethod
    def resolve_placeholder(value, context):
        """
        Resolve a single placeholder in the value string.
        """
        if isinstance(value, str):
            # Match placeholders like ${key.subkey1.subkey2}
            while "${" in value:
                matches = re.findall(r"\$\{([a-zA-Z0-9_.]+)\}", value)
                for match in matches:
                    keys = match.split(".")
                    resolved_value = context
                    for key in keys:
                        resolved_value = resolved_value.get(key, None)
                        if resolved_value is None:
                            raise KeyError(f"Key '{match}' not found in the configuration.")
                    value = value.replace(f"${{{match}}}", str(resolved_value))
        return value

    @classmethod
    def recursive_substitute(cls, obj, context):
        """
        Recursively substitute placeholders in the object.
        """
        if isinstance(obj, dict):
            return {key: cls.recursive_substitute(value, context) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [cls.recursive_substitute(item, context) for item in obj]
        else:
            return cls.resolve_placeholder(obj, context)



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
    def _get_node_cfg(cls, sim_cfg):
        node_manager = NodeParser()

        for node_type in ["mesh", "modules", "pipes"]:
            type_cfg = sim_cfg.get(node_type, None)
            if type_cfg:
                node_manager.parse_node(node_type, **type_cfg)

        return {n.id: n for n in node_manager.nodes}
    
    @classmethod
    def parse(cls, config_filepath):
        """Parse the user config and return a normalized structure."""
        config = cls.load_yaml(config_filepath)

        config = cls.substitute_config(config)
        # First, substitute variables (like ${data_dir})
        # config = cls.substitute_vars(config)

        all_sims = {}

        # Process each simulation block
        for sim_name, sim_cfg in config.get("simulations", {}).items():
            # Flatten modules and input nodes
            node_cfgs = cls._get_node_cfg(sim_cfg)
            all_sims[sim_name] = {
                "sim_type": sim_cfg["sim_type"],  # e.g., 'mf6'
                "ws": sim_cfg["ws"],  # Working directory
                "nodes": node_cfgs  # Extracted nodes (modules + inputs)
            }

        return all_sims
    
    @classmethod
    def parse_template(cls, cfg_dict):
        node_manager = NodeParser()
        config = cls.substitute_config(cfg_dict)

        all_modules = {}

        for k, v in cfg_dict.items():
            all_modules[k] = v
            if k == 'module_templates':
                for module, module_cfg in cfg_dict.get(k, {}).items():
                    node_manager.parse_node(node_type, sim_cfg.get(node_type, None))
