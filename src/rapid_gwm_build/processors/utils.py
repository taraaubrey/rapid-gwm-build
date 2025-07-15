
def _user_defined_processor(processor_name: str):
    from os import path
    
    try:
        # Check if processor_name is valid
        if not processor_name or not isinstance(processor_name, str):
            raise ValueError("processor_name must be a non-empty string")
        
        if '.' not in processor_name:
            raise ValueError(f"processor_name '{processor_name}' must be in format 'module.function' or 'path/to/file.function'")
        
        module_path, func_name = processor_name.rsplit('.', 1)
        
        # Determine if it's a file path or package name
        is_file_path = (
            path.sep in module_path or          # Contains path separators
            module_path.endswith('.py') or         # Ends with .py
            path.exists(module_path + '.py')    # File exists locally
        )
        
        if is_file_path:
            # Handle user-defined module from file
            return _load_from_file(module_path, func_name, processor_name)
        else:
            # Handle installed package (numpy, pandas, etc.)
            return _load_from_package(module_path, func_name, processor_name)
            
    except Exception as e:
        raise RuntimeError(f"Error loading processor '{processor_name}': {str(e)}") from e



def _load_from_file(module_path: str, func_name: str, processor_name: str):
    import os
    import sys
    from importlib.util import spec_from_file_location, module_from_spec

    """Load processor from a local Python file"""
    module_name = os.path.basename(module_path)
    file_path = module_path + '.py' if not module_path.endswith('.py') else module_path
    
    # Validate file exists and is readable
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Module file not found: {file_path}")
    if not os.access(file_path, os.R_OK):
        raise PermissionError(f"Cannot read module file: {file_path}")
    
    # Create and load module from file
    spec = spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not create module spec for {file_path}")
    
    module = module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    
    # Get and validate the processor
    if not hasattr(module, func_name):
        raise AttributeError(f"Function '{func_name}' not found in module {module_name}")
    
    processor = getattr(module, func_name)
    
    if not callable(processor):
        raise TypeError(f"'{func_name}' in module {module_name} is not callable")
    
    # For file-based modules, check if it's a class with 'process' method
    if hasattr(processor, 'process') and callable(getattr(processor, 'process')):
        return processor
    elif callable(processor):
        # It's a function, wrap it to look like a processor class
        class FunctionProcessor:
            def __init__(self, func):
                self.func = func
            def process(self, *args, **kwargs):
                return self.func(*args, **kwargs)
        return FunctionProcessor(processor)
    else:
        raise ValueError(f"Processor {processor_name} must be callable or have a 'process' method")


def _load_from_package(module_path: str, func_name: str, processor_name: str):
    from importlib import import_module
    """Load processor from an installed package"""
    
    try:
        # Import the module using standard import mechanism
        module = import_module(module_path)
    except ImportError as e:
        raise ImportError(f"Could not import package '{module_path}'. Make sure it's installed: {e}")
    
    # Get and validate the processor
    if not hasattr(module, func_name):
        available_attrs = [attr for attr in dir(module) if not attr.startswith('_')]
        raise AttributeError(
            f"'{func_name}' not found in package {module_path}. "
            f"Available attributes: {available_attrs[:10]}{'...' if len(available_attrs) > 10 else ''}"
        )
    
    processor = getattr(module, func_name)
    
    if not callable(processor):
        raise TypeError(f"'{func_name}' in package {module_path} is not callable")
    
    return processor