from abc import ABC, abstractmethod

from rapid_gwm_build import utils
class NodeBase:
    def __init__(self, id: str):
        self.id = id  # unique key for the node
        self._dependencies = None  # dependencies for this node
        self._data = None

    @property
    def type(self):
        return self.id.split(".")[0]
    
    @property
    def name(self):
        return self.id.split(".")[-1]
    
    @property
    def dependencies(self) -> list:
        if self._dependencies is None:
            self._dependencies = self._get_dependencies()
        return self._dependencies

    @property
    def data(self):
        """Read-only property for data."""
        # if self._data is None:
        #     raise ValueError("Data has not been built yet. Call 'build()' first.")
        return self._data
    
    @abstractmethod
    def build(self):
        """
        Build the node. This method should be overridden in subclasses.
        """
        raise NotImplementedError("Subclasses must implement this method.")
    
    @abstractmethod
    def _get_dependencies(self):
        """
        Get the dependencies for this node. This method should be overridden in subclasses.
        """
        raise NotImplementedError("Subclasses must implement this method.")
    
    @staticmethod
    def _input_dependencies(d):
        dependencies = []
        for k, v in d.items():
            if isinstance(v, str) and v.startswith("@"):
                node_id = v[1:]
                dependencies.append(node_id)
        return dependencies


class InputNode(NodeBase):
    def __init__(self, id: str, input, loader_type="default", **kwargs):
        super().__init__(id=id)
        self.input = input  # value of the input node (ie. file path)
        # self.path = path
        self.loader_type = loader_type
        self.kwargs = kwargs
        self._data = None  # will be loaded during execution
    
    def build(self):
        # load the data using the loader type
        if self.loader_type == "default":
            self._data = self.input  # TODO: implement a loader for the data

    def _get_dependencies(self):
        return None #HACK


class ModuleNode(NodeBase):
    def __init__(self, id: str, kind=None, template=None, attr=None, **kwargs):
        super().__init__(id=id)

        self.kind = id.split('.')[1]  # Extract package name (e.g., 'npf' from 'npf-mynpf')
        self.template = template  # template for the module (ie. modflow, mt3d, etc)
        self.attr = attr #TODO rename -> basically any user input

        self._args = None  # args for the module (ie. npf, mt3d, etc)
        self._data = None

        if template:
            self.func = self.template.get("func", None)  # function to call for the module

    @property
    def name(self):
        return f'{self.kind}.{self.id.split(".")[-1]}'  # Extract package name (e.g., 'npf' from 'npf-mynpf')
    
    @property
    def args(self):
        if self._args is None:
            self._set_args()
        return self._args
    
    def _get_dependencies(self):
        return self._input_dependencies(self.args)

    def _set_args(self):
        self._args = {}
        module_func = self.template.get("func", None)  # function to call for the module
        # get default args from the template
        default_args = utils.get_default_args(module_func)

        # replace the default args with the user provided args
        for arg, value in default_args.items():
            if self.attr is None:
                self._args[arg] = value
            elif arg in self.attr.keys():
                self._args[arg] = self.attr.get(arg)
            elif self.template.get('build_dependencies', None):
                if arg in self.template.get('build_dependencies', {}).keys():
                    self._args[arg] = self.template['build_dependencies'].get(arg)

    def build(self, args={}):
        cmd_args = self._resolve_references(args)  # Resolve references in the args

        # build the module using the template and args
        module_func = self.template.get("func", None)
        if module_func is None:
            raise ValueError(f"Module function not found for {self.kind}")
        

        # get the function from the template
        func = utils.get_function(module_func)
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






class PipeNode(NodeBase):
    def __init__(self, id: str, input, **kwargs):
        super().__init__(id=id)
        self.input = input  # template for the module (ie. modflow, mt3d, etc)
        self.kwargs = kwargs if kwargs else None

    def _get_dependencies(self):
        return self._input_dependencies(self.input)