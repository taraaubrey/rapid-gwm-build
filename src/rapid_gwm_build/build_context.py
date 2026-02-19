from typing import Any, Optional
import threading

class BuildContext:
    """Singleton build context for managing mesh and global build state."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        # Only initialize once
        if not getattr(self, '_initialized', False):
            self._mesh_registry = {}
            self._global_state = {}
            self._initialized = True

        self.built_components = {}
        self.mesh_grid = None
        self.mesh_id = None

    def register_mesh(self, mesh_id:str, mesh_grid: Any):
        """Register a built mesh for use by other components."""
        self.mesh_grid = mesh_grid
        self.mesh_id = mesh_id
        self.built_components[mesh_id] = mesh_grid

    def has_mesh(self) -> bool:
        """Check if mesh context is available."""
        return self.mesh_grid is not None
    
    def get_mesh_context(self) -> Optional[Any]:
        """Get the current mesh context for spatial file operations."""
        return self.mesh_grid
    
    def set_global_state(self, key: str, value: Any):
        """Set global state value."""
        with self._lock:
            self._global_state[key] = value
    
    def get_global_state(self, key: str, default: Any = None) -> Any:
        """Get global state value."""
        return self._global_state.get(key, default)
    
    def clear_context(self):
        """Clear all context data."""
        with self._lock:
            self._mesh_registry.clear()
            self._global_state.clear()

# Global singleton instance
build_context = BuildContext()