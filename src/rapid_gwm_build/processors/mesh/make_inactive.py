from ...registries import register_processor

@register_processor("make_inactive")
def make_inactive(mask, layers=None, rows=None, cols=None):
    """
    Make specified layers, cols, or rows inactive for the data mask.

    Args:
        data: Input data mask (numpy array).
        active_domain: Active domain mask (numpy array).
        layers: List of layers to make inactive (optional).
        rows: List of rows to make inactive (optional).
        cols: List of columns to make inactive (optional).
    
    Returns:
        numpy array: Updated data mask with specified layers, rows, or columns set to inactive.
    """
    import numpy as np

    if layers is None and rows is None and cols is None:
        raise ValueError("At least one of layers, rows, or cols must be specified.")
    
    if isinstance(layers, list) and len(layers) > 0:
        mask[layers] = 0
    if isinstance(rows, list) and len(rows) > 0:
        mask[:, rows, :] = 0
    if isinstance(cols, list) and len(cols) > 0:
        mask[:, :, cols] = 0
    return mask
