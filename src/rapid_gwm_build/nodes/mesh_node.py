
class MeshNode:
    def __init__(self, id, **cfg):

        self.cfg = cfg

        self.resolution = cfg.get("resolution", None)
        self.nlay = cfg.get("nlay", None)
        self.nrow = cfg.get("nrow", None)
        self.ncol = cfg.get("ncol", None)
        self.xorigin = cfg.get("xorigin", None)
        self.yorigin = cfg.get("yorigin", None)

        self.top_src = cfg.get("top", None)
        self.botm_src = cfg.get("botm", None)
        self.activedomain_src = cfg.get("activedomain", None)

    @property
    def type(self):
        return 'mesh'

    def build(self):
        # This is a placeholder for the actual mesh building logic.
        # In a real implementation, this would involve creating a mesh
        # based on the node's properties and returning it.
        return f"Mesh built for node: {self.node}"
    
    def _get_dependencies(self):
        # This method should return the dependencies for the mesh node.
        # For example, it might depend on the top and bottom source files.
        return self._input_dependencies(self.cfg)