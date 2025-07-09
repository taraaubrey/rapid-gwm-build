from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from ..result import BuildResult

class BaseNodeBuilder(ABC):
    """Base class for all node builders with mesh context support."""
    
    @abstractmethod
    def build(self, parsed_node: Dict[str, Any], 
              dependencies: Dict[str, Any] = None,
              build_context = None) -> BuildResult:
        """Build the node with access to dependencies and build context."""
        pass