from pathlib import Path
from typing import Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from .file_openers import FileOpener

class FileTypeFactory:
    def __init__(self):
        self.registry: Dict[str, 'FileOpener'] = {}
    

    def register(self, ext: str):
        """Decorator to register file openers."""
        def decorator(opener_class):
            self.registry[ext] = opener_class()  # Create instance
            return opener_class
        return decorator
    
    def register_multiple(self, extensions: list):
        """Decorator to register one opener for multiple extensions."""
        def decorator(opener_class):
            instance = opener_class()
            for ext in extensions:
                self.registry[ext] = instance
            return opener_class
        return decorator
    
    def get(self, ext: str) -> 'FileOpener':
        try:
            return self.registry[ext]
        except KeyError:
            raise ValueError(f"Extension '{ext}' not found in registry.")
    
    def get_file_opener(self, filepath):
        if not isinstance(filepath, Path):
            filepath = Path(filepath)  # Convert string to Path
        
        self._validate(filepath)  # Ensure the filepath is valid
        return self._get_opener(filepath)  # Get the appropriate opener
    
    def _validate(self, filepath: Path):
        """Ensure the filepath is valid."""
        if not filepath.exists():
            raise FileNotFoundError(f"File '{filepath}' does not exist.")
        if not filepath.is_file():
            raise ValueError(f"Path '{filepath}' is not a file.")

    def _get_opener(self, filepath: Path):
        """Get the appropriate file opener based on the file extension."""
        ext = filepath.suffix.lstrip('.').lower()
        if ext not in self.registry:
            raise ValueError(f"No opener registered for extension '{ext}'")
        
        return self.registry[ext]

# Global instance
filetype_factory = FileTypeFactory()
