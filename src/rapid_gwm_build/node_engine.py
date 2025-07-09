from typing import Any


class NodeBuildEngine:
    def __init__(self, registry: dict[str, Any]):
        self.registry = registry
    
    def get_builder(self, node_type):

        if node_type not in self.registry:
            raise ValueError(f"No builder registered for node type '{node_type}'")

        return self.registry[node_type]

