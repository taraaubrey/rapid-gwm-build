import hashlib

from rapid_gwm_build.nodes.node import InputNode, ModuleNode, PipeNode
from rapid_gwm_build.nodes.mesh_node import MeshNode

node_types = {
    'mesh': MeshNode,
    'input': InputNode,
    'module': ModuleNode,
    'pipe': PipeNode,
}

class NodeBuilder:
    def __init__(self, name_registry):
        self.name_registry = name_registry  # passed in from Simulation

    @staticmethod
    def hash_value(param_value):
        """Generate a unique node ID based on the parameter key and value (e.g., file path)."""
        return hashlib.md5(str(param_value).encode()).hexdigest()[:6]

    
    @classmethod
    def parse_module_cfg(cls, key_path, cfg, module_type, module_name):
        module_node = {}
        # Add the module node
        module_node[f"{key_path}"] = {
            "kind": module_type,
            "name": module_name,
            "attr": cfg
        }
        return module_node
    

    @classmethod
    def parse_input_cfg(cls, key_path, value, kwargs=None):
        input_node = {}
        # hash_id = cls.hash_value(value)
        # input_id = f'input.{key_path}.{hash_id}'
        input_id = f'input.{key_path}'
        input_node[input_id] = {
                "input": value,
                "kwargs": kwargs,
            }
        # # Replace the file path with a reference to the input node
        ref_id = f"@{input_id}"  # Mark it as a reference
        return ref_id, input_node

    @classmethod
    def parse_pipe_cfg(cls, key_path, value, kwargs=None):
        pipe_node = {}
        # hash_id = cls.hash_value(value)
        pipe_name = [k for k in value.keys()][0]
        pipe_value = [k for k in value.values()][0]
        # pipe_id = f'pipe.{pipe_name}.{hash_id}'
        pipe_id = f'pipe.{pipe_name}'
        pipe_node[pipe_id] = {
                "pipe": pipe_name,
                "input": pipe_value,
            }
        # # Replace the file path with a reference to the input node
        ref_id = f"@{pipe_id}"
        return ref_id, pipe_node
    
    def build_node(self, id, **kwargs):
        kind = id.split('.')[0]  # Extract the node type from the name
        Node = node_types.get(kind)
        if Node is None:
            raise ValueError(f"Unknown node type: {kind}")
        node = Node(id=id, **kwargs)
        self.name_registry[id] = id  # Register the node ID in the name registry
        return node

    def _resolve_references(self, params):
        def resolve(v):
            if isinstance(v, str) and v.startswith("@"):
                return self.name_registry.get(v[1:], v)
            return v
        return {k: resolve(v) for k, v in params.items()}
