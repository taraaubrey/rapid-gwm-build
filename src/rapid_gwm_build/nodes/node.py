from abc import ABC, abstractmethod

from rapid_gwm_build import utils
class NodeBase:
    def __init__(self, id: str):
        self.id = id  # unique key for the node
        self._dependencies = None  # dependencies for this node

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
    def __init__(self, id: str, loader_type="default", **kwargs):
        super().__init__(id=id)
        self.value = kwargs.get("value", None)  # value of the input node (ie. file path)
        # self.path = path
        self.loader_type = loader_type
        self.kwargs = kwargs
        self._data = None  # will be loaded during execution
    
    # def load(self):
    #     if self._data is None:
    #         loader = InputLoaderRegistry.get(self.loader_type)
    #         self._data = loader(self.path, **self.kwargs)
    #     return self._data
    def _get_dependencies(self):
        return None #HACK


class ModuleNode(NodeBase):
    def __init__(self, id: str, kind=None, template=None, attr=None, **kwargs):
        super().__init__(id=id)

        self.kind = id.split('.')[1]  # Extract package name (e.g., 'npf' from 'npf-mynpf')
        self.template = template  # template for the module (ie. modflow, mt3d, etc)
        self.attr = attr #TODO rename -> basically any user input

        self._args = None  # args for the module (ie. npf, mt3d, etc)

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
            elif arg in self.template['build_dependencies'].keys():
                self._args[arg] = self.template['build_dependencies'].get(arg)

    
    # def resolve_dependencies(self):
    #     dependencies = self.template.get("build_dependencies", None)

    #     if dependencies:# create a dependency identifier for each dependency
    #         for dep_param, dep_id in dependencies.items():
    #             if dep_param not in self.parameters:
    #                 self.parameters[dep_param] = dep_id

    
    def _get_dependencies(self):
        return self._input_dependencies(self.args)








class PipeNode(NodeBase):
    def __init__(self, id: str, input, **kwargs):
        super().__init__(id=id)
        self.input = input  # template for the module (ie. modflow, mt3d, etc)
        self.kwargs = kwargs if kwargs else None

    def _get_dependencies(self):
        return self._input_dependencies(self.input)