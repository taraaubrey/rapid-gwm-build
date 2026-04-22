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
        # value_types=[str, int, bool, dict],
        required_fields=[],
        validation_rules={
            'either_or': [
                ['input'],                    # Just input key
                ['pipeline', 'input'],        # Pipeline + input
                ['builtin', 'input'],         # Builtin + input
                ['levels', 'input'],          # Levels + input
                ['metadata', 'input']         # Metadata + input
            ],
            'nested_validation': {
                # TODO: nested input-dict validation — when `input` value is a dict,
                # validate that it contains `src` key. Without this, {'input': {'data': 25}}
                # (missing src) silently passes and produces wrong results.
                # 'input': {
                #     'nest_type': 'str',
                #     'schema': 'value'
                # },
                'pipeline': {
                    'nest_type': 'list',
                    'schema': 'pipe'
                },
                'levels': {
                    'nest_type': 'key',
                    'schema': 'levels'
                }
            },
            # 'excluded_fields': ['pipeline', 'builtin'], # validation handled by pipeline logic
            'only_keys': ['input', 'metadata', 'pipeline', 'builtin', 'levels'] #special rule
        }
    )

    LEVELS_SCHEMA = NodeSchema(
        node_type='levels',
        required_fields=['input'],
        value_types=[dict],
        validation_rules={
            'input': list,
            'nested_validation': {
                'pipeline': {
                    'nest_type': 'list',
                    'schema': 'pipe'
                },
            }
        }
    )

    # VALUE_SCHEMA = NodeSchema(
    #     node_type='value',
    #     required_fields=['src'],
    #     # validation_rules={
    #     #     'src': [str, list, int, float, bool],
    #     #     'dict_required_keys': ['src'] #special rule
    #     # }
    # )
    
    # Pipe Node Schema
    PIPE_SCHEMA = NodeSchema(
        node_type='pipe',
        value_types=[dict],
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
                # 'input': {
                #     'nest_type': 'key',
                #     'schema': 'value'
                # },
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
    
    # # Mesh Node Schema
    # MESH_CONFIG_SCHEMA = NodeSchema(
    #     node_type='mesh_config',
    #     required_fields=['nlay', 'resolution'],
    #     validation_rules={
    #         'nlay': int,
    #         'resolution': [int, float],
    #         'crs': [int, str],  # EPSG code or proj string
    #     }
    # )

    # # New Mesh Data Schema
    # MESH_DATA_SCHEMA = NodeSchema(
    #     node_type='mesh_data',
    #     required_fields=['top', 'bottoms'],
    #     # dependencies=['top', 'bottoms', 'active_domain'],
    #     validation_rules={
    #         'top': [dict, str],      # Can be input/pipeline config or reference
    #         'bottoms': [dict, str],  # Can be input/pipeline config or reference
    #         'active_domain': [dict, str]  # Optional, can be input/pipeline config or reference
    #     }
    # )

    # --- Mesh schemas ----------------------------------------------------
    # MESH_SCHEMA is a thin dispatcher: it requires `mesh_type` and delegates
    # full validation to the per-type schema in MESH_TYPE_SCHEMAS below.
    # Adding a new mesh type = define its schema and register it in the map.

    STRUCTURED_MESH_SCHEMA = NodeSchema(
        node_type='mesh',
        required_fields=['mesh_type', 'nlay', 'top', 'bottoms'],
        validation_rules={
            # Exactly-one-of, two independent groups (extent source + spacing source).
            'either_or': {
                'extent_source': [
                    ['extent'],              # vector/raster file → gridit derives shape
                    ['nrow', 'ncol'],        # explicit shape
                    ['x_length', 'y_length'],# length-based; shape derived from spacing
                ],
                'spacing_source': [
                    ['resolution'],          # uniform, both axes
                    ['dx', 'dy'],            # uniform, per-axis
                    ['delr', 'delc'],        # per-cell arrays (requires explicit nrow/ncol)
                ],
            },
            # Pairs that cannot co-exist (cross-rule guards).
            'mutually_exclusive': [
                # delr/delc only valid with explicit nrow+ncol
                ['delr', 'extent'], ['delr', 'x_length'], ['delr', 'y_length'],
                ['delc', 'extent'], ['delc', 'x_length'], ['delc', 'y_length'],
                # extent implies shape derivation — cannot combine with explicit shape/length
                ['extent', 'nrow'], ['extent', 'ncol'],
                ['extent', 'x_length'], ['extent', 'y_length'],
            ],
            # Friendly error for legacy field names (pre-rename).
            'renamed_fields': {
                'active_domain': 'domain',
                'kind': 'mesh_type',
            },
            'field_types': {
                'mesh_type': (str,),
                'nlay': (int,),
                'resolution': (int, float),
                'crs': (int, str),
                'nrow': (int,),
                'ncol': (int,),
                'xorigin': (int, float),
                'yorigin': (int, float),
                'angrot': (int, float),
                'x_length': (int, float),
                'y_length': (int, float),
                'dx': (int, float),
                'dy': (int, float),
                # TODO: range validation — add a `field_constraints` rule (e.g. nlay > 0,
                # resolution > 0) so invalid values like nlay: -1 are rejected at parse time.
            },
            'nested_validation': {
                '_': {
                    'nest_type': 'dict',
                    'schema': 'input'
                },
            },
        }
    )

    # Placeholders for future mesh types — register them in MESH_TYPE_SCHEMAS
    # once their validation requirements are defined.
    # UNSTRUCTURED_MESH_SCHEMA = NodeSchema(...)
    # ELEMENT_MESH_SCHEMA = NodeSchema(...)
    # AREA_MESH_SCHEMA = NodeSchema(...)

    MESH_TYPE_SCHEMAS = {
        'structured': STRUCTURED_MESH_SCHEMA,
        # 'unstructured': UNSTRUCTURED_MESH_SCHEMA,
        # 'elements': ELEMENT_MESH_SCHEMA,
        # 'areas': AREA_MESH_SCHEMA,
    }

    # Thin dispatcher: requires `mesh_type`, then delegates to the concrete
    # per-type schema. Keep required_fields minimal here so the per-type schema
    # owns the full set of rules.
    MESH_SCHEMA = NodeSchema(
        node_type='mesh',
        required_fields=['mesh_type'],
        validation_rules={
            'renamed_fields': {
                'active_domain': 'domain',
                'kind': 'mesh_type',
            },
            'dispatch_on': {
                'field': 'mesh_type',
                'map': MESH_TYPE_SCHEMAS,
            },
        }
    )


    
    @classmethod
    def get_schema(cls, node_type: str) -> Optional[NodeSchema]:
        """Get schema for a specific node type."""
        schema_map = {
            'input': cls.INPUT_SCHEMA,
            # 'value': cls.VALUE_SCHEMA,
            'pipe': cls.PIPE_SCHEMA,
            'pipeline': cls.PIPELINE_SCHEMA,
            'mesh': cls.MESH_SCHEMA,
            # 'mesh_config': cls.MESH_CONFIG_SCHEMA,
            # 'mesh_data': cls.MESH_DATA_SCHEMA,
            'module': cls.MODULE_SCHEMA,
            'module_data': cls.MODULE_DATA_SCHEMA,
            'template_build_dependencies': cls.TEMPLATE_BUILD_DEPENDENCIES,
            'levels': cls.LEVELS_SCHEMA,
            # 'template': cls.TEMPLATE_SCHEMA
        }
        return schema_map.get(node_type)
    
    @classmethod
    def validate_config_strict(cls, node_type: str, config: Any, context: str = None, **kwargs) -> None:

        """Validate configuration and raise ValueError if invalid."""
        is_valid, error_msg = cls.validate_config(node_type, config, **kwargs)
        if not is_valid:
            # Normalise context to dot-notation regardless of whether a list or string was passed
            if isinstance(context, (list, tuple)):
                context_str = f"at '{'.'.join(str(p) for p in context)}'"
            elif context:
                context_str = f"at '{context}'"
            else:
                context_str = ""
            raise ValueError(f"Invalid {node_type} configuration {context_str}:\n{error_msg}")
    
    @classmethod
    def validate_config(cls, node_type: str, config: Dict[str, Any], **kwargs) -> tuple[bool, str]:
        """Validate a configuration against its schema."""
        base_schema = cls.get_schema(node_type)

        if not base_schema:
            return False, f"Unknown node type: {node_type}"

        # Create a temporary schema with overrides
        schema = cls._create_schema_with_overrides(base_schema, **kwargs)

        return cls._validate_against_schema(schema, config, node_type)

    @classmethod
    def _validate_against_schema(
        cls, schema: NodeSchema, config: Any, node_type: str
    ) -> tuple[bool, str]:
        """Core rule engine. Applies schema rules to config.

        Split out from `validate_config` so the `dispatch_on` rule can recurse
        into a sub-schema without re-entering the node-type lookup path.
        """
        # Friendly error for renamed fields — run before required-field checks
        # so the user gets "rename X to Y" instead of "missing Y".
        if isinstance(config, dict):
            renamed = schema.validation_rules.get('renamed_fields') or {}
            for old_name, new_name in renamed.items():
                if old_name in config:
                    return False, (
                        f"Field '{old_name}' has been renamed to '{new_name}' "
                        f"in {node_type} configuration. Update your YAML."
                    )

        # Check required fields
        for field in schema.required_fields:
            if isinstance(config, dict) and field not in config:
                return False, f"Missing required field '{field}' for {node_type} node"

        # Check value types
        if schema.value_types and type(config) not in schema.value_types:
            return False, f"\nError input config:\n\n{config}\n\nInvalid value type for {node_type} node. Expected one of: {schema.value_types}, got {type(config)}"

        if schema.optional_fields and isinstance(config, dict):
            for key in config.keys():
                if key not in schema.optional_fields:
                    return False, f"\nError input config:\n\n{config}\n\nUnexpected key '{key}' in {node_type} node. Allowed keys: {schema.optional_fields}"

        validation_rules = schema.validation_rules

        if isinstance(config, dict) and validation_rules.get('only_keys', False):
            # Check if config contains only allowed keys
            allowed_keys = validation_rules['only_keys']
            for key in config.keys():
                if key not in allowed_keys:
                    return False, f"\nError input config:\n\n{config}\n\nDictionary values for {node_type} can only contain keys: {allowed_keys}, got '{key}'"

        # Check scalar field types (field_types rule)
        if isinstance(config, dict) and validation_rules.get('field_types'):
            for field_name, expected_types in validation_rules['field_types'].items():
                if field_name in config:
                    val = config[field_name]
                    if not isinstance(val, expected_types):
                        type_names = ', '.join(t.__name__ for t in expected_types)
                        return False, (
                            f"Field '{field_name}' must be of type ({type_names}), "
                            f"got {type(val).__name__} ({val!r})"
                        )

        # Special validation
        if isinstance(config, dict) and validation_rules.get('dict_required_keys', False):
            for key in validation_rules['dict_required_keys']:
                if key not in config:
                    return False, f"\nError input config:\n\n{config}\n\nDictionary values must contain a '{key}' key"

        if isinstance(config, dict) and validation_rules.get('only_keys', False):
            for key in config:
                if key not in validation_rules.get('only_keys'):
                    return False, f"\nError input config:\n\n{config}\n\nInvalid '{key}' key for {node_type} node. Allowed keys: {validation_rules.get('only_keys')}. If you are trying to set opening kwargs, use: \ninput:\n    src: <file.tif> \n     **kwargs"

        # Mutually exclusive pairs — fields that cannot co-exist.
        if isinstance(config, dict) and 'mutually_exclusive' in validation_rules:
            for pair in validation_rules['mutually_exclusive']:
                present = [f for f in pair if f in config]
                if len(present) > 1:
                    return False, (
                        f"Mutually exclusive fields in {node_type}: {present} "
                        f"cannot be specified together."
                    )

        # Handle either_or validation. Supports two forms:
        #   - list: legacy form, at-least-one match across all rules.
        #   - dict: named groups, each group must have exactly-one match.
        if isinstance(config, dict) and 'either_or' in validation_rules:
            either_or_rules = validation_rules['either_or']

            if isinstance(either_or_rules, dict):
                for group_name, group_rules in either_or_rules.items():
                    matches = []
                    for rule in group_rules:
                        if isinstance(rule, list):
                            if all(f in config for f in rule):
                                matches.append(rule)
                        elif rule in config:
                            matches.append([rule])
                    if len(matches) == 0:
                        return False, (
                            f"\nError input config:\n\n{config}\n\n"
                            f"Missing required field combination for group "
                            f"'{group_name}' in {node_type}. Must have exactly one of: {group_rules}"
                        )
                    if len(matches) > 1:
                        return False, (
                            f"\nError input config:\n\n{config}\n\n"
                            f"Conflicting field combinations for group "
                            f"'{group_name}' in {node_type}. Only one of {group_rules} "
                            f"is allowed, got multiple: {matches}"
                        )
            else:
                valid_combination = False
                for rule in either_or_rules:
                    if isinstance(rule, list):
                        if all(field in config for field in rule):
                            valid_combination = True
                            break
                    else:
                        if rule in config:
                            valid_combination = True
                            break

                if not valid_combination:
                    return False, f"\nError input config:\n\n{config}\n\nInvalid field combination for {node_type}. Must have one of: {either_or_rules}"

        # Dispatcher — delegate full validation to a per-type sub-schema.
        # Runs after basic shape checks so required discriminator & renames
        # produce friendly errors before dispatch.
        if isinstance(config, dict) and 'dispatch_on' in validation_rules:
            disp = validation_rules['dispatch_on']
            field_name = disp['field']
            schema_map = disp['map']
            value = config.get(field_name)
            if value not in schema_map:
                return False, (
                    f"Unknown {field_name} '{value}' for {node_type}. "
                    f"Valid values: {list(schema_map.keys())}"
                )
            sub_schema = schema_map[value]
            return cls._validate_against_schema(sub_schema, config, node_type)

        # Validate nested schemas
        if isinstance(config, dict) and 'nested_validation' in validation_rules:
            nested_rules = validation_rules.get('nested_validation', {})

            for field_name, nest_meta in nested_rules.items():
                nest_type = nest_meta.get('nest_type')
                nest_schema = nest_meta.get('schema')


                if field_name == '_':
                    assert nest_type == 'dict', f"{node_type}: {nest_type} must be 'dict'"
                else:
                    field_value = config.get(field_name)

                if nest_type == 'key':
                    # Validate the nested field against its schema
                    if field_value:
                        is_valid, error_msg = cls.validate_config(nest_schema, field_value)
                        if not is_valid:
                            return False, f"\nError input config:\n\n{config}\n\nInvalid '{field_name}' in {node_type}: {error_msg}"

                elif nest_type == 'list':
                    if field_value:
                        # Validate each item in the list against its schema
                        for item in field_value:
                            is_valid, error_msg = cls.validate_config(nest_schema, item)
                            if not is_valid:
                                return False, f"\nError input config:\n\n{config}\n\nInvalid item in '{field_name}' list in {node_type}: {error_msg}"

                elif nest_type == 'str':
                    is_valid, error_msg = cls.validate_config(nest_schema, field_value)
                    if not is_valid:
                        return False, f"\nError input config:\n\n{config}\n\nInvalid item in '{field_name}' list in {node_type}: {error_msg}"

                elif nest_type == 'dict':
                    if field_name == '_':
                        field_config = config.copy()
                    else:
                        field_config = config.get(field_name, {})
                    for field_value in field_config.values():
                        is_valid, error_msg = cls.validate_config(nest_schema, field_value)
                        if not is_valid:
                            return False, f"\nError input config:\n\n{config}\n\nInvalid '{field_name}' in {node_type}: {error_msg}"


        if node_type == 'pipeline' and isinstance(config, dict) and 'builtin' in config:
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