from pathlib import Path
from dataclasses import dataclass, field
from typing import Any

# import abstract class ABC
from abc import ABC, abstractmethod

# import FileTypeFactory
from .filepath.filetype_factory import filetype_factory

# --- InputValueSpec Classes ---
@dataclass
class InputValueSpec(ABC):
    """Base class for YAML input specifications."""

    value: Any = None  # Value of the input

    
    @classmethod
    @abstractmethod
    def create(self, **kwargs):
        """Create an instance of this class."""
        pass

    @abstractmethod
    def open(self, build_context=None):
        """Open the value. This method should be implemented by subclasses."""
        pass


@dataclass
class ValueInput(InputValueSpec):
    """Represents a simple value input (string, boolean, integer, float)."""
    value: Any = None 
    
    @classmethod
    def create(cls, value):
        return cls(value=value)

    def open(self, build_context=None):
        """Open the value. This is a placeholder for future functionality."""
        # Placeholder for opening the value if needed
        return self.value


@dataclass
class FilepathInput(InputValueSpec):
    """Represents a filepath input (raster, csv, shapefile)."""

    opening_kwargs: dict = field(default_factory=dict)
    value: str = None
    requires_mesh: bool = field(default=False)
        
    def __post_init__(self):
        if self.value:
            self.filepath = Path(self.value)
            self.file_ext = self.filepath.suffix.lstrip('.').lower()
        else:
            raise ValueError("FilepathInput requires a valid filepath value.")
    
    @classmethod
    def create(cls, value, opening_kwargs, requires_mesh=False):
        return cls(
            value=value, 
            opening_kwargs=opening_kwargs or {}, 
            requires_mesh=requires_mesh
        )
    
    
    def open(self, build_context=None):
        """Open the file with optional build context for spatial files."""
        file_opener = filetype_factory.get_file_opener(self.filepath)
        
        if self.requires_mesh and build_context and build_context.has_mesh():
            # Pass mesh context to file opener
            return file_opener.get_data(
                self.filepath, 
                self.opening_kwargs, 
                mesh_context=build_context.get_mesh_context()
            )
        else:
            # Open without mesh context
            return file_opener.get_data(self.filepath, self.opening_kwargs)

