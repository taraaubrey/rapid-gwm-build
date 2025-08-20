from ..config import MESH_CONFIG_KEYS, MESH_DATA_KEYS
from ...parse import utils as parse_utils
from .named_inputs import parse_named_input

def parse_mesh(block_config: dict, context_path: list = None) -> None:
    """
    Compile the mesh configuration block into a structured format.
    
    Args:
        block (dict): The mesh configuration block.
        context_path (list, optional): Path to the current context in the configuration hierarchy.
        
    Returns:
        dict: Compiled mesh configuration.
    """
    from ..node_schemas import NodeSchemas
    
    context_path = context_path or ['mesh']
    
    # First validate the overall mesh configuration
    NodeSchemas.validate_config_strict('mesh', block_config, context_path)
    
    # create nodes for mesh configuration and data
    _parse_meshconfig_block(block_config, context_path)
    _parse_meshdata_block(block_config, context_path)
    

def _parse_meshconfig_block(block_config: dict, context_path: list = None) -> None:
    cfg = parse_utils._get_items(block_config, MESH_CONFIG_KEYS)
    meta = {'mesh_type': block_config.get('mesh_type')}

    # create and register node
    parse_utils._register_node(
        node_type='mesh_config',
        config=cfg,
        context_path=context_path + ['config'],
        metadata=meta,
    )
    
    # parse other blocks
    parse_named_input(cfg, context_path, resolution_mode='literal')


def _parse_meshdata_block(block_config: dict, context_path: list = None) -> None:
    cfg = parse_utils._get_items(block_config, MESH_DATA_KEYS)

    # create and register node
    parse_utils._register_node(
        node_type='mesh_data',
        config=cfg,
        context_path=context_path + ['data'],
    )
    
    # parse other blocks
    parse_named_input(cfg, context_path)