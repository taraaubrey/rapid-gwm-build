from .input_specs import (
    InputValueSpec,
    ValueInput,
    FilepathInput,
)
from .file_extensions import VECTOR_EXTENSIONS, RASTER_EXTENSIONS

class InputClassifier:
    """Classifies raw input values into appropriate input types."""
    def __init__(self):
        # Common file extensions
        self.file_extensions = VECTOR_EXTENSIONS | RASTER_EXTENSIONS
        # Spatial file extensions that require mesh context
        self.spatial_extensions = VECTOR_EXTENSIONS | RASTER_EXTENSIONS

    
    def classify(self, value, opening_kwargs=None, value_type='deferred') -> InputValueSpec:
        """Classify a raw value into an appropriate input type."""

        if value_type == 'deferred' and self._is_filelike_string(value):
            # Determine if this file requires mesh context
            requires_mesh = self._requires_mesh_context(value)

            # Check if it's a file-like string first
            return FilepathInput.create(
                value, 
                opening_kwargs, 
                requires_mesh=requires_mesh
            )
        else:
            # Fallback to value input
            return ValueInput.create(value)
    
    
    def _requires_mesh_context(self, value: str) -> bool:
        """Check if a file requires mesh context based on its extension."""
        if not isinstance(value, str):
            return False
            
        if '.' in value:
            ext = value.split('.')[-1].lower()
            return ext in self.spatial_extensions
        
        return False
    
    
    def _is_filelike_string(self, value) -> bool:
        """Check if a string looks like a file path."""
        if not isinstance(value, str):
            return False
        
        # Check for file extension
        if '.' in value:
            parts = value.split('.')
            if len(parts) >= 2:
                ext = parts[-1].lower()
                # Known file extension
                if ext in self.file_extensions:
                    return True
                # Any reasonable extension (2-4 chars)
                if 2 <= len(ext) <= 4 and ext.isalpha():
                    return True
        
        # Check for path separators (could be path without extension)
        if '/' in value or '\\' in value:
            return True
        
        # Check for URL-like patterns
        if value.startswith(('http://', 'https://', 'ftp://', 'file://')):
            return True
        
        return False

# Global instance
input_classifier = InputClassifier()