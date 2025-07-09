import importlib
import pkgutil
import sys

def discover_file_openers():
    """Auto-discover all file opener modules."""
    package = sys.modules[__name__]  # This package (filepath)
    for _, modname, _ in pkgutil.iter_modules(package.__path__):
        if modname != 'filetype_factory':  # Avoid circular import
            importlib.import_module(f"{__name__}.{modname}")

# Automatically discover all file openers on import
discover_file_openers()