import os
import re
import hashlib
import yaml
from copy import deepcopy

from rapid_gwm_build.nodes.node_builder import NodeBuilder

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
    def _flatten_simulation(cls, sim_cfg):
        """Flatten the simulation configuration into node configurations."""
        sections = ["mesh", "modules", "pipes"]
        nodes = {}
        nodes['modules'] = {} # Track extracted module nodes
        nodes["inputs"] = {} # Track extracted input nodes
        nodes['pipes'] = {} # Track extracted pipe nodes

        # Process each module under 'modules'
        for section in sections:
            if section == 'modules':
                nodes = cls.parse_modules(nodes, sim_cfg, section)
            else:
                section_cfg = sim_cfg.get(section, {})
                if section_cfg:
                    section_cfg, nodes = cls.parse_input(nodes, section, section_cfg)
        return nodes
    
    @classmethod
    def parse_modules(cls, nodes, sim_cfg, section='modules'):
        for module_name, module_cfg in sim_cfg.get(section, {}).items():
            mtype  = module_name.split("-")[0]
            mname = module_name.split("-")[1] if "-" in module_name else mtype  # Extract module name (e.g., 'mynpf' from 'npf-mynpf')
            
            key_path = f"modules.{mtype}.{mname}"
            
            module_cfg, nodes = cls.parse_input(nodes, key_path, module_cfg)

            module_node = NodeBuilder.parse_module_cfg(key_path, module_cfg, mtype, mname)
            nodes['modules'].update(module_node)
        return nodes
    

    @classmethod
    def parse_input(cls, nodes, section_path, section_cfg):
        for input_key, val in section_cfg.items():
            update_input = True
            kwargs = None
            key_path = f"{section_path}.{input_key}"

            if isinstance(val, dict):
                if 'pipes' in val.keys():
                    pipes_cfg = val['pipes']
                    pipe_key = f"{section_path}.{input_key}"
                    ref_id, nodes = cls.parse_pipes(nodes, pipe_key, pipes_cfg)
                    update_input = False
                
                else:
                    if any(special_key in val.keys() for special_key in ["input", "kwargs"]):
                        kwargs = val.get("kwargs", {})
                        val = val.get("input", None)

            if update_input:
                ref_id, input_node = NodeBuilder.parse_input_cfg(key_path, val, kwargs)
                nodes['inputs'].update(input_node)

            section_cfg[input_key] = f"{ref_id}"
        
        return section_cfg, nodes
        
    
    @classmethod
    def parse_pipes(cls, nodes, pipe_key, pipes_cfg):
        for pipe in pipes_cfg:
            for pipe_name, cfg in pipe.items():
                key_path = f"{pipe_key}.{pipe_name}"
                new_cfg, nodes = cls.parse_input(nodes, key_path, pipe)
                ref_id, pipe_node = NodeBuilder.parse_pipe_cfg(key_path, new_cfg)
                nodes['pipes'].update(pipe_node)
                
        return ref_id, nodes
    
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
            node_cfgs = cls._flatten_simulation(sim_cfg)
            all_sims[sim_name] = {
                "sim_type": sim_cfg["sim_type"],  # e.g., 'mf6'
                "nodes": node_cfgs  # Extracted nodes (modules + inputs)
            }

        return all_sims
