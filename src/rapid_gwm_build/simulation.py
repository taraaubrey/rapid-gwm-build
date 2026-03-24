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
        extra_inputs: list[str | Path] | None = None,
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
            config = ConfigParser.parse(str(yaml_path), extra_configs=extra_inputs)
        except (ValueError, KeyError, FileNotFoundError) as exc:
            raise ConfigError(str(exc)) from exc

        # Apply overrides
        CONFIG["cache_enabled"] = cache
        CONFIG["cache_nodes"] = cache

        if ws is not None:
            config.setdefault("simulation", {}).setdefault("setup", {})["ws"] = str(ws)

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
