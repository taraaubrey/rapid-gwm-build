"""
Refactored NodeParser that orchestrates specialized parsers and handles dependencies.
Removed from_node complexity in favor of explicit context paths.
Now supports both NodeCFG object creation and dict-based node data extraction.
"""

import logging
from typing import Dict, Any, List, Optional, Union
from copy import deepcopy
from datetime import datetime

from .node_schemas import NodeSchemas

class NodeParser:
    """
    Main orchestrator for parsing all node types with dependency management.
    Uses explicit context paths instead of from_node for cleaner architecture.
    
    Can operate in two modes:
    1. Object mode: Creates NodeCFG objects (legacy compatibility)
    2. Data mode: Returns structured dict data (new workflow)
    """
    
    def __init__(self, sim_template=None):
        """
        Initialize the parser.
        
        Args:
            node_factory: Factory for creating NodeCFG objects (kept for compatibility)
        """
        # self.node_factory = node_factory or NodeFactory
        self.sim_template = sim_template or {}
        self.node_data = []  # Parsed node data
        
        # # Initialize specialized parsers (kept for potential future use)
        # self.parser_registry = NodeParserRegistry(self.node_factory)
    
    def parse_node(self, node_type: str, config: Union[Dict[str, Any], Any], 
                   context_path: List[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Main entry point for parsing any node type.
        
        Args:
            node_type: Type of node to create ('mesh', 'module', 'pipeline', etc.)
            config: Node configuration (dict or raw value for simple nodes)
            context_path: Current parsing context path (replaces from_node)
            **kwargs: Additional arguments specific to node type
            
        Returns:
            Dict: Node data with validation and dependencies
        """
        if config is None:
            logging.warning(f"Node configuration for {node_type} is None.")
            return None
        
        # Set default context if not provided
        context_path = context_path or [node_type]
        
        # Convert simple values to dict format
        if not isinstance(config, dict):
            config = {'src': config}

       
        # For specific node types, use specialized parsing
        # Each specialized parser handles its own validation and dependency extraction
        if node_type == 'mesh':
            self._parse_mesh(config, context_path)
        elif node_type == 'modules':
            return self._parse_modules(config, context_path, **kwargs)
        else:
            raise ValueError(f'Unsupported node type: {node_type}. Supported types are: mesh, pipeline, modules, input.')

    
    def _parse_modules(self, modules_config: Dict[str, Any], 
                     context_path: List[str] = None):
        if not isinstance(modules_config, dict):
            raise ValueError(f"Modules configuration must be a dictionary, got {type(modules_config)}")
        
        context_path = context_path or ['modules']
        
        for module_key, module_cfg in modules_config.items():
            if module_key == 'default_build':
                # Skip default build for now
                continue

            module_context = context_path + [module_key]
            self._parse_module(module_key, module_cfg, module_context)
    
    
    def _parse_module(self, module_key: str, module_config: Dict[str, Any], 
                     context_path: List[str] = None):
        """
        Parse a single module configuration.
        
        Args:
            module_key: Module identifier
            module_config: Module configuration dict
            context_path: Current parsing context path
            
        Returns:
            str: Reference ID of created module node
        """
        context_path = context_path or ['modules', module_key]

        # module key split
        cmd_module_name = module_key.split('-')[0] if '-' in module_key else module_key

        # validate the overall module configuration
        NodeSchemas.validate_config_strict('module', module_config, context_path)

        # data collection
        data_config = module_config.get('data')
        template_config = self.sim_template.get('modules', {}).get(cmd_module_name, {})
        
        # 2. Parse the data nodes ------------------------------------------------
        if data_config:
            # get valid data fields
            data_required_fields = template_config.get('data', [])
            # validate with allowed fields from template
            NodeSchemas.validate_config_strict('module_data', data_config, context_path, required_fields=data_required_fields)
            # add nodes
            data_context = context_path + ['data']
            data_ids = self._parse_input_collection(data_config, data_context)
        else:
            data_ids = {}

        # 3. Parse the template nodes ------------------------------------------------
        # Validate template
        if not template_config:
            raise ValueError(f"Module '{module_key}' is missing a valid 'template' configuration.")
        if cmd_module_name != module_key:
            template_config = self._replace_template_references(template_config, old_ref=cmd_module_name, new_ref=module_key)
        
        # cmd validation
        func_path = template_config.get('func')
        param_data = self._extract_function_parameters(func_path)
        param_names = [i for i in param_data.keys() if i != 'kwargs']

        # Validate command section of user input if present
        if 'cmd' in module_config:
            cmd_config = module_config['cmd']
            
            if func_path:
                # validate user input kwargs
                for key in cmd_config.keys():
                    if key not in param_names:
                        raise ValueError(f"Invalid command argument '{key}' for function '{func_path}'. Valid parameters are: {param_names}")
            else:
                raise ValueError(f"Module '{module_key}' is missing a valid 'func' in its template configuration.")
        
        # get config dict
        input_cmd_config = module_config.get('cmd', {})
        temp_build_dep_config = {
            k:v for k, v in template_config.get('build_dependencies', {}).items() if k not in input_cmd_config
            }
        default_config = {
            k: v['default'] for k, v in param_data.items() if ('default' in v) and (v['default'] is not None) and k not in input_cmd_config and k not in temp_build_dep_config
            }

        # combine dict -> order of importane default_config < template < cmd
        cmd_config = default_config | temp_build_dep_config | input_cmd_config

        # validate cmd schema
        NodeSchemas.validate_config_strict(
            'template_build_dependencies',
            cmd_config,
            context_path,
            optional_fields=param_names)
        
        default_ids = {}
        for k, v in default_config.items():
            k_context = context_path + [k]
            k_node_id = self._parse_value(v, k_context, value_type='literal')
            default_ids[k] = k_node_id
        
        input_cmd_ids = {}
        for k, v in input_cmd_config.items():
            k_context = context_path + [k]
            k_node_id = self._parse_value(v, k_context, value_type='literal')
            input_cmd_ids[k] = k_node_id
        
        tmp_config = {k:v for k, v in temp_build_dep_config.items() if k not in input_cmd_config}
        template_ids = self._parse_input_collection(tmp_config, context_path)

        all_dependencies = set(template_ids.values()) | set(input_cmd_ids.values())

        module_config = {
            'data': data_ids,
            'cmd': {**template_ids, **input_cmd_ids},
        }
        
        module_node = self._create_node(
            node_type='module',
            node_id='.'.join(context_path),
            config=module_config,
            context_path=context_path,
            dependencies=all_dependencies,
            # Metadata specific to module nodes
            cmd=module_config.get('cmd', {}),
        )

        self._add_to_node_data(module_node)

    def _add_to_node_data(self, node):

        if isinstance(node, list):
            # check if duplicate node in self.node_data
            for n in node:
                if isinstance(n, dict) and n not in self.node_data:
                    self.node_data.append(n)
                else:
                    raise ValueError(f"Unsupported node type in list: {type(n)}. Expected dict.")
        elif isinstance(node, dict) and node not in self.node_data:
            self.node_data.append(node)
        else:
            raise ValueError(f"Unsupported node type: {type(node)}. Expected dict or list of dicts.")
    
    
    def _replace_template_references(self, template_data, old_ref, new_ref):
        """Replace all node references in template data."""
        import re
        
        def replace_refs(obj):
            if isinstance(obj, str) and obj.startswith('@'):
                # Use regex for precise matching of module references
                pattern = rf'@modules\.{re.escape(old_ref)}.'
                return re.sub(pattern, f'@modules.{new_ref}.', obj)
            elif isinstance(obj, dict):
                return {k: replace_refs(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [replace_refs(item) for item in obj]
            return obj
        
        return replace_refs(template_data)
    
    
    #TODO utils?
    def _extract_function_parameters(self, func_path: str) -> dict:
        """Extract all parameters from a function given its module path."""
        import inspect

        # Import the function dynamically
        module_parts = func_path.split('.')
        module_name = '.'.join(module_parts[:-1])
        func_name = module_parts[-1]
        
        module = __import__(module_name, fromlist=[func_name])
        func = getattr(module, func_name)
        
        # Get function signature
        sig = inspect.signature(func)
        
        # Extract parameter information
        parameters = {}
        for name, param in sig.parameters.items():
            param_info = {
                'name': name,
                'kind': param.kind.name,
                'default': param.default if param.default != inspect.Parameter.empty else None,
                'annotation': param.annotation if param.annotation != inspect.Parameter.empty else None
            }
            parameters[name] = param_info
        
        return parameters


    def _parse_mesh(self, mesh_config: Dict[str, Any], 
                context_path: List[str] = None):
        """
        Parse mesh configuration with schema validation.
        """
        from .node_schemas import NodeSchemas  # Import at top of file
        
        context_path = context_path or ['mesh']
        
        # First validate the overall mesh configuration
        NodeSchemas.validate_config_strict('mesh', mesh_config, context_path)
        
        
        # 1. Prepping ------------------------------------------------
        # Define what constitutes mesh config vs mesh data
        config_keys = {'crs', 'nrow', 'ncol', 'nlay', 'resolution', 'delr', 'delc', 'xorigin', 'yorigin', 'domain'}
        data_keys = {'active_domain', 'top', 'bottoms'}
        
        # Separate config from data
        mesh_cfg = {k: v for k, v in mesh_config.items() if k in config_keys}
        mesh_data = {k: v for k, v in mesh_config.items() if k in data_keys}
        
        # 2. Parse the mesh nodes ------------------------------------------------      
        mesh_cfg_node_ids = {}
        for k, v in mesh_cfg.items():
            k_context = context_path + [k]
            k_node_id = self._parse_value(v, k_context, value_type='literal')
            mesh_cfg_node_ids[k] = k_node_id
        
        mesh_cfg_node = self._create_node(
            node_type='mesh_config',
            node_id='.'.join(context_path + ['config']),
            config=mesh_cfg_node_ids,
            context_path=context_path + ['config'],
            dependencies=set(mesh_cfg_node_ids.values()),
            # Metadata specific to mesh config nodes
            mesh_type=mesh_config.get('mesh_type', 'structured'),
        )

        self._add_to_node_data(mesh_cfg_node)
        
        # 3. Parse the data nodes ------------------------------------------------
        mesh_data_node_ids = self._parse_input_collection(mesh_data, context_path)
        
        mesh_data_node = self._create_node(
            node_type='mesh_data',
            node_id='.'.join(context_path + ['data']),
            config=mesh_data_node_ids,
            context_path=context_path + ['data'],
            dependencies=set(mesh_data_node_ids.values()),
            # Metadata specific to mesh data nodes
        )
        self._add_to_node_data(mesh_data_node)
        
        # 4. Combine  ------------------------------------------------
        # Create composite mesh node that references both config and data
        main_mesh_node = self._create_node(
            node_type='mesh',
            node_id='.'.join(context_path),
            config=mesh_config,
            context_path=context_path,
            dependencies=set([mesh_cfg_node['id'], mesh_data_node['id']]),
            # Metadata specific to composite mesh nodes
            config_keys=list(mesh_cfg.keys()),
            data_keys=list(mesh_data.keys())
        )
        self._add_to_node_data(main_mesh_node)
        

    def _is_node_type(self, node_type: str, value: Any) -> bool:
        """Check if a value represents an input node using schema validation."""
        is_valid, _ = NodeSchemas.validate_config(node_type, value)
        return is_valid
    

    def _parse_input_collection(self, data: Dict[str, Any], 
                              context_path: List[str]) -> List[Dict[str, Any]]:
        # Parse mesh data arrays (each can be Input or Pipeline)
        node_ids = {}
        
        for d_key, d_value in data.items():
            d_context = context_path + [d_key]

            # get type of node
            if isinstance(d_value, dict) and 'levels' in d_value.keys() and 'input' in d_value.keys():              
                # parse levels
                node_id = self._parse_levels(d_value, d_context)
            elif isinstance(d_value, dict) and ('pipeline' in d_value or 'builtin' in d_value) and 'input' in d_value:
                node_id = self._parse_pipeline(d_value, d_context)
            else:
                # dict as input value
                node_id = self._parse_value(d_value, d_context)
            
            if node_id:
                node_ids[d_key] = node_id
        
        return node_ids
    
    
    def _parse_levels(self, config: Any, context_path: List[str]):
        # reorganize into pipeline dict and send back to input_data_collection
        levels_config = config.copy().pop('levels')
        
        # already validated
        level_input = levels_config.get('input')
        hier_input = {f'level{i+1}': input for i, input in enumerate(level_input)}
        pipeline = [
            {'processor': 'hierarchical_levels',
             **hier_input
             }
        ]
        
        if 'pipeline' in levels_config:
            # merge with existing pipeline
            pipeline.extend(levels_config['pipeline'])

        # reconfigure
        pipeline_config = {
            **config,
            'pipeline': pipeline
        }

        return self._parse_pipeline(
            pipeline_config, 
            context_path, 
        )
        
    
    def _parse_value(self, config: Any, context_path: List[str], value_type='deferred'):
        
        if value_type not in ['deferred', 'literal']:
            raise ValueError(f"Invalid value_type '{value_type}'. Expected 'deferred' or 'literal'.")
        
        # Handle different input formats
        if isinstance(config, dict):
            input_config = config.copy()
            if 'input' in input_config:
                # Format: {input: "file.txt", other_params: "..."}
                value = input_config.config('input')
                opening_kwargs = input_config if input_config else None
            elif 'src' in input_config:
                # Format: {src: "file.txt"} or just {key: value}
                value = input_config.pop('src')
                opening_kwargs = input_config if input_config else None
            else:                # Assume it's a simple dict value
                value = input_config
                opening_kwargs = None
        else:
            # Simple value
            value = config
            opening_kwargs=None
        
        if isinstance(value, str) and value.startswith('@'):
            return value[1:]

        
        input_node = self._create_node(
            node_type='input',
            node_id='.'.join(context_path),
            config=config,
            context_path=context_path,
            dependencies=set(), # input nodes have no dependencies
            # Metadata specific to input nodes
            value=value,
            value_type=value_type,
            opening_kwargs=opening_kwargs
        )

        self._add_to_node_data(input_node)
        
        return input_node['id']

    
    def _parse_pipe(self, config: Any, context_path: List[str]):
        pipe_config = config.copy()
        # Handle different input formats
        if isinstance(pipe_config, dict):
            pipe_input = pipe_config.pop('input', None) # this is a node_id
            processor = pipe_config.pop('processor')
        else:
            raise ValueError(f"Invalid pipe configuration: {pipe_config}. Expected dict format.")
        
        # parse inputs
        node_ids = []
        for key, value in pipe_config.items():
            node_id = self._parse_value(value, context_path + [key])
            node_ids.append(node_id)
            pipe_config[key] = node_id
        
        dependencies = [pipe_input] + list(node_ids)
        node = self._create_node(
            node_type='pipe',
            node_id='.'.join(context_path),
            config=config,
            context_path=context_path,
            dependencies=set(dependencies),
            # Metadata specific to input nodes
            input=pipe_input,
            processor=processor,
            kwargs=pipe_config,
        )

        self._add_to_node_data(node)
        
        return node['id']

    
    def _create_node(self, node_type: str, node_id: str, config: Any, context_path: List[str], 
                 dependencies: List[str] = None, **metadata) -> Dict[str, Any]:
        """Create a standardized node with common fields."""
        
        return {
            'id': node_id,
            'type': node_type,
            'config': config,
            'context_path': context_path,
            'dependencies': dependencies or [],
            # 'schema_validated': True,
            **metadata,  # Additional metadata passed by caller
            'parser_metadata': {
                'parsed_at': datetime.now().isoformat(),
                'parser_version': '2.0',
            }
        }
    
    def _parse_pipeline(
        self, 
        config: Dict[str, Any], 
        context_path: List[str], 
        ):
        pipeline_config = config.copy()
        # Handle different pipeline formats
        pipelines = []
        if 'builtin' in pipeline_config:
            pipes = []
            for processor_kwargs in pipeline_config['builtin']:
                if isinstance(processor_kwargs, str):
                    pipe = {
                        'processor': processor_kwargs
                    }
                
                elif isinstance(processor_kwargs, dict):
                    processor = list(processor_kwargs.keys())[0]
                    kwargs = processor_kwargs[processor]
                    pipe = {
                        'processor': processor
                    }
                    pipe.update(kwargs)
                
                else:
                    raise ValueError(f'Builtin pipeline in the wrong format. Expect either processor as type(str) or processor: kwargs as type(dict).')
                
                pipelines.append(pipe)
        
        if 'pipeline' in pipeline_config:
            pipes = pipeline_config.get('pipeline')
            pipelines.extend(pipes)
        
        input_part = pipeline_config.get('input')
        if input_part:
            input_context = context_path + ['input']
            input_node_id = self._parse_value(input_part, input_context)
        
        # Extract dependencies from pipeline steps
        pipe_ids = []
        for i, pipe in enumerate(pipelines):
            pipe['input'] = input_node_id
            pipe_context = context_path + [f'pipe{i}']
            pipe_node_id = self._parse_pipe(pipe, pipe_context)
            input_node_id = pipe_node_id # replace with pipe output for next step
            pipe_ids.append(pipe_node_id)
        

        pipeline_node = self._create_node(
            node_type='pipeline',
            node_id='.'.join(context_path),
            config=config,
            context_path=context_path,
            dependencies=set(pipe_ids),
            # pipeline specific kwargs
            input=input_node_id,
            pipes=pipelines,
        )

        self._add_to_node_data(pipeline_node)
        
        return pipeline_node['id']

    
    
    def _extract_dependencies(self, config: Dict[str, Any], exclude_keys: list = []) -> List[str]:
        """Extract dependencies from configuration. """
        dependencies = []
        
        # Look for node references (strings starting with '@')
        if isinstance(config, str) and config.startswith('@'):
            # Remove the '@' and add to dependencies
            dep_id = config[1:]  # Remove '@' prefix
            if dep_id not in dependencies:
                dependencies.append(dep_id)
        elif isinstance(config, dict):
            for k, v in config.items():
                if isinstance(v, str) and v.startswith('@'):
                    dep_id = v[1:]
                    if dep_id not in dependencies and k not in exclude_keys:
                        dependencies.append(dep_id)

        return dependencies

    def get_all_nodes(self) -> List[Dict[str, Any]]:
        """Get all parsed node data (data mode only)."""
        return self.node_data.copy()
    
    def clear_all_node_data(self):
        """Clear all parsed node data."""
        self.node_data.clear()