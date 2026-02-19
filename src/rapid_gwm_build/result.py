from dataclasses import dataclass, field
from typing import Any

@dataclass
class BuildResult:
    """
    Represents the result of a build operation.
    """
    success: bool
    data: Any = None  # The created data object
    files: list[str] = field(default_factory=list)  # Saved file paths
    temp_files: list[str] = field(default_factory=list)  # Temporary files
    metadata: dict = field(default_factory=dict)  # Additional info

    def __post_init__(self):
        pass