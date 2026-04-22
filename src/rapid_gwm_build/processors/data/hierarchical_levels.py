from ...registries import register_processor

@register_processor(
        "hierarchical_levels",
        dependency_args={
            'mesh': '@mesh.domain',
            })
def hierarchical_levels(data, **kwargs):
    return data