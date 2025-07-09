"""Base processor class."""

from abc import ABC, abstractmethod
from typing import Any

class BaseProcessor(ABC):
    """Base class for all processors."""
    
    @abstractmethod
    def process(self, *args, **kwargs) -> Any:
        """Process data. Must be implemented by subclasses."""
        pass
    
    def __call__(self, *args, **kwargs) -> Any:
        """Make processor callable."""
        return self.process(*args, **kwargs)
    
    def __repr__(self) -> str:
        """String representation of processor."""
        return f"{self.__class__.__name__}()"