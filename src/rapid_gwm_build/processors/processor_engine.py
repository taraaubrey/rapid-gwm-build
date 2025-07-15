"""Built-in processor configurations with direct class references."""
from ..config import CONFIG

# Import all processor classes
from typing import Callable, List
from ..registries import BUILTIN_PROCESSORS

class ProcessorEngine:
    """Orchestrates creation and execution of processors from multiple sources."""
    
    def __init__(self):
        self._processor_cache = {}

    def create_processor(self, processor_name: str) -> Callable:
        """
        Create a processor from built-in, user file, or installed package.
        
        Args:
            processor_name: Can be:
                - Built-in name: "array_to_file"
                - File path: "my_module.my_function" or "path/to/file.function_name"
                - Package: "numpy.array" or "pandas.DataFrame"
        
        Returns:
            Callable processor (function or instantiated class)
        """
        if processor_name in self._processor_cache:
            return self._processor_cache[processor_name]
        
        processor = self._resolve_processor(processor_name)
        self._processor_cache[processor_name] = processor
        return processor
    
    def execute(self, processor_name: str, *args, **kwargs):
        """
        Execute a processor with given arguments.
        
        Args:
            processor_name: Name of the processor to execute.
            *args, **kwargs: Arguments to pass to the processor.
        
        Returns:
            Result of the processor execution.
        """
        processor = self.create_processor(processor_name)
        if not callable(processor):
            raise TypeError(f"Processor '{processor_name}' is not callable")
        
        if CONFIG.get('cache_enabled', True):
            from ..cache import memory
            # Use caching if enabled
            return memory.cache(processor)(*args, **kwargs)
        else:
            # Execute without caching
            return processor(*args, **kwargs)
    
    def _resolve_processor(self, processor_name: str) -> Callable:
        """
        Resolve from built-in, user-defined file, or installed package.
        
        Args:
            processor_name: Name or path of the processor.
        
        Returns:
            Callable processor function or class instance.
        """
        
        # 1. Check built-in processors first
        if processor_name in BUILTIN_PROCESSORS:
            processor_metadata = self._load_from_builtin(processor_name)
            return processor_metadata
    
        # 2. Check if it's a user-defined file or package
        if '.' not in processor_name:
            raise ValueError(f"Invalid processor name '{processor_name}'. Must be built-in name or 'module.function' format")
        
        module_path, func_name = processor_name.rsplit('.', 1)

        # 3. Determine if it's a file path or package
        if self._is_file_path(module_path):
            return self._load_from_file(module_path, func_name)
        else:
            return self._load_from_package(module_path, func_name)

    
    def _load_from_builtin(self, processor_name: str) -> Callable:
        """
        Create built-in processor instance.
        
        Args:
            processor_name: Name of the built-in processor.
        Returns:
            Callable processor function or class instance.
        """
        processor = BUILTIN_PROCESSORS[processor_name]
        
        # If it's already a function, return as-is
        return processor['func']

    def _is_file_path(self, module_path: str) -> bool:
        """
        Determine if module_path refers to a local file.

        Args:
            module_path: Path to the module or package.
        Returns:
            bool: True if it's a file path, False if it's a package.
        """
        from os import path
        return (
            path.sep in module_path or
            module_path.endswith('.py') or
            path.exists(module_path + '.py')
        )
    
    def _load_from_file(self, module_path: str, func_name: str) -> Callable:
        """
        Load processor from a local Python file.
        
        Args:
            module_path: Path to the Python file (without .py extension).
            func_name: Name of the function or class to load from the file.
        Returns:
            Callable processor function or class instance.

        """
        from os import path
        from importlib.util import spec_from_file_location, module_from_spec
        import sys
        
        module_name = path.basename(module_path).replace('.py', '')
        file_path = module_path + '.py' if not module_path.endswith('.py') else module_path
        
        if not path.exists(file_path):
            raise FileNotFoundError(f"Module file not found: {file_path}")
        
        spec = spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not create module spec for {file_path}")
        
        module = module_from_spec(spec)
        sys.modules[f"user_defined_{module_name}"] = module
        spec.loader.exec_module(module)
        
        if not hasattr(module, func_name):
            raise AttributeError(f"Function '{func_name}' not found in {file_path}")
        
        processor = getattr(module, func_name)
        
        if not callable(processor):
            raise TypeError(f"'{func_name}' in {file_path} is not callable")
        
        # Return function as-is
        return processor
 
    def _load_from_package(self, module_path: str, func_name: str) -> Callable:
        """
        Load processor from an installed package.

        Args:
            module_path: Name of the package (e.g., "numpy", "pandas").
            func_name: Name of the function or class to load from the package.
        Returns:
            Callable processor function or class instance.
        """
        from importlib import import_module
        
        try:
            module = import_module(module_path)
        except ImportError as e:
            raise ImportError(f"Could not import package '{module_path}': {e}")
        
        if not hasattr(module, func_name):
            available = [attr for attr in dir(module) if not attr.startswith('_')]
            raise AttributeError(f"'{func_name}' not found in {module_path}. Available: {available[:5]}")
        
        processor = getattr(module, func_name)
        
        if not callable(processor):
            raise TypeError(f"'{func_name}' in {module_path} is not callable")
        
        # Return as-is (function or class constructor)
        return processor

    def get_available_processors(self) -> List[str]:
        """Get list of available built-in processor names."""
        return list(BUILTIN_PROCESSORS.keys())
    
    def clear_cache(self):
        """Clear the processor cache."""
        self._processor_cache.clear()

# Create a global instance of the processor engine
processor_engine = ProcessorEngine()