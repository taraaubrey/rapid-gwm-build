def _get_items(block_config: dict, keys: set) -> dict:
    return {k: v for k, v in block_config.items() if k in keys}

def _register_node(node_type, config, context_path, metadata=None):
    from ..node_registry import register_node
    from ..node_data import NodeData

    node = NodeData(
        node_type=node_type,
        config=config,
        context_path=context_path,
        metadata=metadata,
    )

    register_node(node.id, node)

    return node.id