"""Global registry for built nodes and results."""

from typing import Dict, Any, Optional, List
from copy import deepcopy
import threading

class BuildRegistry:
    """Thread-safe global registry for built nodes."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._built_nodes = {}
                    cls._instance._build_history = []
        return cls._instance
    
    def register_built_node(self, node_id: str, result: Any, metadata: Dict = None):
        """Register a built node with optional metadata."""
        with self._lock:
            self._built_nodes[node_id] = {
                'result': result,
                'metadata': metadata or {},
                'timestamp': self._get_timestamp()
            }
            self._build_history.append({
                'node_id': node_id,
                'timestamp': self._get_timestamp(),
                'success': getattr(result, 'success', True)
            })
    
    def result_from_id(self, node_id: str) -> Optional[Any]:
        """Get a built node by ID."""
        with self._lock:
            node_data = self._built_nodes.get(node_id)
            return node_data['result'] if node_data else None
    
    def has_id(self, node_id: str) -> bool:
        """Check if node exists in registry."""
        return node_id in self._built_nodes
    
    def list_built_nodes(self) -> List[str]:
        """List all built node IDs."""
        with self._lock:
            return list(self._built_nodes.keys())
    
    def clear_node(self, node_id: str):
        """Remove a specific node from registry."""
        with self._lock:
            self._built_nodes.pop(node_id, None)
    
    def clear_all(self):
        """Clear all built nodes."""
        with self._lock:
            self._built_nodes.clear()
            self._build_history.clear()
    
    def get_build_history(self) -> List[Dict]:
        """Get build history."""
        with self._lock:
            return deepcopy(self._build_history)
    
    def _get_timestamp(self):
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()

# Global instance
build_registry = BuildRegistry()

# Convenience functions
def register_built_node(node_id: str, result: Any, metadata: Dict = None):
    """Register a built node globally."""
    return build_registry.register_built_node(node_id, result, metadata)

def result_from_id(node_id: str):
    """Get a built node globally."""
    return build_registry.result_from_id(node_id)

def has_built_node(node_id: str) -> bool:
    """Check if node is built globally."""
    return build_registry.has_id(node_id)

def list_built_nodes() -> List[str]:
    """List all built nodes globally."""
    return build_registry.list_built_nodes()