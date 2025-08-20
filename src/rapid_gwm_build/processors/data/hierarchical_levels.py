from ...registries import register_processor

@register_processor(
        "hierarchical_levels",
        dependency_args={
            'mesh': '@mesh.active_domain',
            })
def hierarchical_levels(data, **kwargs):
    return data