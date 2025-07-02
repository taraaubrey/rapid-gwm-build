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
        elif node_type == 'pipeline':
            return self._parse_pipeline_data_mode(config, context_path)
        elif node_type == 'modules':
            return self._parse_modules(config, context_path, **kwargs)
        elif node_type == 'input':
            return self._parse_input(config, context_path)
        else:
            raise ValueError(f'Unsupported node type: {node_type}. Supported types are: mesh, pipeline, modules, input.')
            # For generic node types, validate and extract dependencies here
            # if not self._validate_config(node_type, config):
            #     return None
            
            # dependencies = self._extract_dependencies(config, context_path)
            # node_id = self._generate_node_id(node_type, context_path)
            
            # # Return generic structured dict data for other types
            # node_data = {
            #     'id': node_id,
            #     'type': node_type,
            #     'config': deepcopy(config),
            #     'context_path': context_path.copy(),
            #     'dependencies': dependencies,
            #     'schema_validated': True,
            #     'parser_metadata': {
            #         'parsed_at': datetime.now().isoformat(),
            #         'parser_version': '2.0',
            #         'context_path': context_path
            #     }
            # }
            
            # # Add any type-specific metadata
            # node_data.update(self._get_type_specific_metadata(node_type, config, kwargs))
            
            # self.node_data.append(node_data)
            # return node_data
    
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

        # get template data
        module_config['template'] = self.sim_template.get('modules', {}).get(module_key, {})
        
        # validate the module configuration
        NodeSchemas.validate_config_strict('module', module_config, context_path)
        
        # is_valid, error_msg = NodeSchemas.validate_config('module', module_config)
        # if not is_valid:
        #     logging.error(f"Mesh validation failed: {error_msg}")
        #     raise ValueError(f"Invalid mesh configuration: {error_msg}")

        src_config = module_config.get('src', {})
        cmd_config = module_config.get('cmd', {})
        
        dependencies = self._extract_dependencies(module_config, context_path)
        
        module_node = self._create_node(
            node_type='module',
            node_id='.'.join(context_path),
            config=module_config,
            context_path=context_path,
            dependencies=dependencies,
            # Metadata specific to module nodes
            src_config=src_config,
            cmd_config=cmd_config
        )

    
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
        
        # Parse mesh data arrays (each can be Input or Pipeline)
        mesh_data_nodes = []
        array_dependencies = []
        
        for array_key, array_value in mesh_data.items():
            array_context = context_path + [array_key]

            if self._is_node_type('pipeline', array_value):
                # Parse as pipeline node
                pipeline_node = self._parse_pipeline(array_value, array_context, array_key)
                mesh_data_nodes.append(pipeline_node)
                array_dependencies.extend(pipeline_node['dependencies'])
                array_dependencies.append(pipeline_node['id'])
            
            else:
                # Parse as input node
                input_node = self._parse_input(array_value, array_context, array_key)
                mesh_data_nodes.append(input_node)
                array_dependencies.append(input_node['id'])
        
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
        self.node_data.extend(mesh_data_nodes)
        
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
            self.node_data.append(input_node)
            input_dependencies.append(input_node['id'])
        
        # Extract dependencies from pipeline steps
        pipeline_dependencies = []
        for i, pipe in enumerate(pipeline_part):
            pipe_context = context_path + [f'pipe{i}']
            pipe_node = self._parse_pipe(pipe, pipe_context, f"{array_type}_pipe{i}")
            self.node_data.append(pipe_node)
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
        
        return pipeline_node
    
    def _parse_value(self, key: str, value: Any, 
                     context_path: List[str]):
        """
        Parse a single value from a configuration dictionary.
        
        Args:
            key: Configuration key
            value: Configuration value
            context_path: Current parsing context path
            
        Returns:
            Parsed value or node reference
        """
        # Handle node references (strings starting with '@')
        if isinstance(value, str) and value.startswith('@'):
            return value
        
        # Handle pipeline configurations
        if isinstance(value, dict) and 'pipeline' in value:
            pipeline_src = value.get('pipeline')
            return self.parse_pipeline(
                pipeline_config=pipeline_src, 
                context_path=context_path
            )
        
        # Handle mesh-specific configurations (context-aware)
        if self._is_mesh_context(context_path) and key in ['top', 'bottoms']:
            return self._parse_mesh_component(key, value, context_path)
        
        # Handle nested dictionaries
        if isinstance(value, dict):
            if key == 'src':
                return self.parse_dict(
                    cfg_dict=value, 
                    context_path=context_path
                )
            else:
                # Parse as input by default
                return self.parse_input(
                    config=value, 
                    context_path=context_path
                )
        
        # Return primitive values as-is
        return value
    
    def _is_mesh_context(self, context_path: List[str]) -> bool:
        """Check if we're in a mesh parsing context."""
        return len(context_path) > 0 and context_path[0] == 'mesh'
    
    def _parse_mesh_component(self, component: str, value: Any, 
                             context_path: List[str]):
        """Parse mesh component (top/bottoms) with special handling."""
        component_context = context_path + [component]
        
        # Create mesh component node
        mesh_component = self.node_factory.build_node(
            node_type='mesh',
            attr=component_context,
            src=value,
            param=component
        )
        
        # Handle pipeline in mesh component
        if isinstance(value, dict) and 'pipeline' in value:
            pipeline_src = value.get('pipeline')
            ref_id = self.parse_pipeline(
                pipeline_config=pipeline_src,
                context_path=component_context
            )
            mesh_component.src = ref_id
        
        self.nodes.append(mesh_component)
        return mesh_component.ref_id
    
    def _validate_config(self, node_type: str, config: Dict[str, Any]) -> bool:
        """Validate configuration against schema."""
        try:
            is_valid, error_msg = NodeSchemas.validate_config(node_type, config)
            if not is_valid:
                logging.error(f"Configuration validation failed for {node_type}: {error_msg}")
                return False
            return True
        except Exception as e:
            logging.error(f"Schema validation error for {node_type}: {e}")
            return False
    
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
    
    def _generate_node_id(self, node_type: str, context_path: List[str]) -> str:
        """Generate a unique node ID from context path."""
        if len(context_path) == 1:
            return context_path[0]
        else:
            return '.'.join(context_path)
    
    def _get_type_specific_metadata(self, node_type: str, config: Dict[str, Any], kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Get type-specific metadata for different node types."""
        metadata = {}
        
        if node_type == 'module':
            metadata['module_key'] = kwargs.get('module_key') or config.get('module_key')
        elif node_type == 'pipe':
            metadata['processor'] = config.get('processor') or kwargs.get('processor')
            metadata['input_id'] = kwargs.get('input_id')
        elif node_type == 'mesh':
            metadata['param'] = kwargs.get('param')
        elif node_type == 'pipeline':
            metadata['pipeline_type'] = 'custom' if 'pipeline' in config else 'builtin'
        
        return metadata

    def get_all_node_data(self) -> List[Dict[str, Any]]:
        """Get all parsed node data (data mode only)."""
        return self.node_data.copy()
    
    def clear_all_node_data(self):
        """Clear all parsed node data."""
        self.node_data.clear()
    
    def get_dependencies_graph(self) -> Dict[str, List[str]]:
        """Get a dependency graph from all parsed nodes."""
        graph = {}
        for node_data in self.node_data:
            graph[node_data['id']] = node_data['dependencies']
        return graph

    def get_all_nodes(self) -> List:
        """Get all created nodes."""
        all_nodes = self.node_data.copy()
        return all_nodes
    
    def clear_all_nodes(self):
        """Clear all created nodes."""
        self.nodes.clear()
        self.parser_registry.clear_all_nodes()
        self.pipeline_parser.clear_nodes()
    
    def get_dependencies_for_config(self, node_type: str, config: Dict[str, Any]) -> List[str]:
        """Get dependencies for a given configuration."""
        return NodeSchemas.get_dependencies(node_type, config)
    
    def validate_config(self, node_type: str, config: Dict[str, Any]) -> bool:
        """Validate a configuration against its schema."""
        is_valid, error_msg = NodeSchemas.validate_config(node_type, config)
        if not is_valid:
            logging.error(f"Configuration validation failed: {error_msg}")
            return False
        return True
