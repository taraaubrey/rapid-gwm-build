"""Simulation class — orchestrates the full rmb pipeline."""

import logging
from pathlib import Path
from typing import Any

from .build_context import build_context
from .build_registry import build_registry
from .config import CONFIG
from .errors import BuildError, ConfigError, ValidationError
from .graph_builder import GraphBuilder
from .node_engine import NodeBuildEngine
from .nodes.parse.node_parser import NodeParser
from .parsers.config_parser import ConfigParser
from .registries import BUILDER_REGISTRY
from .rmb_runner import RMBRunner
from .simulation_result import SimulationResult

logger = logging.getLogger(__name__)


class Simulation:
    """Encapsulates the full rmb pipeline: parse → graph → build → write.

    Usage::

        sim = Simulation.from_yaml("model.yaml")
        sim.build()
        sim.write()
        print(sim.result)

    Or for validation only::

        sim = Simulation.from_yaml("model.yaml")
        info = sim.validate()
    """

    def __init__(self, config: dict, yaml_path: Path, template: dict | None = None):
        self._config = config
        self._yaml_path = Path(yaml_path)
        self._template = template or config.get("template", {})
        self._setup = config.get("simulation", {}).get("setup", {})

        self._graph_builder: GraphBuilder | None = None
        self._runner: RMBRunner | None = None
        self._built = False
        self._written = False
        self._errors: list[str] = []

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def from_yaml(
        cls,
        yaml_path: str | Path,
        ws: str | Path | None = None,
        cache: bool = True,
    ) -> "Simulation":
        """Parse a YAML config and return a ready-to-build Simulation.

        Args:
            yaml_path: Path to the primary YAML config file.
            extra_inputs: Additional YAML files to merge into the config.
            ws: Override the workspace directory.
            cache: Enable/disable node caching.
        """
        yaml_path = Path(yaml_path)
        if not yaml_path.exists():
            raise ConfigError(f"Config file not found: {yaml_path}")

        try:
            config = ConfigParser.parse(str(yaml_path))
        except (ValueError, KeyError, FileNotFoundError) as exc:
            raise ConfigError(str(exc)) from exc

        # Apply overrides
        CONFIG["cache_enabled"] = cache
        CONFIG["cache_nodes"] = cache

        if ws is not None:
            config.setdefault("simulation", {}).setdefault("setup", {})["ws"] = str(ws)

        # TODO: sim_ws auto-wiring — users must specify the workspace path twice:
        # once in simulation.setup.ws (rmb) and again in modules.sim.cmd.sim_ws (flopy).
        # Auto-populate modules.sim.cmd.sim_ws from setup.ws here if not already set,
        # so users only need to set it once.
        return cls(config=config, yaml_path=yaml_path)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def workspace(self) -> Path | None:
        ws = self._setup.get("ws")
        return Path(ws) if ws else None

    @property
    def graph(self) -> GraphBuilder | None:
        return self._graph_builder

    @property
    def result(self) -> SimulationResult:
        return SimulationResult(
            success=self._built and not self._errors,
            workspace=self.workspace,
            built_nodes={
                nid: build_registry.result_from_id(nid)
                for nid in build_registry.list_built_nodes()
            },
            build_history=build_registry.get_build_history(),
            errors=list(self._errors),
        )

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def build(self) -> SimulationResult:
        """Parse nodes, construct DAG, and execute the topological build."""
        # Reset global state for a clean run
        build_registry.clear_all()
        build_context.reset()

        # Ensure workspace exists
        if self.workspace:
            self.workspace.mkdir(parents=True, exist_ok=True)

        try:
            self._parse_and_build_graph()
            self._execute_build()
            self._built = True
        except Exception as exc:
            self._errors.append(str(exc))
            logger.error("Build failed: %s", exc)
            raise BuildError(str(exc)) from exc

        logger.info("Build complete — %d nodes built", len(build_registry.list_built_nodes()))
        return self.result

    def _parse_and_build_graph(self):
        """Parse config into nodes and construct the DAG."""
        parser = NodeParser(sim_template=self._template)

        sim_cfg = self._config.get("simulation", {}).copy()
        # Remove setup block — it's metadata, not a node type
        sim_cfg.pop("setup", None)

        logger.info("Parsing simulation config...")
        for key, val in sim_cfg.items():
            logger.info("  Parsing %s...", key)
            parser.parse_node(node_type=key, config=val)

        all_nodes = parser.get_all_nodes()
        logger.info("  Total nodes created: %d", len(all_nodes))

        logger.info("Building dependency graph...")
        self._graph_builder = GraphBuilder(all_nodes)
        self._graph_builder.build()

    def _execute_build(self):
        """Execute the topological build via RMBRunner."""
        sG = self._graph_builder.get_subgraph(ntype="module")
        cG = self._graph_builder.get_subgraph(ntype="mesh_config")

        engine = NodeBuildEngine(registry=BUILDER_REGISTRY)
        self._runner = RMBRunner(graph=sG, mesh_graph=cG, engine=engine)

        logger.info("Executing build...")
        self._runner.run()

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def write(self):
        """Write simulation output files to the workspace directory.

        Requires ``build()`` to have been called first.
        """
        if not self._built:
            raise BuildError("Cannot write — simulation has not been built yet. Call build() first.")

        write_config = self._template.get("write", {})
        if not write_config:
            logger.warning("No 'write' config found in template — nothing to write.")
            return

        for _step_key, step in sorted(write_config.items(), key=lambda x: x[0]):
            func_spec = step.get("func", [])
            if len(func_spec) != 2:
                logger.warning("Skipping write step with unexpected func spec: %s", func_spec)
                continue

            node_ref, method_name = func_spec
            # Resolve @-prefixed node references
            node_id = node_ref.lstrip("@")
            result = build_registry.result_from_id(node_id)
            if result is None or result.data is None:
                raise BuildError(f"Write step references node '{node_id}' which was not built.")

            logger.info("Writing: %s.%s()", node_id, method_name)
            method = getattr(result.data, method_name, None)
            if method is None:
                raise BuildError(
                    f"Built object for '{node_id}' has no method '{method_name}'."
                )
            method()

        self._written = True
        logger.info("Files written to %s", self.workspace)

    # ------------------------------------------------------------------
    # Validate
    # ------------------------------------------------------------------

    def validate(self) -> dict[str, Any]:
        """Parse config and build graph without executing. Returns validation info.

        Useful for checking config correctness and visualizing the DAG.
        """
        try:
            self._parse_and_build_graph()
        except Exception as exc:
            raise ValidationError(str(exc)) from exc

        graph = self._graph_builder.graph
        return {
            "valid": True,
            "node_count": graph.number_of_nodes(),
            "edge_count": graph.number_of_edges(),
            "node_types": _count_node_types(graph),
            "workspace": str(self.workspace) if self.workspace else None,
        }

    # ------------------------------------------------------------------
    # Config inspection
    # ------------------------------------------------------------------

    def show_resolved_config(self) -> dict[str, Any]:
        """Return the fully-resolved config that would be used at build time.

        This merges function-signature defaults, template ``build_dependencies``,
        and user-supplied ``cmd`` values — in that priority order — so you can see
        exactly what parameters will be passed to each flopy function without
        running the build.

        Priority (lowest → highest): function defaults < template < user cmd

        Returns a dict keyed by module name with the effective ``cmd`` config.
        Does not modify any simulation state.
        """
        import inspect

        template_modules = self._template.get("modules", {})
        sim_modules = self._config.get("simulation", {}).get("modules", {})

        resolved: dict[str, Any] = {}

        for module_key, module_cfg in sim_modules.items():
            cmd_module_name = module_key.split("-")[0] if "-" in module_key else module_key
            tmpl = template_modules.get(cmd_module_name, {})
            func_path = tmpl.get("func")

            # 1. Function-signature defaults
            func_defaults: dict[str, Any] = {}
            if func_path:
                try:
                    parts = func_path.split(".")
                    mod = __import__(".".join(parts[:-1]), fromlist=[parts[-1]])
                    func = getattr(mod, parts[-1])
                    for name, param in inspect.signature(func).parameters.items():
                        if param.default is not inspect.Parameter.empty and param.default is not None:
                            func_defaults[name] = param.default
                except Exception:
                    pass  # skip if import fails (e.g. flopy not installed)

            # 2. Template build_dependencies (scalar values only)
            tmpl_deps: dict[str, Any] = {
                k: v
                for k, v in tmpl.get("build_dependencies", {}).items()
                if not isinstance(v, dict)  # skip complex dependency specs
            }

            # 3. User cmd overrides
            user_cmd = module_cfg.get("cmd", {}) if isinstance(module_cfg, dict) else {}

            effective = {**func_defaults, **tmpl_deps, **user_cmd}
            resolved[module_key] = {
                "func": func_path,
                "effective_cmd": effective,
                "sources": {
                    k: (
                        "user_cmd" if k in user_cmd
                        else "template" if k in tmpl_deps
                        else "func_default"
                    )
                    for k in effective
                },
            }

        return resolved

    # ------------------------------------------------------------------
    # Visualization
    # ------------------------------------------------------------------

    def visualize_graph(self, subgraph: bool = False):
        """Plot the DAG. Requires build() or validate() to have been called."""
        if self._graph_builder is None:
            raise ValidationError("No graph available. Call build() or validate() first.")
        self._graph_builder.plot(subgraph=subgraph)


def _count_node_types(graph) -> dict[str, int]:
    """Count nodes by type in a networkx DiGraph."""
    counts: dict[str, int] = {}
    for _node_id, data in graph.nodes(data=True):
        ntype = data.get("ntype", "unknown")
        counts[ntype] = counts.get(ntype, 0) + 1
    return counts
