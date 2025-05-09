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
            node_manager.parse_node(node_type, sim_cfg.get(node_type, None))

        return node_manager.nodes
    
    @classmethod
    def parse_mesh(cls, nodes, sim_cfg, section='mesh'):
        mesh_cfg = sim_cfg.get(section, {})
        if mesh_cfg:
            mesh_cfg, nodes = cls.parse_input(nodes, section, mesh_cfg)
            nodes['mesh'].update(mesh_cfg)
        return nodes
    
    @classmethod
    def parse_modules(cls, nodes, sim_cfg, section='module'):
        for modules_name, modules_cfg in sim_cfg.get('modules', {}).items():
            mtype  = modules_name.split("-")[0]
            mname = modules_name.split("-")[1] if "-" in modules_name else mtype  # Extract modules name (e.g., 'mynpf' from 'npf-mynpf')
            
            key_path = f"{section}.{mtype}.{mname}"
            
            modules_cfg, nodes = cls.parse_input(nodes, key_path, modules_cfg)

            modules_node = NodeBuilder.parse_module_cfg(key_path, modules_cfg, mtype, mname)
            nodes['module'].update(modules_node)
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
                nodes['input'].update(input_node)

            section_cfg[input_key] = ref_id
        
        return section_cfg, nodes
        
    
    @classmethod
    def parse_pipes(cls, nodes, pipe_key, pipes_cfg):
        for pipe in pipes_cfg:
            for pipe_name, cfg in pipe.items():
                key_path = f"{pipe_key}.{pipe_name}"
                new_cfg, nodes = cls.parse_input(nodes, key_path, pipe)
                ref_id, pipe_node = NodeBuilder.parse_pipe_cfg(key_path, new_cfg)
                nodes['pipe'].update(pipe_node)
                
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
            node_cfgs = cls._get_node_cfg(sim_cfg)
            all_sims[sim_name] = {
                "sim_type": sim_cfg["sim_type"],  # e.g., 'mf6'
                "nodes": node_cfgs  # Extracted nodes (modules + inputs)
            }

        return all_sims
