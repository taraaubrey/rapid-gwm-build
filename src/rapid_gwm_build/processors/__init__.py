"""Processors package for data processing operations."""
# Import base class first
# Import subpackages explicitly
from . import io, mf6, data, mesh

# Import main classes for convenience
from .processor_engine import ProcessorEngine

# Export what users should access
__all__ = [
    "ProcessorEngine", 
    "io",
    "mf6",
    "data",
    "mesh"
]