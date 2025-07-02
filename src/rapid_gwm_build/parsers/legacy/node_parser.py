"""
Refactored NodeParser that orchestrates specialized parsers and handles dependencies.
Removed from_node complexity in favor of explicit context paths.
"""

import logging
from typing import Dict, Any, List, Optional, Union
from copy import deepcopy

from .node_schemas import NodeSchemas
from .specialized_parsers import NodeParserRegistry
from .pipeline_parser import PipelineParser
from rapid_gwm_build.nodes.node_cfg import NodeFactory


class NodeParser:
    """
    Main orchestrator for parsing all node types with dependency management.
    Uses explicit context paths instead of from_node for cleaner architecture.
    """
    
    def __init__(self, node_factory=None):
        self.node_factory = node_factory or NodeFactory
        self.nodes = []
        
        # Initialize specialized parsers
        self.parser_registry = NodeParserRegistry(self.node_factory)
        
        # Initialize pipeline parser with dependencies
        self.pipeline_parser = PipelineParser(
            node_factory=self.node_factory,
            input_parser=self.parse_input,
            pipe_parser=self.parse_pipe
        )
    
    def parse_node(self, node_type: str, config: Union[Dict[str, Any], Any], 
                   context_path: List[str] = None, **kwargs) -> str:
        """
        Main entry point for parsing any node type.
        
        Args:
            node_type: Type of node to create ('mesh', 'module', 'pipeline', etc.)
            config: Node configuration (dict or raw value for simple nodes)
            context_path: Current parsing context path (replaces from_node)
            **kwargs: Additional arguments specific to node type
            
        Returns:
            str: Reference ID of the created node
        """
        if config is None:
            logging.warning(f"Node configuration for {node_type} is None.")
            return None
        
        # Set default context if not provided
        context_path = context_path or [node_type]
        
        # Convert simple values to dict format
        if not isinstance(config, dict):
            config = {'src': config}
        
        # Route to appropriate parser
        if node_type == 'pipeline':
            return self.parse_pipeline(config, context_path, **kwargs)
        elif node_type in ['modules', 'module']:
            return self.parse_modules(config, context_path, **kwargs)
        elif node_type == 'mesh':
            return self.parse_mesh(config, context_path, **kwargs)
        else:
            # Use specialized parsers for other types
            parser = self.parser_registry.get_parser(node_type)
            if parser:
                ref_id = parser.parse(config, context_path=context_path, **kwargs)
                self.nodes.extend(parser.get_nodes())
                parser.clear_nodes()
                return ref_id
            else:
                logging.warning(f"Unsupported node type: {node_type}")
                return self.parse_input(config, context_path, **kwargs)
    
    def parse_modules(self, modules_config: Dict[str, Any], 
                     context_path: List[str] = None, **kwargs):
        """
        Parse modules configuration. Can handle single module or multiple modules.
        
        Args:
            modules_config: Dictionary of module configurations
            context_path: Current parsing context path
            
        Returns:
            List of reference IDs for created modules
        """
        if not isinstance(modules_config, dict):
            raise ValueError(f"Modules configuration must be a dictionary, got {type(modules_config)}")
        
        context_path = context_path or ['modules']
        created_modules = []
        
        for module_key, module_cfg in modules_config.items():
            module_context = context_path + [module_key]
            ref_id = self.parse_module(module_key, module_cfg, module_context)
            created_modules.append(ref_id)
        
        return created_modules
    
    def parse_module(self, module_key: str, module_config: Dict[str, Any], 
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
        
        # Create the module node (no from_node needed)
        node = self.node_factory.build_node(
            node_type='module', 
            module_key=module_key,
            attr=context_path
        )
        
        # Parse the module configuration recursively
        updated_src = self.parse_dict(
            cfg_dict=module_config, 
            context_path=context_path
        )
        node.src = updated_src
        
        self.nodes.append(node)
        return node.ref_id
    
    def parse_mesh(self, mesh_config: Dict[str, Any], 
                   context_path: List[str] = None):
        """
        Parse mesh configuration.
        
        Args:
            mesh_config: Mesh configuration dict
            context_path: Current parsing context path
            
        Returns:
            str: Reference ID of created mesh node
        """
        context_path = context_path or ['mesh']
        
        # Create main mesh node
        mesh_node = self.node_factory.build_node(
            node_type='mesh',
            attr=context_path
        )
        
        # Parse mesh configuration recursively
        updated_src = self.parse_dict(
            cfg_dict=mesh_config, 
            context_path=context_path
        )
        mesh_node.src = updated_src
        
        self.nodes.append(mesh_node)
        return mesh_node.ref_id
    
    def parse_pipeline(self, pipeline_config: Dict[str, Any], 
                      context_path: List[str] = None, **kwargs):
        """
        Parse pipeline configuration using the dedicated PipelineParser.
        
        Args:
            pipeline_config: Pipeline configuration dict
            context_path: Current parsing context path
            **kwargs: Additional arguments
            
        Returns:
            str: Reference ID of created pipeline node
        """
        context_path = context_path or ['pipeline']
        
        ref_id = self.pipeline_parser.parse_pipeline(
            src=pipeline_config, 
            attr=context_path,
            **kwargs
        )
        
        # Add the nodes created by the pipeline parser to our nodes list
        self.nodes.extend(self.pipeline_parser.get_nodes())
        self.pipeline_parser.clear_nodes()  # Clear to avoid duplicates
        
        return ref_id
    
    def parse_input(self, config: Union[Dict[str, Any], Any], 
                   context_path: List[str] = None, **kwargs):
        """
        Parse input node configuration.
        
        Args:
            config: Source data or input configuration
            context_path: Current parsing context path
            **kwargs: Additional arguments
            
        Returns:
            str: Reference ID of created input node
        """
        context_path = context_path or ['input']
        
        # Handle different input formats
        if isinstance(config, dict):
            src = config.get('src', config)
        else:
            src = config
        
        node = self.node_factory.build_node(
            node_type='input', 
            src=src, 
            attr=context_path
        )
        
        if isinstance(src, dict):
            updated_src = self.parse_dict(
                cfg_dict=src, 
                context_path=context_path
            )
            node.src = updated_src
        
        self.nodes.append(node)
        return node.ref_id
    
    def parse_pipe(self, config: Dict[str, Any], 
                   context_path: List[str] = None,
                   processor: str = None, input_id: str = None, **kwargs):
        """
        Parse pipe node configuration.
        
        Args:
            config: Pipe configuration
            context_path: Current parsing context path
            processor: Processor name (can be in config or parameter)
            input_id: Input node reference
            **kwargs: Additional arguments
            
        Returns:
            str: Reference ID of created pipe node
        """
        # Get processor from config or parameter
        if processor is None:
            processor = config.get('processor')
        
        if not processor:
            raise ValueError("Processor is required for pipe nodes")
        
        # Handle module path for processors
        module_path = None
        if '.' in processor:
            module_path = processor
            processor = processor.split('.')[-1]
        
        # Build context path with processor
        context_path = context_path or ['pipe']
        pipe_context = context_path + [processor]
        
        # Create pipe node
        pipe_node = self.node_factory.build_node(
            node_type='pipe', 
            attr=pipe_context,
            input_id=input_id, 
            src=config, 
            module_path=module_path
        )
        
        # Parse source configuration if provided
        src = config.copy()
        src.pop('processor', None)  # Remove processor from src
        
        if src:
            updated_src = self.parse_dict(
                cfg_dict=src, 
                context_path=pipe_context
            )
            pipe_node.src = updated_src
        
        self.nodes.append(pipe_node)
        return pipe_node.ref_id
    
    def parse_dict(self, cfg_dict: Dict[str, Any], 
                   context_path: List[str] = None, **kwargs):
        """
        Recursively parse a configuration dictionary.
        
        Args:
            cfg_dict: Configuration dictionary to parse
            context_path: Current parsing context path
            **kwargs: Additional arguments
            
        Returns:
            Dict: Updated dictionary with node references
        """
        context_path = context_path or []
        updated_refs = {}
        
        for k, v in cfg_dict.items():
            # Build item context path
            item_context = context_path + [k]
            
            # Handle different value types
            ref_id = self._parse_value(
                key=k, 
                value=v, 
                context_path=item_context
            )
            
            updated_refs[k] = ref_id
        
        return updated_refs
    
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
    
    def get_all_nodes(self) -> List:
        """Get all created nodes."""
        all_nodes = self.nodes.copy()
        all_nodes.extend(self.parser_registry.get_all_created_nodes())
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
