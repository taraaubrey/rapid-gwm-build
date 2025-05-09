from __future__ import annotations
from copy import deepcopy
from abc import ABC, abstractmethod

from rapid_gwm_build import utils

class NodeBuilder:
    def __init__(self):
        self._node_type = {
            'mesh': MeshNode,
            'input': InputNode,
            'module': ModuleNode,
            'pipe': PipeNode,
            'pipeline': PipelineNode
        }

    @property
    def node_type(self):
        """
        Returns the node type dictionary.
        """
        return self._node_type
    
    @node_type.getter
    def node_type(self):
        """
        Returns the node type dictionary.
        """
        return self._node_type
    
    def create(
            self,
            node_type: str,
            ncfg: NodeCFG=None,
            **kwargs):
        """
        Factory method to create a NodeCFG instance.
        """
        if isinstance(ncfg, NodeCFG):
            return self._update_from_clone(old_ncfg=ncfg, new_type=node_type, **kwargs)
        elif isinstance(node_type, str):
            Node = self.node_type.get(node_type)
            return Node.create(kwargs=kwargs)
        else:
            raise ValueError(f"Invalid key type: {type(key)}. Expected str or NodeCFG.")

    
    def _update_from_clone(
            self,
            new_type: str,
            old_ncfg: NodeCFG,
            **kwargs):
        """
        Factory method to create a NodeCFG instance from an existing NodeCFG.
        """
        if not isinstance(old_ncfg, NodeCFG):
            raise ValueError(f"Invalid node configuration: {ncfg}. Expected NodeCFG instance.")
        

        if new_type != old_ncfg.type:
            Node = self.node_type.get(new_type)
            new_ncfg = Node.from_node(old_ncfg, kwargs)
        else:
            new_ncfg = deepcopy(old_ncfg)
            new_ncfg.update(**kwargs)

        return new_ncfg
    


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
            src = None):
        self.type = node_type
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
    def data(self):
        """Read-only property for data."""
        # if self._data is None:
        #     raise ValueError("Data has not been built yet. Call 'build()' first.")
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
        if self.src:
            raise Warning("Source already set. Overwriting the source.")
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
    
    @property
    def id(self):
        """
        Returns the ID of the node.
        """
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
        kwargs: dict = None):
        """
        Factory method to create a NodeCFG instance.
        """
        return cls(kwargs=kwargs)

    @classmethod
    def from_node(cls, old_ncfg: NodeCFG, kwargs: dict = None):
        # create a dict of the old_ncfg attributes
        new_kwargs = {}
        for key in ['module_type', 'module_name', 'attr']:
            if hasattr(old_ncfg, key):
                new_kwargs[key] = deepcopy(getattr(old_ncfg, key))
        
        # Update attributes from the dictionary
        new_ncfg = cls.create(new_kwargs)
        
        new_ncfg.update(**kwargs)
        
        return new_ncfg
    
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
    def _input_dependencies(d):
        if isinstance(d, str):
            return d[1:] if d.startswith("@") else None
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
    def get_data(self):
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
    

class PipeNode(NodeCFG):
    """
    Class to represent a node ID in the GWM file.
    """
    def __init__(self, kwargs: dict):
        super().__init__('pipe', **kwargs)



class PipelineNode(NodeCFG):
    """
    Class to represent a node ID in the GWM file.
    """
    def __init__(self, kwargs: dict):
        super().__init__('pipeline', **kwargs)
        self._pipes = []
    
    @property
    def pipes(self):
        """
        Returns the pipes of the node.
        """
        return self._pipes
    
    @pipes.setter
    def pipes(self, value):
        """
        Sets the pipes of the node.
        """
        if not isinstance(value, list):
            raise ValueError("Pipes must be a list.")
        self._pipes = value

    def _get_dependencies(self):
        """
        Get the dependencies for this node. This method should be overridden in subclasses.
        """
        return self._input_dependencies(self.pipes)


class ModuleNode(NodeCFG):
    """
    Class to represent a node ID in the GWM file.
    """
    def __init__(self, kwargs: dict):
        super().__init__('module', **kwargs)
        self.template = None
        self._args = None
        self._func = None


    def _get_dependencies(self):
        """
        Get the dependencies for this node. This method should be overridden in subclasses.
        """
        input_dependencies =  self._input_dependencies(self.args)
        
        # if self.template['build_dependencies']:
        #     for k, v in self.template['build_dependencies'].items():
        #         if v not in self.src:
        #             dep_id = self._input_dependencies(v)
        #             input_dependencies.append(dep_id)

        return input_dependencies

    @property
    def func(self):
        if self._func is None:
            self._set_func()
        return self._func
    
    def _set_func(self):
        if self.template:
            self._func = self.template.get("func", None)
        else:
            raise ValueError("Template is not set. Cannot set function.")
    
    @property
    def args(self):
        if self._args is None:
            self._set_args()
        return self._args
    
    def _set_args(self):
        self._args = {}

        # get default args from the template
        default_args = utils.get_default_args(self.func)

        # replace the default args with the user provided args
        for arg, value in default_args.items():
            if self.src is None:
                self._args[arg] = value
            elif arg in self.src.keys():
                self._args[arg] = self.src.get(arg)
            elif self.template.get('build_dependencies', None):
                if arg in self.template.get('build_dependencies', {}).keys():
                    self._args[arg] = self.template['build_dependencies'].get(arg)
    
    
    def build(self, args={}):
        cmd_args = self._resolve_references(args)  # Resolve references in the args

        # build the module using the template and args
        if self.func is None:
            raise ValueError(f"Module function not found for {self.kind}")
        

        # get the function from the template
        func = utils.get_function(self.func)
        # Build the module using the function and args
        self._data = func(**cmd_args)  # Set the internal _data attribute
        return self._data
    
    def _resolve_references(self, args):
        cmd_args = self.args.copy()  # Copy the default args
        for key, value in cmd_args.items():
            if isinstance(value, str) and value.startswith("@"):
                dep_id = value[1:]  # Remove the "@" prefix
                ref_id = utils.match_nodeid(dep_id, args.keys())  # Check if the dependency ID is valid
                
                new_value = args.get(ref_id, None)  # Get the value from the args
                cmd_args[key] = new_value  # Update the value in the cmd_args
        return cmd_args


class MeshNode(NodeCFG):
    """
    Class to represent a node ID in the GWM file.
    """
    def __init__(self, kwargs: dict):
        super().__init__('mesh', **kwargs)


class InputNode(NodeCFG):
    """
    Class to represent a node ID in the GWM file.
    """
    def __init__(self, kwargs: dict):
        super().__init__('input', **kwargs)
    
    def get_data(self):
        """
        Get the data for this node. This method should be overridden in subclasses.
        """
        self._data = self.src
