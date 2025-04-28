# base node class

class NodeBase:
    def __init__(self, gkey: str, ntype: str, **kwargs):
        self.gkey = gkey  # unique key for the node
        self.ntype = ntype  # type of the node (ie. module, core, etc)
        self._attributes = kwargs  # attributes of the node (ie. module, core, etc)
        self._dependencies = []  # dependencies of the node (ie. module, core, etc)


class InputNode(NodeBase):
    def __init__(self, name, path, loader_type="default", **kwargs):
        super().__init__(gkey=name, ntype="input", **kwargs)
        self.path = path
        self.loader_type = loader_type
        self.kwargs = kwargs
        self._data = None  # will be loaded during execution

    def load(self):
        if self._data is None:
            loader = InputLoaderRegistry.get(self.loader_type)
            self._data = loader(self.path, **self.kwargs)
        return self._data

