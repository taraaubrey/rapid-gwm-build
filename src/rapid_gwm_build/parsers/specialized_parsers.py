"""
Specialized parsers for different node types.
Each parser handles the specific logic for creating and configuring its node type.
"""

import logging
from typing import Dict, Any, List, Optional, Union
from abc import ABC, abstractmethod

from .node_schemas import NodeSchemas
from rapid_gwm_build.nodes.node_cfg import NodeFactory


class BaseNodeParser(ABC):
    """Base class for all node parsers."""
    
    def __init__(self, node_factory=None):
        self.node_factory = node_factory or NodeFactory
        self.created_nodes = []
    
    @abstractmethod
    def parse(self, config: Dict[str, Any], **kwargs) -> str:
        """Parse configuration and return node reference ID."""
        pass
    
    def validate_config(self, node_type: str, config: Dict[str, Any]) -> None:
        """Validate configuration against schema."""
        is_valid, error_msg = NodeSchemas.validate_config(node_type, config)
        if not is_valid:
            raise ValueError(f"Invalid {node_type} configuration: {error_msg}")
    
    def get_dependencies(self, node_type: str, config: Dict[str, Any]) -> List[str]:
        """Get dependencies for this node."""
        return NodeSchemas.get_dependencies(node_type, config)
    
    def clear_nodes(self):
        """Clear created nodes."""
        self.created_nodes.clear()
    
    def get_nodes(self):
        """Get all created nodes."""
        return self.created_nodes


class InputNodeParser(BaseNodeParser):
    """Parser for Input nodes."""
    
    def parse(self, config: Dict[str, Any], 
              context_path: List[str] = None, **kwargs) -> str:
        """
        Parse input node configuration.
        
        Args:
            config: Input configuration
            context_path: Context path for this node
            **kwargs: Additional arguments
            
        Returns:
            str: Reference ID of created input node
        """
        # For input nodes, the config might be the src directly
        if isinstance(config, (str, int, float, list)):
            src = config
            node_config = {'src': src}
        else:
            node_config = config.copy()
        
        self.validate_config('input', node_config)
        
        node = self.node_factory.build_node(
            node_type='input',
            src=node_config.get('src'),
            attr=context_path
        )
        
        self.created_nodes.append(node)
        return node.ref_id


class PipeNodeParser(BaseNodeParser):
    """Parser for Pipe nodes."""
    
    def parse(self, config: Dict[str, Any], processor: str = None,
              input_id: str = None, context_path: List[str] = None, **kwargs) -> str:
        """
        Parse pipe node configuration.
        
        Args:
            config: Pipe configuration
            processor: Processor name (can be in config or separate)
            input_id: Input node reference ID
            context_path: Context path for this node
            **kwargs: Additional arguments
            
        Returns:
            str: Reference ID of created pipe node
        """
        # Processor can come from config or parameter
        if processor is None:
            processor = config.get('processor')
        
        if not processor:
            raise ValueError("Pipe configuration must include 'processor'")
        
        # Validate configuration
        pipe_config = config.copy()
        pipe_config['processor'] = processor
        if input_id:
            pipe_config['input_id'] = input_id
        
        self.validate_config('pipe', pipe_config)
        
        # Handle module path for processors
        module_path = None
        if '.' in processor:
            module_path = processor
            processor = processor.split('.')[-1]
        
        # Build attribute path
        if context_path:
            pipe_attr = context_path + [processor]
        else:
            pipe_attr = [processor]
        
        node = self.node_factory.build_node(
            node_type='pipe',
            attr=pipe_attr,
            input_id=input_id,
            src=config,
            module_path=module_path
        )
        
        self.created_nodes.append(node)
        return node.ref_id


class MeshNodeParser(BaseNodeParser):
    """Parser for Mesh nodes."""
    
    def parse(self, config: Dict[str, Any], param: str = None,
              context_path: List[str] = None, **kwargs) -> str:
        """
        Parse mesh node configuration.
        
        Args:
            config: Mesh configuration
            param: Specific mesh parameter (for sub-mesh nodes)
            context_path: Context path for this node
            **kwargs: Additional arguments
            
        Returns:
            str: Reference ID of created mesh node
        """
        self.validate_config('mesh', config)
        
        node = self.node_factory.build_node(
            node_type='mesh',
            src=config,
            param=param,
            attr=context_path
        )
        
        self.created_nodes.append(node)
        return node.ref_id


class ModuleNodeParser(BaseNodeParser):
    """Parser for Module nodes."""
    
    def parse(self, config: Dict[str, Any], module_key: str,
              context_path: List[str] = None, **kwargs) -> str:
        """
        Parse module node configuration.
        
        Args:
            config: Module configuration
            module_key: Module identifier
            context_path: Context path for this node
            **kwargs: Additional arguments
            
        Returns:
            str: Reference ID of created module node
        """
        module_config = config.copy()
        module_config['module_key'] = module_key
        
        self.validate_config('module', module_config)
        
        node = self.node_factory.build_node(
            node_type='module',
            module_key=module_key,
            src=config,
            attr=context_path
        )
        
        self.created_nodes.append(node)
        return node.ref_id


class SourceNodeParser(BaseNodeParser):
    """Parser for Source/Data nodes."""
    
    def parse(self, config: Dict[str, Any], data_type: str = None,
              context_path: List[str] = None, **kwargs) -> str:
        """
        Parse source node configuration.
        
        Args:
            config: Source configuration
            data_type: Type of data source
            context_path: Context path for this node
            **kwargs: Additional arguments
            
        Returns:
            str: Reference ID of created source node
        """
        source_config = config.copy()
        if data_type:
            source_config['data_type'] = data_type
        
        self.validate_config('source', source_config)
        
        node = self.node_factory.build_node(
            node_type='source',
            src=config,
            attr=context_path
        )
        
        self.created_nodes.append(node)
        return node.ref_id


class TemplateNodeParser(BaseNodeParser):
    """Parser for Template nodes."""
    
    def parse(self, config: Dict[str, Any], module_key: str,
              context_path: List[str] = None, **kwargs) -> str:
        """
        Parse template node configuration.
        
        Args:
            config: Template configuration
            module_key: Module identifier
            context_path: Context path for this node
            **kwargs: Additional arguments
            
        Returns:
            str: Reference ID of created template node
        """
        template_config = config.copy()
        template_config['module_key'] = module_key
        
        self.validate_config('template', template_config)
        
        node = self.node_factory.build_node(
            node_type='template',
            module_key=module_key,
            src=config,
            attr=context_path
        )
        
        self.created_nodes.append(node)
        return node.ref_id


class NodeParserRegistry:
    """Registry for all node parsers."""
    
    def __init__(self, node_factory=None):
        self.node_factory = node_factory or NodeFactory
        self._parsers = {
            'input': InputNodeParser(self.node_factory),
            'pipe': PipeNodeParser(self.node_factory),
            'mesh': MeshNodeParser(self.node_factory),
            'module': ModuleNodeParser(self.node_factory),
            'modules': ModuleNodeParser(self.node_factory),  # Alias
            'source': SourceNodeParser(self.node_factory),
            'template': TemplateNodeParser(self.node_factory),
        }
    
    def get_parser(self, node_type: str) -> Optional[BaseNodeParser]:
        """Get parser for a specific node type."""
        return self._parsers.get(node_type)
    
    def parse_node(self, node_type: str, config: Dict[str, Any], **kwargs) -> str:
        """Parse a node using the appropriate parser."""
        parser = self.get_parser(node_type)
        if not parser:
            raise ValueError(f"No parser available for node type: {node_type}")
        
        return parser.parse(config, **kwargs)
    
    def get_all_created_nodes(self) -> List:
        """Get all nodes created by all parsers."""
        all_nodes = []
        for parser in self._parsers.values():
            all_nodes.extend(parser.get_nodes())
        return all_nodes
    
    def clear_all_nodes(self):
        """Clear all created nodes from all parsers."""
        for parser in self._parsers.values():
            parser.clear_nodes()
