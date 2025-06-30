def mbr(idomain, mbr_arr, layers):
    import pandas as pd
    import numpy as np

    mbr_list = []
    for i in layers:  # remove mbr from bottom 2 layers
        in_idomarr, idom_i = get_interior_indices(idomain[i], layer=i)  # idomainget interior indices of the mbr area
        mbr_active = np.logical_and(mbr_arr.data, in_idomarr)
        mbr_list.append(mbr_active)
    return np.stack(mbr_list, axis=0)


def get_interior_indices(arr, layer=None):
    import numpy as np
    from scipy.ndimage import binary_erosion
    """
    Extract boundary indices of an active domain (where values == 1).
    Boundary pixels are active pixels that have at least one inactive neighbor.
    
    Args:
        arr: numpy array where 1s represent active domain
        
    Returns:
        list: List of tuples representing boundary indices
    """
    # Create binary mask for active domain
    active_mask = (arr == 1)
    # Erode the mask - this removes boundary pixels
    eroded = binary_erosion(active_mask)
    # Boundary is active pixels minus eroded pixels
    boundary_mask = active_mask & ~eroded
    # Get indices where exterior mask is True
    result = get_indices(boundary_mask, layer)

    return boundary_mask, result


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



def make_layers(input, **kwargs):
    pass