import hashlib

from rapid_gwm_build.nodes.node import InputNode, ModuleNode

node_types = {
    'input': InputNode,
    'modules': ModuleNode,
    'pipeline': 'PipelineNode',
}

class NodeBuilder:
    def __init__(self, name_registry):
        self.name_registry = name_registry  # passed in from Simulation

    @staticmethod
    def make_input_node_name(key_path, param_value):
        """Generate a unique node ID based on the parameter key and value (e.g., file path)."""
        hash_id = hashlib.md5(str(param_value).encode()).hexdigest()[:6]
        return f"input.{key_path}.{hash_id}"

    
    @classmethod
    def parse_module_cfg(cls, key_path, cfg):
        module_node = {}
        # Add the module node
        module_node[f"module.{key_path}"] = {
            "attr": cfg
        }
        return module_node
    

    @classmethod
    def parse_input_cfg(cls, key_path, value, kwargs=None):
        input_node = {}
        input_id = cls.make_input_node_name(key_path, value)
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
        pipe_id = f'pipe.{key_path}'
        pipe_node[pipe_id] = {
                "input": value,
                "kwargs": kwargs,
            }
        # # Replace the file path with a reference to the input node
        ref_id = f"@{pipe_id}"
        return ref_id, pipe_node
    
    def build_node(self, id, template=None, **kwargs):
        node_type = id.split('.')[0]  # Extract the node type from the name
        Node = node_types.get(node_type)
        if Node is None:
            raise ValueError(f"Unknown node type: {node_type}")
        node = Node(gkey=id, template=template, **kwargs)
        self.name_registry[id] = id  # Register the node ID in the name registry
        return id, node

    # def build_input_node(self, name, path, input_type=None, open_instructions=None):
    #     node_id = f"input::{name}"
    #     node = InputNode(id=node_id, path=path, input_type=input_type, open_instructions=open_instructions or {})
    #     self.name_registry[name] = node_id
    #     return node_id, node

    # def build_module_node(self, name, package, parameters):
    #     node_id = f"module::{name}"
    #     resolved_params = self._resolve_references(parameters)
    #     node = ModuleNode(id=node_id, package=package, parameters=resolved_params)
    #     self.name_registry[name] = node_id
    #     return node_id, node

    def _resolve_references(self, params):
        def resolve(v):
            if isinstance(v, str) and v.startswith("@"):
                return self.name_registry.get(v[1:], v)
            return v
        return {k: resolve(v) for k, v in params.items()}
