from typing import Callable, Dict
import importlib
import inspect
import logging

class PipeFactory:
    """
    A factory to register and retrieve functions (pipes) by name.
    """
    def __init__(self):
        self._registry: Dict[str, Callable] = {}

    def register(self, name: str, func: Callable):
        """
        Register a function with a given name.
        """
        if not callable(func):
            raise ValueError(f"The provided function for '{name}' is not callable.")
        self._registry[name] = func


    def get(self, name: str) -> Callable:
        """
        Retrieve a registered function by name. If not found, return the default function.
        """
        if name in self._registry:
            return self._registry[name]
        else:
            raise KeyError(f"No function registered with name '{name}', and no default function is set.")
        
    
    def load_all_from_module(self, module_name=None):
        """
        Load and register all functions from a specified module.
        """
        try:
            module = importlib.import_module(module_name)

            # Inspect the module and register all functions
            for name, obj in inspect.getmembers(module, inspect.isfunction):
                self.register(name, obj)

        except ModuleNotFoundError:
            raise ImportError(f"Module '{module_name}' not found.")
        except Exception as e:
            raise RuntimeError(f"Failed to load functions from module '{module_name}': {e}")


# Example usage
pipe_registry = PipeFactory()
pipe_registry.load_all_from_module("rapid_gwm_build.pipes.builtin_pipes")




# from_mesh_top = PipelineNode(
#     name="from_mesh_top",
#     operation=lambda mesh: mesh.top,
#     inkeys=['core.2Dmesh'],
#     outkeys=['data.dis.top'],
# )

# adjust_from_rbtm = PipelineNode(
#     name="adjust_top",
#     operation=adjust_top,
#     inkeys=['core.mesh.grid', 'data.sfr.rbtom'],
#     outkeys=['core.mesh-modified.grid'],
# )

# top_output = PipelineNode(
#     name="top_output",
#     operation=array2text,
#     inkeys=['dis.top'],
#     outkeys=['dis.top', 'filename.dis.top'],
# )

# from_mesh_botm = PipelineNode(
#     name="from_mesh_botm",
#     operation=lambda mesh: mesh.botm,
#     inkeys=['core.2Dmesh'],
#     outkeys=['data.dis.botm'],
# )

# discretize_cond = PipelineNode(
#     name="discretize_2D",
#     operation=discretize_2D,
#     inkeys=['usr.drn.cond', 'core.2Dmesh'],
#     outkeys=['data.drn.cond'],
# )

# discretize_elev = PipelineNode(
#     name="discretize_2D",
#     operation=discretize_2D,
#     inkeys=['usr.drn.elev', 'core.2Dmesh'],
#     outkeys=['data.drn.elev'],
# )

# stress_period_data_drn = PipelineNode(
#     name="stress_period_data_drn",
#     operation=stress_period_data,
#     inkeys=['core.2Dmesh', 'data.drn.cond', 'data.drn.elev'],
#     outkeys=['mf6.drn-mydrn.stressperioddata'],
# )


# pipe_registry = {
#     'from_mesh_top': from_mesh_top,
#     'adjust_from_rbtm': adjust_from_rbtm,
#     'top_output': top_output,
#     'from_mesh_botm': from_mesh_botm,
#     'discretize_cond': discretize_cond,
#     'discretize_elev': discretize_elev,
#     'stress_period_data_drn': stress_period_data_drn,
# }