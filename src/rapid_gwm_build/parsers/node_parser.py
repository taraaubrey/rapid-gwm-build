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
from .specialized_parsers import NodeParserRegistry
from .pipeline_parser import PipelineParser
from rapid_gwm_build.nodes.node_cfg import NodeFactory


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
        cmd_key = module_key.split('-')[0] if '-' in module_key else module_key

        # validate the overall module configuration
        NodeSchemas.validate_config_strict('module', module_config, context_path)

        # data collection
        data_config = module_config.get('data')
        template_config = self.sim_template.get('modules', {}).get(cmd_key, {})
        
        if data_config:
            # get valid data fields
            data_required_fields = template_config.get('data', [])
            # validate with allowed fields from template
            NodeSchemas.validate_config_strict('module_data', data_config, context_path, required_fields=data_required_fields)
            # add nodes
            data_context = context_path + ['data']
            data_nodes, data_dependencies = self._parse_data_collection(data_config, data_context)

        # Validate template
        if not template_config:
            raise ValueError(f"Module '{module_key}' is missing a valid 'template' configuration.")
        if cmd_key != module_key:
            template_config = self._replace_template_references(template_config, old_ref=cmd_key, new_ref=module_key)
        
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

        default_config = {k: v['default'] for k, v in param_data.items() if ('default' in v) and (v['default'] is not None)}

        # combine dict -> order of importane default_config < template < cmd
        cmd_config = {
            **default_config,
            **template_config.get('build_dependencies', {}),
            **module_config.get('cmd', {})}

        # validate cmd schema
        NodeSchemas.validate_config_strict(
            'template_build_dependencies',
            cmd_config,
            context_path,
            optional_fields=param_names)
        
        # add nodes
        cmd_nodes, cmd_dependencies = self._parse_data_collection(cmd_config, context_path)
        
        # don't need to include defualts
        module_dependencies = [i['id'] for i in cmd_nodes if i['context_path'][-1] not in default_config.keys()]
        module_node = self._create_node(
            node_type='module',
            node_id='.'.join(context_path),
            config=cmd_config,
            context_path=context_path,
            dependencies=module_dependencies,
            # Metadata specific to module nodes
            template_config=template_config,
            module_config=module_config
        )

        self.node_data.append(module_node)

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
        # is_valid, error_msg = NodeSchemas.validate_config('mesh', mesh_config)
        # if not is_valid:
        #     logging.error(f"Mesh validation failed: {error_msg}")
        #     raise ValueError(f"Invalid mesh configuration: {error_msg}")
        
        # Define what constitutes mesh config vs mesh data
        config_keys = {'crs', 'nrow', 'ncol', 'nlay', 'resolution', 'delr', 'delc', 'xorigin', 'yorigin'}
        data_keys = {'active_domain', 'top', 'bottoms'}
        
        # Separate config from data
        mesh_cfg = {}
        mesh_data = {}
        
        for key, value in mesh_config.items():
            if key in config_keys:
                mesh_cfg[key] = value
            elif key in data_keys:
                mesh_data[key] = value
            else:
                # Unknown keys go to data by default (could be custom arrays)
                logging.warning(f"Unknown mesh key '{key}', treating as data array")
                mesh_data[key] = value
        
        # Validate mesh config schema
        NodeSchemas.validate_config_strict('mesh_config', mesh_cfg, context_path)
        # is_valid, error_msg = NodeSchemas.validate_config('mesh_config', mesh_cfg)
        # if not is_valid:
        #     logging.error(f"Mesh config validation failed: {error_msg}")
        #     raise ValueError(f"Invalid mesh config: {error_msg}")
        
        # Validate mesh data schema
        NodeSchemas.validate_config_strict('mesh_data', mesh_data, context_path)
        # is_valid, error_msg = NodeSchemas.validate_config('mesh_data', mesh_data)
        # if not is_valid:
        #     logging.error(f"Mesh data validation failed: {error_msg}")
        #     raise ValueError(f"Invalid mesh data: {error_msg}")
        
        # Create mesh config node (metadata only, no dependencies)
        mesh_config_node = self._create_node(
            node_type='mesh_config',
            node_id='.'.join(context_path + ['config']),
            config=mesh_cfg,
            context_path=context_path + ['config'],
            dependencies=[],  # Config has no dependencies
            # Metadata specific to mesh config nodes
            parser_metadata= {
                'parsed_at': datetime.now().isoformat(),
                'parser_version': '2.0',
                'is_mesh_config': True,
                'validation_passed': True
            }
        )

        self.node_data.append(mesh_config_node)
        
        
        mesh_data_nodes, array_dependencies = self._parse_data_collection(mesh_data, context_path)
        # # Parse mesh data arrays (each can be Input or Pipeline)
        # mesh_data_nodes = []
        # array_dependencies = []
        
        # for array_key, array_value in mesh_data.items():
        #     array_context = context_path + [array_key]

        #     if self._is_node_type('pipeline', array_value):
        #         # Parse as pipeline node
        #         pipeline_node = self._parse_pipeline(array_value, array_context, array_key)
        #         mesh_data_nodes.append(pipeline_node)
        #         array_dependencies.extend(pipeline_node['dependencies'])
        #         array_dependencies.append(pipeline_node['id'])
            
        #     else:
        #         # Parse as input node
        #         input_node = self._parse_input(array_value, array_context, array_key)
        #         mesh_data_nodes.append(input_node)
        #         array_dependencies.append(input_node['id'])
        
        # Create main mesh data node that references all arrays
        mesh_data_node = self._create_node(
            node_type='mesh_data',
            node_id='.'.join(context_path + ['data']),
            config={key: f"@{'.'.join(context_path + [key])}" for key in mesh_data.keys()},
            context_path=context_path + ['data'],
            dependencies=array_dependencies,
            # Metadata specific to mesh data nodes
            parser_metadata={
                'parsed_at': datetime.now().isoformat(),
                'parser_version': '2.0',
                'is_mesh_data': True,
                'array_keys': list(mesh_data.keys())
            }
        )
        self.node_data.append(mesh_data_node)
        
        # Add all array nodes to our data
        # self.node_data.extend(mesh_data_nodes)
        
        # Create composite mesh node that references both config and data
        main_mesh_node = self._create_node(
            node_type='mesh',
            node_id='.'.join(context_path),
            config={
                'config_ref': f"@{mesh_config_node['id']}",
                'data_ref': f"@{mesh_data_node['id']}"
            },
            context_path=context_path,
            dependencies=[mesh_config_node['id'], mesh_data_node['id']],
            # Metadata specific to composite mesh nodes
            parser_metadata={
                'parsed_at': datetime.now().isoformat(),
                'parser_version': '2.0',
                'is_composite_mesh': True,
            },
            is_composite_mesh=True,
            has_config=bool(mesh_cfg),
            has_data=bool(mesh_data),
            config_keys=list(mesh_cfg.keys()),
            data_keys=list(mesh_data.keys())
        )
        self.node_data.append(main_mesh_node)
        

    def _is_node_type(self, node_type: str, value: Any) -> bool:
        """Check if a value represents an input node using schema validation."""
        is_valid, _ = NodeSchemas.validate_config(node_type, value)
        return is_valid
    

    def _parse_data_collection(self, data: Dict[str, Any], 
                              context_path: List[str]) -> List[Dict[str, Any]]:
                # Parse mesh data arrays (each can be Input or Pipeline)
        data_nodes = []
        dependencies = []
        
        for d_key, d_value in data.items():
            d_context = context_path + [d_key]

            if self._is_node_type('pipeline', d_value):
                # Parse as pipeline node
                pipeline_node = self._parse_pipeline(d_value, d_context, d_key)
                data_nodes.append(pipeline_node)
                # dependencies.extend(pipeline_node['dependencies'])
                dependencies.append(pipeline_node['id'])
            
            else:
                # Parse as input node
                input_node = self._parse_input(d_value, d_context, d_key)
                data_nodes.append(input_node)
                dependencies.append(input_node['id'])
        
        return data_nodes, dependencies
    
    
    def _parse_input(self, input_config: Any, context_path: List[str], array_type: str = None):

        # Handle different input formats
        if isinstance(input_config, dict):
            if 'input' in input_config:
                # Format: {input: "file.txt", other_params: "..."}
                src = input_config['input']
                config = input_config.copy()
            else:
                # Format: {src: "file.txt"} or just {key: value}
                src = input_config.get('src', input_config) # this should be avoided in validation (not allowed to have dict as lazy input)
                config = input_config
        else:
            # Simple value
            src = input_config
            config = {'src': src}
        
        # Extract dependencies
        dependencies = self._extract_dependencies(config, context_path)
        
        input_node = self._create_node(
            node_type='input',
            node_id='.'.join(context_path),
            config=config,
            context_path=context_path,
            dependencies=dependencies,
            # Metadata specific to input nodes
            is_mesh_array=True,
            array_type=array_type,
            src=src
        )

        self.node_data.append(input_node)
        
        return input_node

    
    def _parse_pipe(self, pipe_config: Any, context_path: List[str], array_type: str = None):

        # Handle different input formats
        if isinstance(pipe_config, dict):
            config = pipe_config.copy()
            processor = pipe_config.pop('processor')
        else:
            raise ValueError(f"Invalid pipe configuration: {pipe_config}. Expected dict format.")
        
        # Extract dependencies
        dependencies = self._extract_dependencies(config, context_path)
        
        node = self._create_node(
            node_type='pipe',
            node_id='.'.join(context_path),
            config=config,
            context_path=context_path,
            dependencies=dependencies,
            # Metadata specific to input nodes
            processor=processor,
        )

        self.node_data.append(node)
        
        return node

    
    def _create_node(self, node_type: str, node_id: str, config: Any, context_path: List[str], 
                 dependencies: List[str] = None, **metadata) -> Dict[str, Any]:
        """Create a standardized node with common fields."""
        
        return {
            'id': node_id,
            'type': node_type,
            'config': config,
            'context_path': context_path,
            'dependencies': dependencies or [],
            'schema_validated': True,
            'parser_metadata': {
                'parsed_at': datetime.now().isoformat(),
                'parser_version': '2.0',
                **metadata  # Additional metadata passed by caller
            }
        }
    
    def _parse_pipeline(self, pipeline_config: Dict[str, Any], context_path: List[str], array_type: str = None):

        # Extract input and pipeline components
        input_part = pipeline_config.get('input')
        pipeline_part = pipeline_config.get('pipeline', [])
        
        # Parse input dependency if exists
        input_dependencies = []
        if input_part:
            input_context = context_path + ['input']
            input_node = self._parse_input(input_part, input_context, f"{array_type}_input")
            input_dependencies.append(input_node['id'])
        
        # Extract dependencies from pipeline steps
        pipeline_dependencies = []
        for i, pipe in enumerate(pipeline_part):
            pipe_context = context_path + [f'pipe{i}']
            pipe_node = self._parse_pipe(pipe, pipe_context, f"{array_type}_pipe{i}")
            pipeline_dependencies.append(pipe_node['id'])
        
        # Combine all dependencies
        all_dependencies = input_dependencies + pipeline_dependencies
        
        pipeline_node = {
            'id': '.'.join(context_path),
            'type': 'pipeline',
            'config': pipeline_config,
            'context_path': context_path,
            'dependencies': all_dependencies,
            'schema_validated': True,
            'parser_metadata': {
                'parsed_at': datetime.now().isoformat(),
                'parser_version': '2.0',
                'is_mesh_array': True,
                'array_type': array_type,
                'has_input': input_part is not None,
                'pipeline_steps': len(pipeline_part),
                'processors': [step.get('processor') for step in pipeline_part if isinstance(step, dict) and 'processor' in step]
            }
        }

        self.node_data.append(pipeline_node)
        
        return pipeline_node

    
    
    def _extract_dependencies(self, config: Dict[str, Any], context_path: List[str]) -> List[str]:
        """Extract dependencies from configuration."""
        dependencies = []
        
        # Look for node references (strings starting with '@')
        def find_refs(obj):
            if isinstance(obj, str) and obj.startswith('@'):
                # Remove the '@' and add to dependencies
                dep_id = obj[1:]  # Remove '@' prefix
                if dep_id not in dependencies:
                    dependencies.append(dep_id)
            elif isinstance(obj, dict):
                for v in obj.values():
                    find_refs(v)
            elif isinstance(obj, list):
                for item in obj:
                    find_refs(item)
        
        find_refs(config)
        
        # Add context-specific dependencies
        # if len(context_path) > 1:
        #     # If this is a sub-node, it depends on its parent
        #     parent_path = context_path[:-1]
        #     parent_id = '.'.join(parent_path)
        #     if parent_id not in dependencies:
        #         dependencies.append(parent_id)
        
        return dependencies

    def get_all_nodes(self) -> List[Dict[str, Any]]:
        """Get all parsed node data (data mode only)."""
        return self.node_data.copy()
    
    def clear_all_node_data(self):
        """Clear all parsed node data."""
        self.node_data.clear()