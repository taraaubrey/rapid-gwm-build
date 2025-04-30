# base node class

class NodeBase:
    def __init__(self, gkey: str, ntype: str, **kwargs):
        self.gkey = gkey  # unique key for the node
        self.ntype = ntype  # type of the node (ie. module, core, etc)
        self._attributes = kwargs  # attributes of the node (ie. module, core, etc)
        # self._dependencies = []  # dependencies of the node (ie. module, core, etc)


class InputNode(NodeBase):
    def __init__(self, gkey: str, loader_type="default", **kwargs):
        super().__init__(gkey=gkey, ntype="input", **kwargs)
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


class ModuleNode(NodeBase):
    def __init__(self, gkey: str, module_type, module_name=None, parameters=None, template=None, **kwargs):
        super().__init__(gkey=gkey, ntype="modules", **kwargs)

        self.module_type = module_type  # Extract package name (e.g., 'npf' from 'npf-mynpf')
        self.name = module_name
        self.parameters = parameters # parameters for the module (ie. npf, ssm, etc)
        self.template = template  # template for the module (ie. modflow, mt3d, etc)

        if self.template:
            self.resolve_dependencies()
        
    
    def resolve_dependencies(self):
        dependencies = self.template.get("build_dependencies", None)

        if dependencies:# create a dependency identifier for each dependency
            for dep_param, dep_id in dependencies.items():
                if dep_param not in self.parameters:
                    self.parameters[dep_param] = dep_id

    def get_edge_data(self):
        return {k: v for k, v in self.parameters.items() if k.startswith("@")}