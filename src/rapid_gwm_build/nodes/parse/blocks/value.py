from ..config import VALUE_KEYS
from ...parse import utils as parse_utils

def parse_value(block_config: dict, context_path: list = None, 
                resolution_mode='literal', use_mesh_build_context=False) -> None:

    if resolution_mode not in ['auto', 'literal']:
        raise ValueError(f"Invalid resolution_mode '{resolution_mode}'. Expected 'auto' or 'literal'.")
    
    if isinstance(block_config, str | int | float | bool):
        cfg = {'src': block_config}

    cfg = parse_utils._get_items(block_config, VALUE_KEYS)

    if cfg.get('src') and cfg.get('src').startswith('@'):
        return cfg.get('src')[1:]

    meta = {
        'value': cfg.get('src'),
        'resolution_mode': cfg.get('resolution_mode', resolution_mode),
        'load_options': cfg.get('load_options', {}),
        'use_mesh_build_context': cfg.get('load_options', use_mesh_build_context),
    }

    # create and register node
    parse_utils._register_node(
        node_type='mesh_config',
        config=cfg,
        context_path=context_path + ['config'],
        metadata=meta,
    )