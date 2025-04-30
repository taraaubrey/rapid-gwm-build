# base node class

class NodeBase:
    def __init__(self, id: str):
        self.id = id  # unique key for the node

    @property
    def type(self):
        return self.id.split(".")[0]

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


class ModuleNode(NodeBase):
    def __init__(self, id: str, kind=None, template=None, attr=None, **kwargs):
        super().__init__(id=id)

        self.kind = kind  # Extract package name (e.g., 'npf' from 'npf-mynpf')
        self.name = id.split('.')[2]
        self.template = template  # template for the module (ie. modflow, mt3d, etc)
        self.attr = attr
    
    
    def resolve_dependencies(self):
        dependencies = self.template.get("build_dependencies", None)

        if dependencies:# create a dependency identifier for each dependency
            for dep_param, dep_id in dependencies.items():
                if dep_param not in self.parameters:
                    self.parameters[dep_param] = dep_id

    def get_edge_data(self):
        return {k: v for k, v in self.parameters.items() if k.startswith("@")}



class PipeNode(NodeBase):
    def __init__(self, id: str, **kwargs):
        super().__init__(id=id)

        self.name = id.split('.')[1]
        self.input = input  # template for the module (ie. modflow, mt3d, etc)
        self.kwargs = kwargs if kwargs else None