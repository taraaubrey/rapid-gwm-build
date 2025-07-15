"""Centralized registry management for all application components."""

from typing import Dict, Any, List

# =============================================================================
# Registry Storage
# =============================================================================

BUILDER_REGISTRY: Dict[str, Any] = {}
BUILTIN_PROCESSORS: Dict[str, Any] = {}

# =============================================================================
# Decorator Functions
# =============================================================================

def register_builder(node_type: str):
    """Register a builder for a specific node type."""
    def decorator(builder):
        BUILDER_REGISTRY[node_type] = builder
        return builder
    return decorator

def register_processor(processor_name: str, dependency_args: Dict[str, str]={}, context_required: bool=False):
    """Register a processor with a given name."""
    def decorator(processor):
        BUILTIN_PROCESSORS[processor_name] = {
            'func': processor,
            'dependency_args': dependency_args,
            'context_required': context_required,
        }
        return processor
    return decorator

# =============================================================================
# Registry Access Functions
# =============================================================================

def get_builder(node_type: str):
    """Get a registered builder by node type."""
    if node_type not in BUILDER_REGISTRY:
        raise KeyError(f"No builder registered for node type: {node_type}")
    return BUILDER_REGISTRY[node_type]

def get_processor(processor_name: str):
    """Get a registered processor by name."""
    if processor_name not in BUILTIN_PROCESSORS:
        raise KeyError(f"No processor registered with name: {processor_name}")
    return BUILTIN_PROCESSORS[processor_name]


# =============================================================================
# Registry Management
# =============================================================================

def list_builders() -> List[str]:
    """List all registered builder node types."""
    return list(BUILDER_REGISTRY.keys())

def list_processors() -> List[str]:
    """List all registered processor names."""
    return list(BUILTIN_PROCESSORS.keys())

def get_all_registries() -> Dict[str, Dict[str, Any]]:
    """Get all registries for debugging/inspection."""
    return {
        "builders": BUILDER_REGISTRY.copy(),
        "processors": BUILTIN_PROCESSORS.copy(),
    }
