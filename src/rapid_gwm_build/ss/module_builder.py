import networkx as nx

from rapid_gwm_build.network_registry import NetworkRegistry
from rapid_gwm_build.utils import _parse_module_usrkey
from rapid_gwm_build.ss.module import (
    Module,
    StressModule,
    SpatialDiscretizationModule,
    TemporalDiscretizationModule,
)
import logging


class ModuleBuilder:
    """
    Tasks:
    - Creates module objects which are model specific with default input kwargs
    - Adds inter-module dependencies to the graph
    - Interacts with the module_registry
    """
    def __init__(
        self,
        graph: NetworkRegistry,
        templates: dict = None,  # template config file (ie. yaml file)
    ):
        self.module_types = {
            "simple": Module,
            "StressModule": StressModule,
            "SpatialDiscretizationModule": SpatialDiscretizationModule,
            "TemporalDiscretizationModule": TemporalDiscretizationModule,
        }
        self.graph = graph  # TODO create a Graph class
        self._templates = templates  # this is already validated

    def _check_duplicated_allowed(self, kind: str):  # TODO move to Template class
        module_registry = self.graph.module_registry()
        
        if kind in [m.kind for m in module_registry]:
            duplicates_allowed = self._templates.get(kind).get("duplicates_allowed")
            if not duplicates_allowed:
                raise ValueError(
                    f'Only one "{kind}" allowed. Remove this module or set duplicates_allowed to True in the template file.'
                )

    def _get_module_meta(self, gkey: str):
        kind, usr_name = _parse_module_usrkey(gkey)

        # checks
        self._check_duplicated_allowed(kind)

        meta = {
            "gkey": gkey,
            "kind": kind,
            "template_cfg": self._templates[kind],
            "parent_module": self._templates[kind].get("parent_module", None),
        }
        return meta

    def _create_module(self, module_type: str, module_meta: dict) -> Module:
        builder = self.module_types.get(module_type)
        module = builder(**module_meta, graph=self.graph)
        
        # add the module to the graph
        self.graph.add_node(
            module.gkey, ntype="module", module=module
        )  
        
        return module

    def from_cfg(
        self, module_key: str, module_cfg: dict
    ):  # TODO: test schema against a module template
        if module_key in self.graph.list_nodes('module'):
            logging.debug(f"Module {module_key} already exists in the graph. Skipping.")
        else:
            module_meta = self._get_module_meta(module_key)
            module_meta["cfg"] = module_cfg  # update the cfg with the user config
            module = self._create_module(
                "simple", module_meta
            )  # HACK hardcoded to simple for now

            self._build_parent_module(module)
        logging.debug("Finished building modules from config file.")

    def _build_parent_module(self, child_module: Module):
        dependencies = child_module._template_cfg["build_dependencies"]
        module_registry = self.graph.module_registry()

        if dependencies:  # TODO what if the user specified a dependancy in the cfg (ie. model is this dependancy)
            for dep_kind in dependencies.keys():
                dep_modules = [
                    m for m in module_registry if m.kind == dep_kind
                ]
                if len(dep_modules) > 1:
                    raise ValueError(
                        f'{child_module.name} cannot be linked to a required dependancy module "{dep_kind}" because there is more than one.'
                    )
                elif len(dep_modules) == 1:
                    logging.debug(
                        f"Automatically finding dependancy module {dep_kind} for {child_module.name}."
                    )
                    dep_module = [
                        m for m in module_registry if m.kind == dep_kind
                    ][0]
                elif len(dep_modules) == 0:
                    logging.debug(
                        f"Building default {dep_kind} for {child_module.name}."
                    )
                    
                    #BUG when gwf has a name this logic doesn't work; creates 2 gwfs
                    
                    # create the module from the template
                    dep_module_meta = self._get_module_meta(dep_kind)
                    dep_module = self._create_module("simple", dep_module_meta)
                    # recursive to build parent module if it has a parent module
                    self._build_parent_module(dep_module)

                cmd_key = child_module._dependencies.get(dep_kind)
                
                # add edge
                self.graph.add_edge(
                    dep_module.gkey, child_module.gkey, module_dependency=cmd_key
                )  # add the module to the graph
