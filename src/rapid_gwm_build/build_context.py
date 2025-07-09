from typing import Any, Dict, Optional

class BuildContext:
    """Context for managin build-time dependencies and state."""

    def __init__(self):
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
    
    def register_component(self, component_id: str, component: Any):
        """Register any built component."""
        self.built_components[component_id] = component
    
    def get_component(self, component_id: str) -> Optional[Any]:
        """Get a previously built component."""
        return self.built_components.get(component_id)