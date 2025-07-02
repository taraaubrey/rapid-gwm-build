"""
Simplified node parser without from_node dependency.
Uses context paths and explicit node relationships instead.
"""

import logging
from typing import Dict, Any, List, Optional, Union
from copy import deepcopy

from ..node_schemas import NodeSchemas
from ..specialized_parsers import NodeParserRegistry
from ..pipeline_parser import PipelineParser
from rapid_gwm_build.nodes.node_cfg import NodeFactory


class SimplifiedNodeParser:
    """
    Simplified NodeParser that eliminates from_node complexity.
    Uses context paths and explicit relationships instead.
    """
    
    def __init__(self, node_factory=None):
        self.node_factory = node_factory or NodeFactory
        self.nodes = []
        self.context_stack = []  # Track parsing context instead of from_node
        
        # Initialize specialized parsers (simplified versions)
        self.parser_registry = NodeParserRegistry(self.node_factory)
        
        # Initialize pipeline parser with simplified dependencies
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
            node_type: Type of node to create
            config: Node configuration
            context_path: Current parsing context path (replaces from_node)
            **kwargs: Additional arguments
            
        Returns:
            str: Reference ID of the created node
        """
        if config is None:
            logging.warning(f"Node configuration for {node_type} is None.")
            return None
        
        # Set context
        context_path = context_path or []
        self.context_stack.append(context_path)
        
        try:
            # Convert simple values to dict format
            if not isinstance(config, dict):
                config = {'src': config}
            
            # Route to appropriate parser based on node type
            if node_type == 'pipeline':
                return self.parse_pipeline(config, context_path, **kwargs)
            elif node_type in ['modules', 'module']:
                return self.parse_modules(config, context_path, **kwargs)
            elif node_type == 'mesh':
                return self.parse_mesh(config, context_path, **kwargs)
            elif node_type == 'input':
                return self.parse_input(config, context_path, **kwargs)
            elif node_type == 'pipe':
                return self.parse_pipe(config, context_path, **kwargs)
            else:
                # Default to input parser
                logging.warning(f"Unknown node type {node_type}, treating as input")
                return self.parse_input(config, context_path, **kwargs)
        
        finally:
            # Clean up context
            self.context_stack.pop()
    
    def parse_modules(self, modules_config: Dict[str, Any], 
                     context_path: List[str] = None, **kwargs):
        """Parse modules configuration."""
        if not isinstance(modules_config, dict):
            raise ValueError(f"Modules configuration must be a dictionary")
        
        context_path = context_path or []
        created_modules = []
        
        for module_key, module_cfg in modules_config.items():
            module_context = context_path + ['modules', module_key]
            ref_id = self.parse_module(module_key, module_cfg, module_context)
            created_modules.append(ref_id)
        
        return created_modules
    
    def parse_module(self, module_key: str, module_config: Dict[str, Any], 
                     context_path: List[str] = None):
        """Parse a single module configuration."""
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
            context_path=context_path,
            src_arg=True
        )
        node.src = updated_src
        
        self.nodes.append(node)
        return node.ref_id
    
    def parse_mesh(self, mesh_config: Dict[str, Any], 
                   context_path: List[str] = None):
        """Parse mesh configuration."""
        context_path = context_path or ['mesh']
        
        # Create main mesh node
        mesh_node = self.node_factory.build_node(
            node_type='mesh',
            attr=context_path
        )
        
        # Parse mesh configuration recursively
        updated_src = self.parse_dict(
            cfg_dict=mesh_config,
            context_path=context_path,
            src_arg=False
        )
        mesh_node.src = updated_src
        
        self.nodes.append(mesh_node)
        return mesh_node.ref_id
    
    def parse_pipeline(self, pipeline_config: Dict[str, Any], 
                      context_path: List[str] = None, **kwargs):
        """Parse pipeline configuration."""
        context_path = context_path or ['pipeline']
        
        # Use the pipeline parser (it can handle its own node creation)
        ref_id = self.pipeline_parser.parse_pipeline(
            src=pipeline_config,
            attr=context_path,
            **kwargs
        )
        
        # Collect nodes from pipeline parser
        self.nodes.extend(self.pipeline_parser.get_nodes())
        self.pipeline_parser.clear_nodes()
        
        return ref_id
    
    def parse_input(self, config: Union[Dict[str, Any], Any], 
                   context_path: List[str] = None, src_arg: bool = False, **kwargs):
        """Parse input node configuration."""
        context_path = context_path or ['input']
        
        # Handle different input formats
        if isinstance(config, dict):
            src = config.get('src', config)
            src_arg = config.get('src_arg', src_arg)
        else:
            src = config
        
        # Create input node
        node = self.node_factory.build_node(
            node_type='input',
            src_arg=src_arg,
            src=src,
            attr=context_path
        )
        
        # Parse nested dictionaries if needed
        if not src_arg and isinstance(src, dict):
            updated_src = self.parse_dict(
                cfg_dict=src,
                context_path=context_path,
                src_arg=src_arg
            )
            node.src = updated_src
        
        self.nodes.append(node)
        return node.ref_id
    
    def parse_pipe(self, config: Dict[str, Any], 
                   context_path: List[str] = None, 
                   processor: str = None, input_id: str = None, **kwargs):
        """Parse pipe node configuration."""
        context_path = context_path or ['pipe']
        
        # Get processor from config or parameter
        if processor is None:
            processor = config.get('processor')
        
        if not processor:
            raise ValueError("Pipe configuration must include 'processor'")
        
        # Handle module path
        module_path = None
        if '.' in processor:
            module_path = processor
            processor = processor.split('.')[-1]
        
        # Build context path with processor
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
                context_path=pipe_context,
                src_arg=False
            )
            pipe_node.src = updated_src
        
        self.nodes.append(pipe_node)
        return pipe_node.ref_id
    
    def parse_dict(self, cfg_dict: Dict[str, Any], 
                   context_path: List[str] = None, 
                   src_arg: bool = False, **kwargs):
        """Recursively parse a configuration dictionary."""
        context_path = context_path or []
        updated_refs = {}
        
        for k, v in cfg_dict.items():
            # Build new context path
            item_context = context_path + [k]
            
            # Parse the value based on its type and context
            ref_id = self._parse_value(
                key=k,
                value=v,
                context_path=item_context,
                src_arg=src_arg
            )
            
            updated_refs[k] = ref_id
        
        return updated_refs
    
    def _parse_value(self, key: str, value: Any, 
                     context_path: List[str], src_arg: bool = False):
        """Parse a single value from a configuration dictionary."""
        
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
                    context_path=context_path,
                    src_arg=src_arg
                )
            else:
                # Parse as input node
                return self.parse_input(
                    config=value,
                    context_path=context_path,
                    src_arg=src_arg
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
