from .value import parse_value
from .pipeline import parse_pipeline

from ..config import VALUE_KEYS, PIPELINE_KEYS

def parse_named_inputs(block_config: dict, context_path: list = None,
                       resolution_mode='auto') -> None:
    if not isinstance(block_config, dict):
        raise ValueError(f"Invalid block_config type: {type(block_config)}. Expected dict.")
        
    if resolution_mode == 'literal':
        _parse_group('value', block_config, context_path, resolution_mode='literal')

    elif resolution_mode == 'auto':
        keys = set(block_config.keys())
        if keys in VALUE_KEYS:
            _parse_group('value', block_config, context_path)
        elif keys in PIPELINE_KEYS:
            _parse_group('pipeline', block_config, context_path)
    else:
        raise ValueError(f"Invalid resolution_mode '{resolution_mode}'. Expected 'auto' or 'literal'.")


def _parse_group(kind, block_config: dict, context_path: list = None, resolution_mode='auto') -> None:
    for k, v in block_config.items():
        k_context = context_path + [k]
        if kind == 'value':
            parse_value(v, k_context, resolution_mode=resolution_mode)
        elif kind == 'pipeline':
            parse_pipeline(v, k_context)