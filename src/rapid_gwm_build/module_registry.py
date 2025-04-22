from rapid_gwm_build.module import Module


class ModuleRegistry:
    def __init__(self):
        """Initialize an empty registry."""
        self._registry = {}

    def __iter__(self):
        """Iterate over the keys in the registry."""
        return iter(self._registry.keys())

    def __len__(self):
        """Get the number of modules in the registry."""
        return len(self._registry.keys())

    def values(self):
        """Get all values in the registry."""
        return self._registry.values()

    def keys(self):
        """Get all keys in the registry."""
        return self._registry.keys()

    def add(self, key: str, module: Module):
        """
        Add a module to the registry.
        :param key: Unique identifier for the module.
        :param module: The module object to add.
        :raises ValueError: If the key already exists in the registry.
        """
        if key in self._registry:
            raise ValueError(f"Module with key '{key}' already exists in the registry.")
        self._registry[key] = module

    def remove(self, key: str):
        """
        Remove a module from the registry.
        :param key: Unique identifier for the module.
        :raises KeyError: If the key does not exist in the registry.
        """
        if key not in self._registry:
            raise KeyError(f"Module with key '{key}' does not exist in the registry.")
        del self._registry[key]

    def get(self, key: str):
        """
        Get a module from the registry.
        :param key: Unique identifier for the module.
        :return: The module object.
        :raises KeyError: If the key does not exist in the registry.
        """
        if key not in self._registry:
            raise KeyError(f"Module with key '{key}' does not exist in the registry.")
        return self._registry[key]

    def update(self, key: str, module):
        """
        Update an existing module in the registry.
        :param key: Unique identifier for the module.
        :param module: The new module object to replace the existing one.
        :raises KeyError: If the key does not exist in the registry.
        """
        if key not in self._registry:
            raise KeyError(f"Module with key '{key}' does not exist in the registry.")
        self._registry[key] = module

    def clear_registry(self):
        """
        Clear all modules from the registry.
        """
        self._registry.clear()

    def __repr__(self):
        return f"ModuleRegistry({len(self._registry)} modules)"

    def _check_unique_module_name(self, name: str):  # TODO move out of class
        if name in [m for m in self._registry.keys()]:
            raise ValueError(
                f"Module {name} already exists in the simulation. Are you sure you want to add it? Make sure to use a different name if multiples of the same package."
            )
