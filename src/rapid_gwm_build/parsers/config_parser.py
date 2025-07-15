import os
import re
from pathlib import Path
import yaml
from copy import deepcopy


class ConfigParser:
    # Regular expression to match variables like ${variable_name}
    VAR_PATTERN = re.compile(r"\$\{(\w+)\}")

    templates = {
        'mf6': r'../templates/mf6_template.yaml',
    }

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
    def parse(cls, config_filepath):
        """Parse the user config and return a normalized structure."""
        config = cls.load_yaml(config_filepath) # First, substitute variables (like ${data_dir})
        config = cls.substitute_config(config)

        sim_type = config.get('simulation', {}).get('setup', {}).get('sim_type', None)
        if not sim_type:
            raise ValueError("Simulation type 'sim_type' is required in the 'simulation.setup' block.")
        
        config['template'] = cls.load_template(sim_type)
        # this is where multiple yamls would be open and merged
        
        return config

    @classmethod
    def load_template(cls, sim_type):
        
        template_filename = cls.templates.get(sim_type)

        script_dir = Path(__file__).parent
    
        # Join with the filepath
        full_path = script_dir / template_filename

        return cls.load_yaml(full_path)
                       
        # if filename:
        #     with importlib.resources.path('rapid_gwm_build.templates', filename) as filepath:
        #         return template_processor.load_and_validate(str(filepath))
        # else:
        #     logging.debug("No sim template file.")
        #     return None
    
    # @classmethod
    # def get_template_nodes(cls, config):
    #     node_manager = NodeParser()
    #     for k, v in config.items():
    #         if k == 'module_templates':
    #             for module, module_cfg in v.items():
    #                 # parse build_dependency keys
    #                 if 'build_dependencies' in module_cfg.keys():
    #                     template_cfg = module_cfg['build_dependencies']
    #                     if template_cfg:
    #                         for k, val in template_cfg.items():
    #                             if isinstance(val, dict):
    #                                 template_node = node_manager.parse_template(module_key=module, attr=k, cfg=val)
    #                                 config['module_templates'][module]['build_dependencies'][k] = template_node.ref_id

    #     return {n.id: n for n in node_manager.nodes}
