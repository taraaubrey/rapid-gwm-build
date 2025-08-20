"""Global registry for parsed nodes (pre-build DAG)."""

from typing import Dict, Optional, List, Any
import threading

class NodeRegistry:
    """Thread-safe global registry for declared/parsed nodes (not built)."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._nodes = {}
        return cls._instance

    def register_node(self, node_id: str, node_obj: Any):
        """Register a declared node."""
        with self._lock:
            if node_id in self._nodes:
                raise ValueError(f"Node ID '{node_id}' already registered.")
            self._nodes[node_id] = node_obj

    def get_node(self, node_id: str) -> Optional[Any]:
        """Get a parsed node object."""
        with self._lock:
            return self._nodes.get(node_id)


    def has_node(self, node_id: str) -> bool:
        """Check if node exists."""
        return node_id in self._nodes

    def list_nodes(self) -> List[str]:
        """List all registered node IDs."""
        with self._lock:
            return list(self._nodes.keys())

    def clear_node(self, node_id: str):
        """Remove a node."""
        with self._lock:
            self._nodes.pop(node_id, None)

    def clear_all(self):
        """Clear all nodes."""
        with self._lock:
            self._nodes.clear()

# Global singleton instance
node_registry = NodeRegistry()

# Convenience functions
def register_node(node_id: str, node_obj: Any):
    return node_registry.register_node(node_id, node_obj)

def get_node(node_id: str) -> Optional[Any]:
    return node_registry.get_node(node_id)

def has_node(node_id: str) -> bool:
    return node_registry.has_node(node_id)

def list_nodes() -> List[str]:
    return node_registry.list_nodes()


def clear_node(node_id: str):
    return node_registry.clear_node(node_id)

def clear_all_nodes():
    return node_registry.clear_all()
