import logging
from typing import Dict, Tuple, Any, List, Optional


class PipelineParser:
    """
    A dedicated parser class for handling pipeline configurations.
    Manages both built-in pipeline references and custom pipeline definitions.
    """
    
    # Schema definition for pipeline nodes
    pipeline_schema = {
        # Full pipeline definition with input and pipeline steps
        'input': 'required_with_pipeline',
        'pipeline': 'required_with_input',
        
        # Built-in pipeline references
        'builtin_pipelines': ['only_top'],  # List of valid built-in pipeline names
        
        # Validation rules
        'validation': {
            'either_or': [
                ['input', 'pipeline'],  # Both input and pipeline required together
                'builtin_pipelines'     # OR a built-in pipeline reference
            ]
        }
    }
    
    def __init__(self, node_factory, input_parser, pipe_parser):
        """
        Initialize the PipelineParser with required dependencies.
        
        Args:
            node_factory: Factory for creating nodes
            input_parser: Function to parse input configurations
            pipe_parser: Function to parse pipe configurations
        """
        self.node_factory = node_factory
        self.input_parser = input_parser
        self.pipe_parser = pipe_parser
        self.nodes = []
    
    def validate_pipeline_config(self, config: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validates pipeline configuration against the pipeline_schema.
        
        Args:
            config (dict): Pipeline configuration to validate
            
        Returns:
            tuple: (is_valid: bool, error_message: str)
        """
        if not isinstance(config, dict):
            return False, "Pipeline configuration must be a dictionary"
        
        # Check if it's a built-in pipeline reference
        builtin_pipelines = self.pipeline_schema.get('builtin_pipelines', [])
        
        # Check if any key in config matches a built-in pipeline
        for key in config.keys():
            if key in builtin_pipelines:
                return True, ""
        
        # Check if both 'input' and 'pipeline' are present
        has_input = 'input' in config
        has_pipeline = 'pipeline' in config
        
        if has_input and has_pipeline:
            return True, ""
        elif has_input and not has_pipeline:
            return False, "Pipeline configuration with 'input' requires 'pipeline' to be specified"
        elif has_pipeline and not has_input:
            return False, "Pipeline configuration with 'pipeline' requires 'input' to be specified"
        else:
            valid_options = ", ".join(builtin_pipelines) if builtin_pipelines else "none available"
            return False, f"Pipeline configuration must have either ('input' AND 'pipeline') or use a built-in pipeline ({valid_options})"
    
    def get_builtin_pipeline(self, pipeline_name: str) -> Dict[str, Any]:
        """
        Returns the configuration for a built-in pipeline.
        
        Args:
            pipeline_name (str): Name of the built-in pipeline
            
        Returns:
            dict: Pipeline configuration
        """
        builtin_configs = {
            'only_top': {
                'input': {'type': 'mesh_layer', 'layer': 'top'},
                'pipeline': [
                    {'processor': 'extract_layer'},
                    {'processor': 'validate_data'}
                ]
            }
            # Add more built-in pipelines here as needed
        }
        
        return builtin_configs.get(pipeline_name, {})
    
    def is_builtin_pipeline(self, config: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Check if the configuration contains a built-in pipeline reference.
        
        Args:
            config (dict): Pipeline configuration
            
        Returns:
            tuple: (is_builtin: bool, pipeline_name: str or None)
        """
        builtin_pipelines = self.pipeline_schema.get('builtin_pipelines', [])
        
        for key in config.keys():
            if key in builtin_pipelines:
                return True, key
        
        return False, None
    
    def parse_builtin_pipeline(self, pipeline_name: str, config: Dict[str, Any], 
                             context_path: List[str] = None) -> str:
        """
        Parse a built-in pipeline reference.
        
        Args:
            pipeline_name (str): Name of the built-in pipeline
            config (dict): Pipeline configuration
            context_path: Context path for this node
            
        Returns:
            str: Reference ID of the created pipeline node
        """
        pipeline_node = self.node_factory.build_node(
            node_type='pipeline', 
            src={pipeline_name: config[pipeline_name]}, 
            attr=context_path, 
            builtin_pipeline=pipeline_name
        )
        
        self.nodes.append(pipeline_node)
        return pipeline_node.ref_id
    
    def parse_custom_pipeline(self, config: Dict[str, Any], context_path: List[str] = None) -> str:
        """
        Parse a custom pipeline with input and pipeline steps.
        
        Args:
            config (dict): Pipeline configuration
            context_path: Context path for this node
            
        Returns:
            str: Reference ID of the created pipeline node
        """
        # Handle input
        in_attr = ['pipeline', 'input']
        if isinstance(context_path, list):
            in_attr.extend(context_path)
            
        if 'input' in config:
            src_input = config.pop('input')
            in_ref_id = self.input_parser(
                config=src_input, context_path=in_attr)
        else:
            in_ref_id = None
        
        # Create pipeline node
        pipeline_node = self.node_factory.build_node(
            node_type='pipeline', src=config, attr=context_path)

        # Parse pipeline steps
        pipes = []
        pipeline_steps = config.get('pipeline', [])
        
        for pipe_cfg in pipeline_steps:
            if isinstance(pipe_cfg, dict) and 'processor' in pipe_cfg:
                processor = pipe_cfg.pop('processor')
                ref_id = self.pipe_parser(
                    config=pipe_cfg,
                    context_path=context_path,
                    input_id=in_ref_id, 
                    processor=processor
                )
                in_ref_id = ref_id  # update the input reference for the next pipe
                pipes.append(ref_id)
        
        pipeline_node.src = pipes
        self.nodes.append(pipeline_node)
        return pipeline_node.ref_id
    
    def parse_pipeline(self, src: Dict[str, Any] = None, attr: List[str] = None, **kwargs) -> str:
        """
        Main entry point for parsing pipeline configurations.
        
        Args:
            src (dict): Pipeline configuration
            attr: Context path for this node
            **kwargs: Additional keyword arguments
            
        Returns:
            str: Reference ID of the created pipeline node
            
        Raises:
            ValueError: If pipeline configuration is invalid
        """
        if src is None:
            raise ValueError("Pipeline source configuration cannot be None")
        
        # Validate pipeline configuration against schema
        is_valid, error_msg = self.validate_pipeline_config(src)
        if not is_valid:
            raise ValueError(f"Invalid pipeline configuration: {error_msg}")
        
        # Check if this is a built-in pipeline reference
        is_builtin, pipeline_name = self.is_builtin_pipeline(src)
        
        if is_builtin:
            return self.parse_builtin_pipeline(pipeline_name, src, attr)
        else:
            return self.parse_custom_pipeline(src.copy(), attr)
    
    def add_builtin_pipeline(self, name: str, config: Dict[str, Any]) -> None:
        """
        Add a new built-in pipeline configuration.
        
        Args:
            name (str): Name of the pipeline
            config (dict): Pipeline configuration
        """
        if name not in self.pipeline_schema['builtin_pipelines']:
            self.pipeline_schema['builtin_pipelines'].append(name)
        
        # This would typically update a builtin_configs dict in get_builtin_pipeline
        # For now, we'll log the addition
        logging.info(f"Added built-in pipeline: {name}")
    
    def get_nodes(self) -> List:
        """
        Get all nodes created by this parser.
        
        Returns:
            List: All created nodes
        """
        return self.nodes
    
    def clear_nodes(self) -> None:
        """
        Clear all created nodes.
        """
        self.nodes.clear()
    
    @classmethod
    def parse_from_dict(cls, pipeline_dict: Dict[str, Any], node_factory, input_parser, pipe_parser):
        """
        Convenient entry point to parse a pipeline from a raw dictionary.
        
        Args:
            pipeline_dict (dict): Raw pipeline configuration dictionary
            node_factory: Factory for creating nodes
            input_parser: Function to parse input configurations  
            pipe_parser: Function to parse pipe configurations
            
        Returns:
            tuple: (reference_id: str, created_nodes: List)
            
        Example:
            pipeline_config = {
                'input': {'type': 'mesh_layer', 'layer': 'top'},
                'pipeline': [
                    {'processor': 'extract_layer'},
                    {'processor': 'validate_data'}
                ]
            }
            
            ref_id, nodes = PipelineParser.parse_from_dict(
                pipeline_config, NodeFactory, input_parser, pipe_parser)
        """
        parser = cls(node_factory, input_parser, pipe_parser)
        ref_id = parser.parse_pipeline(src=pipeline_dict)
        return ref_id, parser.get_nodes()
