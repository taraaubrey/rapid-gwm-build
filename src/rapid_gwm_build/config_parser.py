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

        # Process each module under 'modules'
        for section in sections:
            nodes[section] = {}
            if section == 'modules':
                module_nodes, input_nodes = cls.parse_modules(sim_cfg, section)
                nodes['modules'].update(module_nodes)
            else:
                section_cfg = sim_cfg.get(section, {})
                if section_cfg:
                    section_cfg, input_nodes = cls.parse_input(section, section_cfg)
            nodes['inputs'].update(input_nodes)

        return nodes
    
    @classmethod
    def parse_modules(cls, sim_cfg, section='modules'):
        nodes = {}
        all_input_nodes = {}
        for module_name, module_cfg in sim_cfg.get(section, {}).items():
            mtype  = module_name.split("-")[0]
            mname = module_name.split("-")[1] if "-" in module_name else mtype  # Extract module name (e.g., 'mynpf' from 'npf-mynpf')
            
            key_path = f"modules.{mtype}.{mname}"
            
            module_cfg, input_nodes = cls.parse_input(key_path, module_cfg)


            module_node = NodeBuilder.parse_module_cfg(key_path, module_cfg)
            nodes.update(module_node)
            all_input_nodes.update(input_nodes)
        return nodes, input_nodes
    
    @classmethod
    def parse_input(cls, section_path, section_cfg):
        input_nodes = {}
        for input_key, val in section_cfg.items():
            if isinstance(val, dict):
                if 'pipes' in val.keys():
                    pipes_cfg = val['pipes']
                    pipe_key = f"{section_path}.{input_key}"
                    pipe_id = cls.parse_pipes(pipe_key, pipes_cfg)

                    ref_id, input_node = NodeBuilder.parse_input_cfg(key_path, value=pipe_id, kwargs=None)
                    input_nodes.update(input_node)

                    section_cfg[input_key] = f"{pipe_id}"
                
                elif any(special_key in val.keys() for special_key in ["input", "kwargs"]):
                    value = val.get("input", None)
                    kwargs = val.get("kwargs", {})
                    key_path = f"{section_path}.{input_key}"
                    ref_id, input_node = NodeBuilder.parse_input_cfg(key_path, value, kwargs)
                    input_nodes.update(input_node)
                    # Replace the file path with a reference to the input node
                    section_cfg[input_key] = f"{ref_id}"
                    
            else:
                value = val
                kwargs = None
            
                key_path = f"{section_path}.{input_key}"
                ref_id, input_node = NodeBuilder.parse_input_cfg(key_path, value, kwargs)
                input_nodes.update(input_node)
                # Replace the file path with a reference to the input node
                section_cfg[input_key] = f"{ref_id}"
        
        return section_cfg, input_nodes
        
    
    @classmethod
    def parse_pipes(cls, pipe_key, pipes_cfg):
        nodes = {}
        all_input_nodes = {}
        for pipe_cfg in pipes_cfg:
            for pipe_name, pipe_cfg in pipe_cfg.items():
                key_path = f"{pipe_key}.{pipe_name}"
                pipe_cfg, input_nodes = cls.parse_input(key_path, pipe_cfg)
                pipe_node = NodeBuilder.parse_pipe_cfg(key_path, pipe_cfg)
                nodes.update(pipe_node)
                all_input_nodes.update(input_nodes)
        return nodes, input_nodes
    
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
