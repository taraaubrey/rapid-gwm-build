"""Result object returned after a simulation build."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class SimulationResult:
    """Summary of a completed simulation build."""

    success: bool
    workspace: Path | None = None
    built_nodes: dict[str, Any] = field(default_factory=dict)
    build_history: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def __repr__(self):
        n = len(self.built_nodes)
        status = "SUCCESS" if self.success else "FAILED"
        return f"SimulationResult({status}, {n} nodes built, ws={self.workspace})"
