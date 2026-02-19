import logging 

from rapid_gwm_build import utils
from rapid_gwm_build.io.input_specs import InputValueSpec
from rapid_gwm_build.nodes.node_base import NodeCFG
from rapid_gwm_build.io.input_classifier import user_input_factory
from rapid_gwm_build.pipes.pipe_registry import pipe_registry
from rapid_gwm_build.mesh import Mesh

class PipeNode(NodeCFG):
    """
    Class to represent a node ID in the GWM file.
    """
    def __init__(self, input_id, module_path=None, **kwargs):
        super().__init__('pipe', **kwargs)
        self._input_id = input_id
        self.module_path = module_path
    
    
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
        if func is None:
            func = utils.get_function_from_filepath(self.module_path)

        if func is None:
            raise ValueError(f"Function {self.name} not found in the registry or module path.")
        
        # Get the input data
        def resolve_input(input_id): 
            if isinstance(input_id, str) and input_id.startswith("@"):
                input_node = sim_nodes[input_id[1:]]
                if input_node.data is None:
                    raise ValueError(f"Dependency node {dep_node} is empty.")
                return resolve_input(input_node.data)
            return input_id

        input_data = resolve_input(self.input_id)

        func_args = {}
        for k, v in self.src.items():
            if isinstance(v, str) and v.startswith("@"):
                dep_node = sim_nodes.get(v[1:])
                if dep_node.data is None:
                    raise ValueError(f"Dependency node {dep_node} is empty.")
                func_args[k] = dep_node.data
            elif isinstance(v, list):
                func_args[k] = [resolve_input(i) for i in v]
            else:
                func_args[k] = resolve_input(v)

        self._data = func(outdir=derived_dir, **func_args)

    
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
        # self._pipes = []
        # self._src_input = src_input
        self.int_data = []
    
    # @property
    # def pipes(self):
    #     """
    #     Returns the pipes of the node.
    #     """
    #     return self._pipes
    
    # @pipes.setter
    # def pipes(self, value):
    #     """
    #     Sets the pipes of the node.
    #     """
    #     if not isinstance(value, list):
    #         raise ValueError("Pipes must be a list.")
    #     self._pipes = value

    def _get_dependencies(self):
        """
        Get the dependencies for this node. This method should be overridden in subclasses.
        """
        
        return self._input_dependencies(self.src)
    
    
    def resolve(self, sim_nodes: dict=None, ref_dir=None, derived_dir=None, **kwargs):

        for pipe_rif in self.src:
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
            if isinstance(v, str) and v.startswith("@input"):
                dep_node = sim_nodes.get(v[1:])
                kwargs[k] = dep_node.src

        self._mesh = Mesh(**kwargs)

    @property
    def param(self):
        return self._param
    
    @param.setter
    def param(self, value):
        self._param = value

    def _get_dependencies(self):
        if len(self.id.split(".")) > 1:
            if self.src:
                return ['mesh', self.src[1:]]
            else:
                return ['mesh']
        elif self.id == 'mesh':
            deps = []
            for v in self.src.values():
                if v.startswith("@input"):
                    deps.append(v[1:])
            if len(deps) > 1:
                return deps
            else:
                return None
        return None
        # src_dep = self._input_dependencies(self.src)
        # # return src_dep
        # mesh_dep = self._input_dependencies(self.mesh)
        
        # if src_dep is not None and mesh_dep is not None:
        #     return src_dep + mesh_dep
        # elif src_dep is not None:
        #     return src_dep
        # elif mesh_dep is not None:
        #     return mesh_dep
    
    def resolve(self, sim_nodes: dict, **kwargs):

        if self.id == 'mesh':
            self._set_mesh(sim_nodes)
            self._data = self.mesh
        
        else:
            mesh_node = sim_nodes.get('mesh')
            if self.param in ['nrow', 'ncol', 'nlay', 'active_domain', 'delr', 'delc', 'grid']:
                self._data = getattr(mesh_node.data, self.param)
            elif self.param in ['top', 'bottoms']:
                if self.param == 'top':
                    pipeline = sim_nodes.get(mesh_node.src['top'])
                    self._data = mesh_node.data.make_top(self.src)
                elif self.param == 'bottoms':
                    self._data = mesh_node.data.make_bottoms(self.src)
                else:
                    raise ValueError(f"Parameter {self.param} not recognized for mesh node.")
            else:
                raise ValueError(f"Parameter {self.param} not recognized for mesh node.")




class InputNode(NodeCFG):
    """
    Class to represent a node ID in the GWM file.
    """
    def __init__(self, **kwargs):
        super().__init__('input',  **kwargs)
        # Default to auto-detect input type (src_arg=False)
        # Commands are now handled through 'cmd' key structure
        self.src_arg = False
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
        data = self.input.open()
        if data is not None:
            self._data = data
        else:
            self._data = self.src

class TemplateNode(NodeCFG):
    """
    Class to represent a node ID in the GWM file.
    """
    def __init__(self, **kwargs):
        super().__init__('template', **kwargs)
    
    
    def resolve(self, sim_nodes: dict=None, derived_dir=None, **kwargs):
        for k, v in self.src.items():
            if isinstance(v, str) and v.startswith("@"):
                dep_node = sim_nodes.get(v[1:])
                if dep_node.data is None:
                    raise ValueError(f"Dependency node {dep_node} is empty.")
                self._data = dep_node.data
            else:
                self._data = v

    
    def _get_dependencies(self):
        """
        Get the dependencies for this node. This method should be overridden in subclasses.
        """
        return self._input_dependencies(self.src)


class PlaceholderNode(NodeCFG):

    def __init__(self, node_id, **kwargs):
        super().__init__('placeholder', **kwargs)
        self._placeholder_id = node_id