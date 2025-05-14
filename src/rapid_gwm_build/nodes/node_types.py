
from rapid_gwm_build import utils
from rapid_gwm_build.io.input_types import InputValueSpec
from rapid_gwm_build.nodes.node_base import NodeCFG
from rapid_gwm_build.io.user_input_factory import user_input_factory
from rapid_gwm_build.pipes.pipe_registry import pipe_registry

class PipeNode(NodeCFG):
    """
    Class to represent a node ID in the GWM file.
    """
    def __init__(self, **kwargs):
        super().__init__('pipe', **kwargs)
        self._input = None
    
    
    @property
    def input(self):
        """
        Returns the input of the node.
        """
        return self._input
    
    @input.setter
    def input(self, value):
        """
        Sets the input of the node.
        """
        self._input = value
    
    def resolve(self, sim_nodes: dict=None, derived_dir=None, **kwargs):
        """
        Get the data for this node. This method should be overridden in subclasses.
        """
        func = pipe_registry.get(self.name)

        kwargs = {}
        for k, v in self.src.items():
            if isinstance(v, str) and v.startswith("@"):
                dep_node = sim_nodes.get(v[1:])
                kwargs[k] = dep_node.data
        
        # Get the input data
        if isinstance(self.input, str) and self.input.startswith("@"):
            input_node = sim_nodes[self.input[1:]]
            input_data = input_node.data

        self._data = func(input_data, node_id=self.id, outdir=derived_dir, **kwargs)

    
    def _get_dependencies(self):
        """
        Get the dependencies for this node. This method should be overridden in subclasses.
        """
        return self._input_dependencies(self.input)



class PipelineNode(NodeCFG):
    """
    Class to represent a node ID in the GWM file.
    """
    def __init__(self, **kwargs):
        super().__init__('pipeline', **kwargs)
        self._pipes = []
        # self._src_input = src_input
        self.int_data = []
    
    # @property
    # def src_input(self):
    #     """
    #     Returns the input of the node.
    #     """
    #     return self._src_input
    
    # @src_input.setter
    # def src_input(self, value):
    #     """
    #     Sets the input of the node.
    #     """
    #     if not isinstance(value, list | str):
    #         raise ValueError("Input must be a list.")
    #     self._src_input = value
    
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
        # dep_input = self._input_dependencies(self.src_input)

        # if dep_pipes and dep_input:
        #     return dep_pipes + dep_input
        # elif dep_pipes:
        #     return dep_pipes
        # elif dep_input:
        #     return dep_input
    
    
    def resolve(self, sim_nodes: dict=None, ref_dir=None, derived_dir=None, **kwargs):

        for pipe_rif in self.pipes:
            pipe_node = sim_nodes.get(pipe_rif[1:])
            self.int_data.append(pipe_node.data)
            # if not pipe_node.data:
            #     pipe_node.resolve(input_node.data, sim_nodes=sim_nodes, derived_dir=derived_dir, **kwargs)
            #     out_data = pipe_node.data
            #     self.int_data.append(out_data)
            # else:
            #     raise ValueError(f"Pipe node {pipe_node} not found in the simulation.")

        self._data = self.int_data[-1]

        


class ModuleNode(NodeCFG):
    """
    Class to represent a node ID in the GWM file.
    """
    def __init__(self, **kwargs):
        super().__init__('module', **kwargs)
        self.template = None
        self._args = None
        self._func = None


    def _get_dependencies(self):
        """
        Get the dependencies for this node. This method should be overridden in subclasses.
        """
        input_dependencies =  self._input_dependencies(self.args)
        
        # if self.template['build_dependencies']:
        #     for k, v in self.template['build_dependencies'].items():
        #         if v not in self.src:
        #             dep_id = self._input_dependencies(v)
        #             input_dependencies.append(dep_id)

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
        self._args = {}

        # get default args from the template
        default_args = utils.get_default_args(self.func)

        # replace the default args with the user provided args
        for arg, value in default_args.items():
            if self.src is None:
                self._args[arg] = value
            elif arg in self.src.keys():
                self._args[arg] = self.src.get(arg)
            elif self.template.get('build_dependencies', None):
                if arg in self.template.get('build_dependencies', {}).keys():
                    self._args[arg] = self.template['build_dependencies'].get(arg)
    
    
    def resolve(self, sim_nodes: dict=None, ref_dir=None, derived_dir=None, **kwargs):
        cmd_args = self._get_arg_data(sim_nodes)  # Get the data for the arguments
        # cmd_args = self._resolve_references(args)  # Resolve references in the args

        # build the module using the template and args
        if self.func is None:
            raise ValueError(f"Module function not found for {self.kind}")
        

        # get the function from the template
        func = utils.get_function(self.func)
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

    def _get_arg_data(self, sim_nodes: dict):
        """
        Get the data for the arguments of the module. This method should be overridden in subclasses.
        """
        arg_data = {}
        for k, v in self.args.items():
            if isinstance(v, str) and v.startswith("@"):
                dep_node = sim_nodes.get(v[1:])
                if not dep_node.data:
                    raise ValueError(f"Dependency node {dep_node} is empty.")
                arg_data[k] = dep_node.data
            else:
                arg_data[k] = v
        return arg_data


class MeshNode(NodeCFG):
    """
    Class to represent a node ID in the GWM file.
    """
    def __init__(self, kwargs: dict):
        super().__init__('mesh', **kwargs)


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