import importlib
import pkgutil
import sys

def discover_processors():
    package = sys.modules[__name__]  # This module (builders)
    for _, modname, _ in pkgutil.iter_modules(package.__path__):
        if modname != 'base':  # Skip base module to avoid double import
            importlib.import_module(f"{__name__}.{modname}")

# Automatically discover all builders on import
discover_processors()