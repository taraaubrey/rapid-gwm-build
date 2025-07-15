import numpy as np
from ...registries import register_processor

@register_processor("tile_to_nlay", dependency_args={'nlay': '@mesh.nlay'})
def tile_to_nlay(array: np.ndarray, nlay):
    """
    Tile a 2D array to match the number of layers in a 3D model.

    Parameters:
        array (np.ndarray): Input 2D array to be tiled.
        nlay (int): Number of layers in the 3D model.
    Returns:
        np.ndarray: A 3D array with the input array tiled across the specified number of layers.
    """
    return np.tile(array, (nlay, 1, 1))