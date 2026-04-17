"""Parsed node representation with type-specific metadata support."""

from dataclasses import dataclass, field
from typing import Set, Dict, Any, List

from ..build_registry import build_registry

# TODO: two required-field registries — required/defaults defined here AND in NodeSchemas
# (node_schemas.py) can drift out of sync. Consolidate into a single source of truth:
# keep node-runtime defaults here, move parse-time required/optional into NodeSchemas only.
NODE_TYPE_SCHEMAS = {
    'input': {
        'required': ['value'],
        'defaults': {
            'resolution_mode': 'auto',
            'load_options': {},
            'use_mesh_build_context': True
        }
    },
    'pipe': {
        'required': ['input', 'processor'],
        'defaults': {
            'processor_args': {},
        }
    },
    'pipeline': {
        'required': ['output'],
        'defaults': {}
    },
    'mesh_config': {
        'required': [],
        'defaults': {
            'mesh_type': 'structured',
        },
    },
    'mesh_data':{
        'required': [],
        'defaults': {},
    },
    'mesh': {
        'required': [],
        'defaults': {},
    }, 
    'module': {
        'required': ['cmd'],
        'defaults': {}
    },
}

# @dataclass
# class NodeMetadata:
#     """Parser metadata for all nodes."""
#     parsed_at: str = field(default_factory=lambda: datetime.now().isoformat())
#     parser_version: str = "2.0"

@dataclass
class NodeData:
    """Base parsed node with common fields and flexible metadata."""
    
    # Core fields (always present)
    node_type: str
    config: Dict[str, Any] = field(default_factory=dict) # raw configuration data
    context_path: List[str] = field(default_factory=list)
    dependencies: Set[str] = field(default_factory=set)
    
    # Parser metadata
    # parser_metadata: NodeMetadata = field(default_factory=NodeMetadata)
    
    # Node-specific metadata (flexible)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if len(self.context_path) == 0:
            raise ValueError("Context path cannot be empty")
        
        if isinstance(self.dependencies, list) and not isinstance(self.dependencies, set):
            self.dependencies = set(self.dependencies)

        # Apply type-specific metadata validation and defaults
        self._apply_type_schema()
    
    @property
    def id(self) -> str:
        """Unique identifier for the node based on context path."""
        return '.'.join(self.context_path)
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if not isinstance(other, NodeData):
            return False
        return (self.id == other.id)
    
    def _apply_type_schema(self):
        """Apply node type schema for metadata validation and defaults."""
        if self.node_type not in NODE_TYPE_SCHEMAS:
            raise ValueError(f"Can't build node data. Unknown node type: {self.node_type}")
        
        schema = NODE_TYPE_SCHEMAS[self.node_type]
        
        # Apply defaults — use `is None` so falsy-but-valid values (False, 0, []) are not overwritten
        for key, default_value in schema.get('defaults', {}).items():
            if self.get(key) is None:
                self.metadata.update({key: default_value})
        
        # Validate required fields
        for required_key in schema.get('required', []):
            if required_key not in self.metadata:
                raise ValueError(f"Node {self.id} of type '{self.node_type}' missing required metadata: {required_key}")
          
    
    # === Dict-like access for backward compatibility ===
    def get(self, key: str, default=None):
        """Dict-like access to node data."""
        # First check core fields
        if hasattr(self, key):
            return getattr(self, key)
        
        # Then check metadata
        if key in self.metadata:
            return self.metadata[key]
        
        # Finally return default
        return default
    
    def __getitem__(self, key: str):
        """Dict-like access that raises KeyError if not found."""
        value = self.get(key)
        if value is None and not self._has_key(key):
            raise KeyError(f"Key '{key}' not found in NodeData")
        return value
    
    def _has_key(self, key: str) -> bool:
        """Check if key exists anywhere in the node."""
        return (hasattr(self, key) or 
                key in self.metadata)
    
    
    # === Dependency resolution methods ===
    def get_dependency_data(self, key: str):
        """Get data from dependencies based on config key."""
        if key not in build_registry.list_built_nodes():
            raise ValueError(f"Dependency '{key}' not found for node {self.id}")
        
        build_result = build_registry.result_from_id(key)
        if build_result.data is None:
            raise ValueError(f"Data for dependency '{key}' is None in node {self.id}")
        
        return build_result.data
        

    # === Conversion methods ===
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict format for backward compatibility."""
        return {
            'id': self.id,
            'type': self.node_type,
            'config': self.config,
            'context_path': self.context_path,
            'dependencies': self.dependencies,
            'parser_metadata': {
                'parsed_at': self.parser_metadata.parsed_at,
                'parser_version': self.parser_metadata.parser_version,
            },
            **self.metadata  # Flatten metadata into main dict
        }
    