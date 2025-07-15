from abc import ABC, abstractmethod
from typing import Dict, Any
from ...result import BuildResult
from ..node_data import NodeData

class BaseNodeBuilder(ABC):
    """Base class for all node builders with mesh context support."""
    
    @abstractmethod
    def build(self, node_data: NodeData, 
              dependencies: Dict[str, Any] = None,
              build_context = None) -> BuildResult:
        """Build the node with access to dependencies and build context."""
        pass

    @staticmethod
    def _validate_result(result):
        if result is not None:
            return True
        else:
            raise ValueError("Build result cannot be None or empty.")