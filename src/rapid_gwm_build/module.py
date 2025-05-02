# import logging
import logging
import networkx as nx

from rapid_gwm_build.utils import inspect_class_defaults
from rapid_gwm_build.pipe_utils import pipe_registry
from rapid_gwm_build.pipeline_node import GraphPipeline

class Module:
    def __init__(
        self,
        kind: str,
        template_cfg: dict,  ## template config file (ie. yaml file)
        cfg: dict = None,  ## user cfg file (ie. yaml file)
        gkey: str = None,
        graph: nx.DiGraph = None,
        **kwargs,  # TODO these are not used
    ):
        
        self.gkey = gkey
        self.kind = kind
        self.name = None #TODO add parse logic here probably
        self.pipe_kwargs = template_cfg.get("pipe_kwargs", None)

        self._cmd = template_cfg.get("cmd")  # get the command from the config file
        self._special_kwargs = template_cfg.get("special_kwargs", {})
        self._graph = graph

        self._dependencies = template_cfg.get("build_dependencies")
        self._cfg = cfg  # config file for the module (ie. yaml file)
        self._template_cfg = template_cfg  # template config file (ie. yaml file)

        kwargs = inspect_class_defaults(
            self._cmd
        )  # this will be set to the defaults of the cmd
        self._cmd_kwargs = kwargs[
            "defaults"
        ]  # TODO: this should be a setter method for the cmd_kwargs

        # if cfg:
        #     extended_funcs = cfg.get("extended_funcs", None)
        #     if extended_funcs:
        #         for ext_func, ext_func_kwargs in extended_funcs.items():
        #             # check if the extended function is in the cmd_kwargs
        #             output = self.call_cmd(ext_func, ext_func_kwargs)
        #             if output is not None:
        #                 # update the cmd_kwargs with the output
        #                 self.update_cmd_kwargs(output)  # TODO: cmd_kwarsgs
        if self.pipe_kwargs:
            self._extract_pipeline_kwargs()
        self._output = None  # TODO this will need to have some sort of setter method

    def __repr__(self):
        # format of Module(name)
        return f"{self.__class__.__name__}({self.kind})"

    @property
    def output(self):
        if self._output is None:
            self.build()
        return self._output

    @output.setter
    def output(self, value):
        if value is None:
            logging.warning(f"{self.name}: Output is None.")
        self._output = value

    def update_cmd_kwargs(self, kwargs):
        if isinstance(kwargs, dict):
            self._cmd_kwargs.update(kwargs)
        else:
            raise ValueError("kwargs must be a dictionary.")

    def add_params(self, params: dict):  # FIXME: old method
        # check if the key is in the cmd defaults
        # check if the key is in the special methods dict
        # update the cmd defaults with the new values
        for key, value in params.items():
            if key in self.cmd_kwargs.keys():
                # special logic for special methods
                if key in self.special_methods.keys():
                    # call special method
                    print(f"Calling special method for {key} with values {value}")
                else:
                    # set the parameter value
                    print(
                        f"{key}:{value} is not a valid adjustable parameter for {self.name}"
                    )

    def call_cmd(
        self, cmd: str, cmd_kwargs: dict = None
    ):  # TODO move out to utils or something
        import importlib

        try:
            module, class_name = cmd.rsplit(".", 1)
            module = importlib.import_module(module)
            func = getattr(module, class_name)
            output = func(**cmd_kwargs)
        except ImportError as e:
            raise ImportError(f"Could not import {cmd}: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

        if output is None:
            logging.warning(f"Command {cmd} returned None.")
        return output

    def build(self):
        # self._build_dependencies(module_registry)

        # run the command with the parameters
        self.output = self.call_cmd(
            self._cmd, self._cmd_kwargs
        )  # TODO: this should be a setter method for the output

    def _extract_pipeline_kwargs(self):
        for kwarg, pipelines in self.pipe_kwargs.items():

            for pipe in pipelines:
                # get pipeline from registry
                pipe_obj = pipe_registry.get(pipe)
                if pipe_obj is None:
                    raise ValueError(f"Pipeline {pipe} not found in registry.") #TODO look in usr file
                
                self._graph.add_pipeline_node(pipe_obj)



class StressModule(Module):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class SpatialDiscretizationModule(Module):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class TemporalDiscretizationModule(Module):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
