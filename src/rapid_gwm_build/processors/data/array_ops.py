import numpy as np
from ...registries import register_processor


@register_processor("top_only")
def top_only(array: np.ndarray, keep_dims=False) -> np.ndarray:
    """
    Returns the top element of an array along a specified axis.
    
    Parameters:
        array (np.ndarray): Input array.
    
    Returns:
        np.ndarray: The top element of the input array along the specified axis.
    """
    if keep_dims:
        return array * np.array([1, 0, 0]) if array.ndim == 3 else array[0:1, :, :]
    else:
        return specific_layer(array, index=0)


@register_processor("specific_layer")
def specific_layer(data: np.ndarray, index: int):
    """
    Returns a specific layer of an array along a specified axis.
    Parameters:
        array (np.ndarray): Input array.
        index (int): Index of the layer to extract.
        axis (int): Axis along which to extract the layer. Default is 0.
    Returns:
        np.ndarray: The specified layer of the input array along the specified axis.
    """
    if isinstance(data, (int, float)):
        return data
    if isinstance(data, (int, float)):
        if data.ndim != 3:
            raise ValueError(f"Input array must be 3-dimensional, got {data.ndim} dimensions.")
        if index < 0 or index >= data.shape[0]:
            raise ValueError(f"Invalid layer index {index} for axis 0 with size {data.shape[0]}.")
        
        return data.take(indices=index, axis=0)

