"""Public API for rmb — convenience functions for building groundwater models."""

import logging
from pathlib import Path

from .simulation import Simulation
from .simulation_result import SimulationResult

logger = logging.getLogger(__name__)


def build(
    yaml_path: str | Path,
    ws: str | Path | None = None,
    cache: bool = True,
    verbose: bool = False,
) -> SimulationResult:
    """One-shot build: parse YAML, build all nodes, write output files.

    Args:
        yaml_path: Path to the YAML config file.
        ws: Override the workspace directory.
        cache: Enable/disable node caching.
        verbose: Enable verbose logging.
        extra_inputs: Additional YAML files to merge into the config.

    Returns:
        SimulationResult with build summary.
    """
    if verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")

    sim = create_simulation(yaml_path, ws=ws, cache=cache)
    sim.build()
    sim.write()
    return sim.result


def validate(
    yaml_path: str | Path,
    extra_inputs: list[str | Path] | None = None,
) -> dict:
    """Parse config and build graph without executing.

    Returns a dict with validation info (node_count, edge_count, node_types).
    """
    sim = create_simulation(yaml_path)
    return sim.validate()


def create_simulation(
    yaml_path: str | Path,
    ws: str | Path | None = None,
    cache: bool = True,
    extra_inputs: list[str | Path] | None = None,
) -> Simulation:
    """Create a Simulation object for interactive use.

    Args:
        yaml_path: Path to the YAML config file.
        ws: Override the workspace directory.
        cache: Enable/disable node caching.
        extra_inputs: Additional YAML files to merge into the config.

    Returns:
        A Simulation instance ready for .build() / .validate().
    """
    return Simulation.from_yaml(
        yaml_path=yaml_path,
        ws=ws,
        cache=cache,
    )
