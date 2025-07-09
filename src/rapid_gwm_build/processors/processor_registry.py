"""Built-in processor configurations with direct class references."""

# Import all processor classes
from .io import ArrayToFileProcessor, FileToArrayProcessor, FromMeshProcessor
# from .spatial import InterpolateProcessor, ResampleProcessor, ClipProcessor, ReprojectProcessor
# from .analysis import StatisticsProcessor, FilterProcessor, ThresholdProcessor

# Use direct class references instead of strings
BUILTIN_PROCESSORS = {
    "array_to_file": {
        "class": ArrayToFileProcessor,  # ✅ Direct reference
        "args": {},
    },
    "file_to_array": {
        "class": FileToArrayProcessor,
        "args": {},
    },
    "interpolate": {
        "class": InterpolateProcessor,
        "args": {"method": "linear"},
    },
    # ... etc
}

def create_processor(processor_name: str, **override_args):
    """Create processor instance."""
    config = BUILTIN_PROCESSORS[processor_name]
    processor_class = config["class"]
    args = {**config["args"], **override_args}
    return processor_class(**args)