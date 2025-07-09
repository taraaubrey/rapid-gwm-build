"""Processors package for data processing operations."""

from .base import BaseProcessor
from .processor_registry import BUILTIN_PROCESSORS, create_processor

# Import all processor categories
from . import io

__all__ = [
    "BaseProcessor",
    "BUILTIN_PROCESSORS", 
    "create_processor",
    "io",
]