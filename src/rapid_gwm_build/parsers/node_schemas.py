"""
Node schema definitions for different node types.
Each schema defines the structure and validation rules for its node type.
"""

from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass


@dataclass
class NodeSchema:
    """Base schema for all node types."""
    node_type: str
    required_fields: List[str] = None
    optional_fields: List[str] = None  # Only keys allowed in this node
    value_types: List[Union[type, str]] = None  # Types that can be used in this node
    validation_rules: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.required_fields is None:
            self.required_fields = []
        if self.optional_fields is None:
            self.optional_fields = None
        if self.value_types is None:
            self.value_types = None
        if self.validation_rules is None:
            self.validation_rules = {}
    
    # create a copy of the schema with updated attributes
    def copy(self):
        """Create a copy of the schema with updated attributes."""
        return NodeSchema(
            node_type=self.node_type,
            required_fields=self.required_fields.copy(),
            optional_fields=self.optional_fields.copy() if self.optional_fields else None,
            value_types=self.value_types.copy() if self.value_types else None,
            validation_rules=self.validation_rules.copy()
        )
    
    
    def update(self, **kwargs):
        updated_schema = self.copy()
        
        """Update schema with new attributes."""
        for key, value in kwargs.items():
            if hasattr(updated_schema, key):
                setattr(updated_schema, key, value)
            else:
                raise ValueError(f"Invalid attribute '{key}' for NodeSchema")
        return updated_schema


class NodeSchemas:
    """Registry of all node schemas."""
    
    # Input Node Schema
    INPUT_SCHEMA = NodeSchema(
        node_type='input',
        required_fields=[],
        validation_rules={
            'input': [str, list, int, float, bool],
            'metadata': dict,
            'pipeline': list,  # List of pipe configurations
            'nested_validation': {
                'input': {
                    'nest_type': 'str',
                    'schema': 'value'
                },
                'pipeline': {
                    'nest_type': 'list',
                    'schema': 'pipe'
                }
            },
            # 'excluded_fields': ['pipeline', 'builtin'], # validation handled by pipeline logic
            'only_keys': ['input', 'metadata', 'pipeline', 'builtin'] #special rule
        }
    )

    VALUE_SCHEMA = NodeSchema(
        node_type='value',
        required_fields=['src'],
        # validation_rules={
        #     'src': [str, list, int, float, bool],
        #     'dict_required_keys': ['src'] #special rule
        # }
    )
    
    # Pipe Node Schema
    PIPE_SCHEMA = NodeSchema(
        node_type='pipe',
        required_fields=['processor'],
        validation_rules={
            'processor': str,
        }
    )
    
    # Pipeline Node Schema
    PIPELINE_SCHEMA = NodeSchema(
        node_type='pipeline',
        required_fields=['input'],
        value_types=[dict],
        validation_rules={
            'pipeline': list,  # List of pipe configurations
            'either_or': [
                ['pipeline'],
                ['builtin']
            ],
            'builtin': ['only_top', 'extract_layer', 'mesh_processor'],
            'nested_validation': {
                'input': {
                    'nest_type': 'key',
                    'schema': 'value'
                },
                'pipeline': {
                    'nest_type': 'list',
                    'schema': 'pipe'
                }
            }
        }
    )

    MODULE_SCHEMA = NodeSchema(
        node_type='module',
        required_fields=[],
        optional_fields=['data', 'cmd', 'template'],
        validation_rules={
            'data': dict,
            'cmd': dict,
            'nested_validation': {
                'data': {
                    'nest_type': 'dict',
                    'schema': 'input'
                },
            },
        }
    )

    MODULE_DATA_SCHEMA = NodeSchema(
        node_type='module_data',
        validation_rules={
            'nested_validation': {
                '_': {
                    'nest_type': 'dict',
                    'schema': 'input'
                },
            },
        },
    )

    TEMPLATE_BUILD_DEPENDENCIES = NodeSchema(
        node_type='template_build_dependencies',
        validation_rules={
            'nested_validation': {
                '_': {
                    'nest_type': 'dict',
                    'schema': 'input'
                },
            },
        },
    )
    
    # Mesh Node Schema
    MESH_CONFIG_SCHEMA = NodeSchema(
        node_type='mesh_config',
        required_fields=['nlay', 'resolution'],
        validation_rules={
            'nlay': int,
            'resolution': [int, float],
            'crs': [int, str],  # EPSG code or proj string
        }
    )

    # New Mesh Data Schema
    MESH_DATA_SCHEMA = NodeSchema(
        node_type='mesh_data',
        required_fields=['top', 'bottoms'],
        # dependencies=['top', 'bottoms', 'active_domain'],
        validation_rules={
            'top': [dict, str],      # Can be input/pipeline config or reference
            'bottoms': [dict, str],  # Can be input/pipeline config or reference
            'active_domain': [dict, str]  # Optional, can be input/pipeline config or reference
        }
    )

    # Updated Mesh Schema (composite)
    MESH_SCHEMA = NodeSchema(
        node_type='mesh',
        required_fields=[],  # Composite node
        validation_rules={
            'either_or': [
                ['active_domain'],  # Has active_domain
                ['xorigin', 'yorigin']  # OR has both origin coordinates
            ],
            'nested_validation': {
                '_': {
                    'nest_type': 'dict',
                    'schema': 'input'
                },
            },
        }
    )

    
    
    @classmethod
    def get_schema(cls, node_type: str) -> Optional[NodeSchema]:
        """Get schema for a specific node type."""
        schema_map = {
            'input': cls.INPUT_SCHEMA,
            'value': cls.VALUE_SCHEMA,
            'pipe': cls.PIPE_SCHEMA,
            'pipeline': cls.PIPELINE_SCHEMA,
            'mesh': cls.MESH_SCHEMA,
            'mesh_config': cls.MESH_CONFIG_SCHEMA,
            'mesh_data': cls.MESH_DATA_SCHEMA,
            'module': cls.MODULE_SCHEMA,
            'module_data': cls.MODULE_DATA_SCHEMA,
            'template_build_dependencies': cls.TEMPLATE_BUILD_DEPENDENCIES,
            # 'template': cls.TEMPLATE_SCHEMA
        }
        return schema_map.get(node_type)
    
    @classmethod
    def validate_config_strict(cls, node_type: str, config: Any, context: str = None, **kwargs) -> None:

        """Validate configuration and raise ValueError if invalid."""
        is_valid, error_msg = cls.validate_config(node_type, config, **kwargs)
        if not is_valid:
            context_str = f" for {context}" if context else ""
            # logging.error(f"{node_type.title()} validation failed{context_str}: {error_msg}")
            raise ValueError(f"Invalid {node_type} configuration {context_str}: {error_msg}")
    
    @classmethod
    def validate_config(cls, node_type: str, config: Dict[str, Any], **kwargs) -> tuple[bool, str]:
        """Validate a configuration against its schema."""
        base_schema = cls.get_schema(node_type)
        
        # Create a temporary schema with overrides
        schema = cls._create_schema_with_overrides(base_schema, **kwargs)
    
        
        if not schema:
            return False, f"Unknown node type: {node_type}"
    

        # if 'excluded_fields' in validation_rules:
        #     excluded_fields = validation_rules['excluded_fields']
        #     for excluded_field in excluded_fields:
        #         if isinstance(config, dict) and excluded_field in config:
        #             return False, f"Field '{excluded_field}' is not allowed in {node_type} nodes"
    
        
        # Check required fields
        for field in schema.required_fields:
            if isinstance(config, dict) and field not in config:
                return False, f"Missing required field '{field}' for {node_type} node"
            
        # Check value types
        if schema.value_types and type(config) not in schema.value_types:
            return False, f"Invalid value type for {node_type} node. Expected one of: {schema.value_types}, got {type(config)}"
        
        if schema.optional_fields and isinstance(config, dict):
            for key in config.keys():
                if key not in schema.optional_fields:
                    return False, f"Unexpected key '{key}' in {node_type} node. Allowed keys: {schema.optional_fields}"

        # Check for excluded fields first (before other validation)
        validation_rules = schema.validation_rules
        
        if isinstance(config, dict) and validation_rules.get('only_keys', False):
            # Check if config contains only allowed keys
            allowed_keys = validation_rules['only_keys']
            for key in config.keys():
                if key not in allowed_keys:
                    return False, f"Dictionary values for {node_type} can only contain keys: {allowed_keys}, got '{key}'"
        
        # Special validation
        if isinstance(config, dict) and validation_rules.get('dict_required_keys', False):
            for key in validation_rules['dict_required_keys']:
                if key not in config:
                    return False, f"Dictionary values must contain a '{key}' key"
        
        if isinstance(config, dict) and validation_rules.get('only_keys', False):
            for key in config:
                if key not in validation_rules.get('only_keys'):
                    return False, f"Invalid '{key}' key for {node_type} node. Allowed keys: {validation_rules.get('only_keys')}. If you are trying to set opening kwargs, use: \ninput:\n    src: <file.tif> \n     **kwargs"

        # Handle either_or validation
        if isinstance(config, dict) and 'either_or' in validation_rules:
            either_or_rules = validation_rules['either_or']
            valid_combination = False
            
            for rule in either_or_rules:
                if isinstance(rule, list):
                    # Check if all fields in this combination are present
                    if all(field in config for field in rule):
                        valid_combination = True
                        break
                else:
                    # Single field check
                    if isinstance(config, dict) and rule in config:
                        valid_combination = True
                        break
            
            if not valid_combination:
                return False, f"Invalid field combination for {node_type}. Must have one of: {either_or_rules}"
        
        # Validate nested schemas
        if isinstance(config, dict) and 'nested_validation' in validation_rules:
            nested_rules = validation_rules.get('nested_validation', {})

            for field_name, nest_meta in nested_rules.items():
                nest_type = nest_meta.get('nest_type')
                nest_schema = nest_meta.get('schema')

            
                if field_name == '_':
                    assert nest_type == 'dict', f"Invalid nest_type for '_' field in {node_type}: {nest_type} must be 'dict'"
                else: 
                    field_value = config.get(field_name, [])

                if nest_type == 'key':
                    # Validate the nested field against its schema
                    is_valid, error_msg = cls.validate_config(nest_schema, field_value)
                    if not is_valid:
                        return False, f"Invalid '{field_name}' in {node_type}: {error_msg}"
                
                elif nest_type == 'list':
                    
                    # Validate each item in the list against its schema
                    for item in field_value:
                        is_valid, error_msg = cls.validate_config(nest_schema, item)
                        if not is_valid:
                            return False, f"Invalid item in '{field_name}' list in {node_type}: {error_msg}"
                
                elif nest_type == 'str':
                    is_valid, error_msg = cls.validate_config(nest_schema, field_value)
                    if not is_valid:
                        return False, f"Invalid item in '{field_name}' list in {node_type}: {error_msg}"
                
                elif nest_type == 'dict':
                    if field_name == '_':
                        field_config = config.copy()
                    else:
                        field_config = config.get(field_name, {})
                    for field_value in field_config.values():
                        is_valid, error_msg = cls.validate_config(nest_schema, field_value)
                        if not is_valid:
                            return False, f"Invalid '{field_name}' in {node_type}: {error_msg}"
                
        
        # Validate builtin pipelines #TODO
        if node_type == 'pipeline' and 'builtin' in config:
            builtin_name = config['builtin']
            valid_builtins = validation_rules.get('builtin', [])
            if builtin_name not in valid_builtins:
                return False, f"Unknown builtin pipeline: {builtin_name}. Valid options: {valid_builtins}"
        
        return True, ""
    
    @classmethod
    def _create_schema_with_overrides(cls, base_schema: NodeSchema, **kwargs) -> NodeSchema:
        """Create a temporary schema with overridden attributes."""
        # from dataclasses import fields

        return base_schema.update(**kwargs)

        # # Get valid NodeSchema attributes
        # valid_attrs = {field.name for field in fields(NodeSchema) if field.name != 'node_type'}
        
        # # Filter kwargs to only include valid NodeSchema attributes
        # overrides = {k: v for k, v in kwargs.items() if k in valid_attrs}
        
        # # Create new schema with overrides
        # return NodeSchema(
        #     node_type=base_schema.node_type,
        #     required_fields=overrides.get('required_fields', base_schema.required_fields),
        #     value_types=overrides.get('value_types', base_schema.value_types),
        #     validation_rules=overrides.get('validation_rules', base_schema.validation_rules)
        # )