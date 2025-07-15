def make_bottom_inactive(idomain, mask, inactive_indices):
    import numpy as np
    """
    Set layers to inactive based on a mask.

    Args:
        idomain (np.ndarray): The array representing the model domain.
        mask (np.ndarray): The mask array where 0 indicates inactive areas.
        inactive_indices (list): Indices of layers to be set to inactive.

    """
    for i in inactive_indices:
        idomain[i] = np.where(mask == 0, 0, idomain[i])
    
    return idomain

def k_layers(k, nlay, nrow, ncol, layer_mapping):
    import numpy as np

    k = np.ones((nlay, nrow, ncol)) * k  # Initialize k with ones
    for lay, val in layer_mapping.items():
        k[int(lay)] = val  # Set specific layer values based on mapping
    return k

def chd_area(x1, idomain):
    import numpy as np
    x1 = np.array(x1, dtype=bool)
    x2 = np.array(idomain[0], dtype=bool)

    return np.logical_and(x1, x2).astype(int)  # Return logical AND as integer array
