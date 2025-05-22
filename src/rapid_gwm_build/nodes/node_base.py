from __future__ import annotations
from copy import deepcopy
from abc import ABC, abstractmethod

class NodeCFG:
    """
    Class to represent a node ID in the GWM file.
    """
    def __init__(
            self,
            node_type: str,
            module_key: str = None,
            module_type: str = None,
            module_name: str = None,
            attr: list = [],
            src = None,
            **kwargs):
        self._type = node_type
        self.module_type = module_type
        self.module_name = module_name
        self._attr = attr
        self._src = src
        self._dependencies = None
        self._name = None
        self._data = None  # will be loaded during execution


        if module_key:
            self.module_name = module_key.split("-")[1] if "-" in module_key else None
            self.module_type = module_key.split(".")[0]
 
    
    @property
    def type(self):
        return self._type
    
    def istemplate(self):
        """Check if the node is a template."""
        if 'template' in self.attr:
            return True
        
    
    @property
    def data(self):
        """Read-only property for data."""
        if self._data is None:
            print("Data has not been built yet. Call 'build()' first.")
            return None
        else:
            return self._data
    
    @property
    def name(self):
        if self.type == 'module':
            if self.module_name:
                self._name = self.module_name
            else:
                self._name = self.module_type
        if self._name is None:
            self._name = self.id.split('.')[-1]
        return self._name
    
    @property
    def dependencies(self):
        """
        Returns the dependencies of the node.
        """
        if self._dependencies is None:
            self._dependencies = self._get_dependencies()
        return self._dependencies
    
    @property
    def src(self):
        """
        Returns the source of the node.
        """
        return self._src
    
    @src.setter
    def src(self, value):
        """
        Sets the source of the node.
        """
        # if self.src:
        #     raise Warning("Source already set. Overwriting the source.")
        self._src = value

    @property
    def attr(self):
        """
        Returns the attributes of the node.
        """
        return self._attr
    
    @attr.setter
    def attr(self, value):
        """
        Sets the attributes of the node.
        """
        # add to list
        if isinstance(value, str):
            self._attr.append(value)
        elif isinstance(value, list):
            for i in value:
                if isinstance(i, str):
                    self._attr.append(i)
                else:
                    raise ValueError(f"Invalid attribute type: {type(i)}. Expected str.")
    
    @property
    def id(self):
        """
        Returns the ID of the node.
        """
        if self._type == 'placeholder':
            return self._placeholder_id
        return self._set_id()

    @property
    def ref_id(self):
        """
        Returns the reference ID of the node.
        """
        return f"@{self.id}"

    @classmethod
    def create(
        cls,
        **kwargs):
        """
        Factory method to create a NodeCFG instance.
        """
        return cls(**kwargs)

    @classmethod
    def from_node(cls, from_node: NodeCFG, kwargs: dict = {}):
        """
        Make a copy of the node and update it with new attributes.
        """
        # pass on 'module_type' and 'module_name'
        kwargs['module_type'] = from_node.module_type
        kwargs['module_name'] = from_node.module_name
        
        from_attr = deepcopy(from_node.attr)
        to_attr = kwargs.get('attr', None)
        if to_attr:
            if isinstance(to_attr, str):
                from_attr.append(to_attr)
            elif isinstance(to_attr, list):
                from_attr.extend(to_attr)
            kwargs['attr'] = from_attr
        else:
            kwargs['attr'] = from_attr

        new_node = cls(**kwargs)
        
        # # create a dict of the old_ncfg attributes
        # new_kwargs = {}
        # for key in ['module_type', 'module_name', 'attr']:
        #     if hasattr(from_node, key):
        #         new_kwargs[key] = deepcopy(getattr(from_node, key))
        
        # if 'attr' in kwargs.keys():
        #     new_kwargs['attr'].append(kwargs.pop('attr'))
        
        # kwargs.update(new_kwargs)
        
        # # kwargs.update(new_kwargs)
        # # Update attributes from the dictionary
        # new_ncfg = cls(**new_kwargs)
        
        # new_ncfg.update(**kwargs)
        
        return new_node
    
    def update(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)


    def _set_id(self):
        id = f"{self.type}"
        for i in [self.module_type] + self.attr:
            if i is not None:
                id += f".{i}"
        return id

    @property
    def dependencies(self) -> list:
        if self._dependencies is None:
            self._dependencies = self._get_dependencies()
        return self._dependencies
    
    
    def _get_dependencies(self):
        """
        Get the dependencies for this node. This method should be overridden in subclasses.
        """
        return self._input_dependencies(self.src)
    
    @staticmethod
    def _input_dependencies(d) -> list:
        if isinstance(d, str):
            if d.startswith("@"):
                # If the string starts with "@", return the node ID without the "@".
                return [d[1:]]
            else:
                return None
        elif isinstance(d, dict):
            dependencies = []
            for k, v in d.items():
                if isinstance(v, str) and v.startswith("@"):
                    node_id = v[1:]
                    dependencies.append(node_id)
            return dependencies
        elif isinstance(d, list):
            dependencies = []
            for item in d:
                if isinstance(item, str) and item.startswith("@"):
                    node_id = item[1:]
                    dependencies.append(node_id)
            return dependencies
    
    @abstractmethod
    def resolve(self, **kwargs):
        """
        Get the data for this node. This method should be overridden in subclasses.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    def __str__(self):
        return self.id

    def __repr__(self):
        return f"{self.id}"

    def __eq__(self, other):
        if isinstance(other, NodeCFG):
            return self.id == other.id
        return False

    def __hash__(self):
        return hash(self.id)
   