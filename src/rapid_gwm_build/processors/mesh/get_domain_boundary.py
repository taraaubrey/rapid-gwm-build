from ...registries import register_processor

@register_processor("domain_boundary", dependency_args={'active_domain': '@mesh.active_domain'})
def domain_boundary(data, active_domain):
    import numpy as np
    boundary_mask = get_interior_mask(active_domain)
    return np.logical_and(data, boundary_mask)


    
def get_interior_mask(arr):
    from scipy.ndimage import binary_erosion
    """
    Get interior boundary pixels from an active domain.
    
    Args:
        arr: numpy array where 1s represent active domain
        
    Returns:
        arr: numpy array of the same shape as input, with True for boundary pixels
    """
    # Create binary mask for active domain
    active_mask = (arr == 1)
    
    # Erode the mask - this removes boundary pixels
    eroded = binary_erosion(active_mask, axes=(1, 2))
    
    # Boundary is active pixels minus eroded pixels
    boundary_mask = active_mask & ~eroded
    
    return boundary_mask


def get_indices(arr, layer=None, value=False):
    import numpy as np
    
    # Get indices where exterior mask is True
    indices = np.where(arr)
    result = []
    for i in range(len(indices[0])):
        index_tuple = tuple(int(idx[i]) for idx in indices)
        ivalue = arr[tuple(index_tuple)]
        if layer is not None:
            index_tuple = (layer, index_tuple[0], index_tuple[1])
        if value:
            index_tuple = [index_tuple, ivalue]
        result.append(index_tuple)

    return result