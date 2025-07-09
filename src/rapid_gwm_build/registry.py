BUILDER_REGISTRY = {}

def register_builder(node_type: str):
    def decorator(builder):
        BUILDER_REGISTRY[node_type] = builder
        return builder
    return decorator