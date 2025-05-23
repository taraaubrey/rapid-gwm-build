import numpy as np
import logging 

from rapid_gwm_build import utils
from rapid_gwm_build.io.input_types import InputValueSpec
from rapid_gwm_build.nodes.node_base import NodeCFG
from rapid_gwm_build.io.user_input_factory import user_input_factory
from rapid_gwm_build.pipes.pipe_registry import pipe_registry
from rapid_gwm_build.mesh import Mesh

class PipeNode(NodeCFG):
    """
    Class to represent a node ID in the GWM file.
    """
    def __init__(self, input_id, **kwargs):
        super().__init__('pipe', **kwargs)
        self._input_id = input_id
    
    
    @property
    def input_id(self):
        """
        Returns the input of the node.
        """
        return self._input_id
    
    # @input.setter
    # def input(self, value):
    #     """
    #     Sets the input of the node.
    #     """
    #     self._input = value
    
    def resolve(self, sim_nodes: dict=None, derived_dir=None, **kwargs):
        """
        Get the data for this node. This method should be overridden in subclasses.
        """
        func = pipe_registry.get(self.name)

        # kwargs = {}
        # for k, v in self.src.items():
        #     if isinstance(v, str) and v.startswith("@"):
        #         dep_node = sim_nodes.get(v[1:])
        #         kwargs[k] = dep_node.data
        
        # Get the input data
        def resolve_input(input_id):
            if isinstance(input_id, str) and input_id.startswith("@"):
                input_node = sim_nodes[input_id[1:]]
                return resolve_input(input_node.data)
            return input_id

        input_data = resolve_input(self.input_id)

        self._data = func(input_data, node_id=self.id, outdir=derived_dir, **self.src)

    
    def _get_dependencies(self):
        """
        Get the dependencies for this node. This method should be overridden in subclasses.
        """
        input_dep = self._input_dependencies(self.input_id)
        src_dep = self._input_dependencies(self.src)
        if input_dep is not None and src_dep is not None:
            return input_dep + src_dep
        elif input_dep is not None:
            return input_dep
        elif src_dep is not None:
            return src_dep


class PipelineNode(NodeCFG):
    """
    Class to represent a node ID in the GWM file.
    """
    def __init__(self, **kwargs):
        super().__init__('pipeline', **kwargs)
        self._pipes = []
        # self._src_input = src_input
        self.int_data = []
    
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
    
    
    def resolve(self, sim_nodes: dict=None, ref_dir=None, derived_dir=None, **kwargs):

        for pipe_rif in self.pipes:
            pipe_node = sim_nodes.get(pipe_rif[1:])
            self.int_data.append(pipe_node.data)

        self._data = self.int_data[-1]


class ModuleNode(NodeCFG):
    """
    Class to represent a node ID in the GWM file.
    """
    def __init__(self, **kwargs):
        super().__init__('module', **kwargs)
        self.template = {}
        self._args = None
        self._func = None


    def _get_dependencies(self):
        """
        Get the dependencies for this node. This method should be overridden in subclasses.
        """
        input_dependencies =  self._input_dependencies(self.args)

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
        template_deps = self.template.get('build_dependencies', {})
        self._args = {}

        # get default args from the template
        default_args = utils.get_default_args(self.func)

        # replace the default args with the user provided args
        for arg, value in default_args.items():
            if arg in self.src:
                self._args[arg] = self.src.get(arg)
            elif arg in self.src.get('src', {}):
                self._args[arg] = self.src['src'].get(arg)
            elif arg in template_deps:
                self._args[arg] = template_deps.get(arg)
                    # if isinstance(val, str) and val.startswith("@"):
                    #     self._args[arg] = val
            else:
                logging.warning(f"Argument {arg} not found in source or template dependencies. Using default value.")
    
    
    def resolve(self, sim_nodes: dict=None, ref_dir=None, derived_dir=None, **kwargs):
        cmd_args = self._get_arg_data(sim_nodes)  # Get the data for the arguments

        # build the module using the template and args
        if self.func is None:
            raise ValueError(f"Module function not found for {self.kind}")
        
        # get the function from the template
        func = utils.get_function(self.func)
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

    def _get_arg_data(self, sim_nodes: dict):
        """
        Get the data for the arguments of the module. This method should be overridden in subclasses.
        """
        arg_data = {}
        for k, v in self.args.items():
            if isinstance(v, str) and v.startswith("@"):
                dep_node = sim_nodes.get(v[1:])
                if dep_node.data is None:
                    raise ValueError(f"Dependency node {dep_node} is empty.")
                arg_data[k] = dep_node.data
            else:
                arg_data[k] = v
        return arg_data


class MeshNode(NodeCFG):
    """
    Class to represent a node ID in the GWM file.
    """
    def __init__(
            self,
            param=None,
            mesh=None,
            **kwargs):
        super().__init__('mesh', **kwargs)
        self._param = param
        self._mesh = mesh #TODO: add mesh type

    @property
    def mesh(self):
        return self._mesh
    
    @mesh.setter
    def mesh(self, value):
        if value.startswith("@"):
            self._mesh = value
        else:
            raise ValueError("Cannot modify mesh. Update the source instead.")

    def _set_mesh(self, sim_nodes):
        kwargs = {}
        for k, v in self.src.items():
            if isinstance(v, str) and v.startswith("@"):
                dep_node = sim_nodes.get(v[1:])
                kwargs[k] = dep_node.data
            else:
                kwargs[k] = v

        self._mesh = Mesh(**kwargs)

    @property
    def param(self):
        return self._param
    
    @param.setter
    def param(self, value):
        self._param = value

    def _get_dependencies(self):
        src_dep = self._input_dependencies(self.src)
        # return src_dep
        mesh_dep = self._input_dependencies(self.mesh)
        if src_dep is not None and mesh_dep is not None:
            return src_dep + mesh_dep
        elif src_dep is not None:
            return src_dep
        elif mesh_dep is not None:
            return mesh_dep
    
    def resolve(self, sim_nodes: dict, **kwargs):
        """
        Get the data for this node. This method should be overridden in subclasses.
        """
        if self.id == 'mesh':
            self._set_mesh(sim_nodes)
            self._data = self.mesh
        elif self.mesh.startswith("@"):
            mesh_node = sim_nodes.get(self._mesh[1:])
            self._data = getattr(mesh_node.data, self.param)
        else:
            self._set_mesh()
            self._data = self.mesh




class InputNode(NodeCFG):
    """
    Class to represent a node ID in the GWM file.
    """
    def __init__(self, src_arg=True, **kwargs):
        super().__init__('input',  **kwargs)
        self.src_arg = src_arg #flag to specify if the input data is args
        self._input = None

    @property
    def input(self):
        if self._input is None:
            self._set_input()
        return self._input
    
    @input.setter
    def input(self, value):
        if not isinstance(value, InputValueSpec):
            raise ValueError("Input must be an instance of InputValueSpec.")
        self._input = value

    def _set_input(self):
        if self.src is None:
            raise ValueError("Source is not set. Cannot set input.")
        self._input = user_input_factory.classify_user_input(self.src, src_args=self.src_arg)

    
    def resolve(self, **kwargs):
        """
        Get the data for this node. This method should be overridden in subclasses.
        """
        self._data = self.input.open()

class TemplateNode(NodeCFG):
    """
    Class to represent a node ID in the GWM file.
    """
    def __init__(self, **kwargs):
        super().__init__('template', **kwargs)
    
    
    def resolve(self, sim_nodes: dict=None, derived_dir=None, **kwargs):
        for k, data in self.src.items():
            if isinstance(data, str) and data.startswith("@"):
                dep_node = sim_nodes.get(data[1:])
                if dep_node.data is None:
                    raise ValueError(f"Dependency node {dep_node} is empty.")
                self._data = dep_node.data
            else:
                self._data = data

    
    def _get_dependencies(self):
        """
        Get the dependencies for this node. This method should be overridden in subclasses.
        """
        return self._input_dependencies(self.src)


class PlaceholderNode(NodeCFG):

    def __init__(self, node_id, **kwargs):
        super().__init__('placeholder', **kwargs)
        self._placeholder_id = node_id