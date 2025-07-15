from ..base import BaseProcessor
from ...registries import register_processor

@register_processor(
        "check_data_dims_tdis", 
                    dependency_args={
                        'nper': '@modules.tdis.nper',
                        'idomain': '@mesh.active_domain',
                        })
def check_dims_andor_add_tdis(data, nper, idomain, expected_dims, *kwargs):
    import numpy as np

    if isinstance(data, int | float):
        return _number_to_array(data, idomain, nper, expected_dims)
    
    elif isinstance(data, np.ndarray):
        if data.ndim == expected_dims:
            _check_dims(data, nper, idomain)
            return data
        else:
            if nper == 1:
                # add a dim for stress period
                _add_tdis(data, nper)
                _check_dims(data, nper, idomain)
            else:
                raise ValueError(
                    f"Data must be in tdis format (4D array) or nper must be 1. Current shape: {data.shape}, nper: {nper}"
                )
            return data
    else:
        raise TypeError(
            f"Data must be an int, float, or numpy array. Current type: {type(data)}"
        )

def _number_to_array(data, idomain, nper, expected_dims):
    import numpy as np
    nlay, nrow, ncol = idomain.shape

    if expected_dims == 4:
        return np.ones(shape=(nper, nlay, nrow, ncol), dtype=int) * data
    elif expected_dims == 3:
        return np.ones(shape=(nlay, nrow, ncol), dtype=int) * data
    elif expected_dims == 2:
        return np.ones(shape=(nrow, ncol), dtype=int) * data
    else:
        raise ValueError(f"Expected dimensions must be 2, 3, or 4. Current: {expected_dims}")

def _check_dims(data, nper, idomain):
    import numpy as np
    nlay, nrow, ncol = idomain.shape
    if data.ndim == 4:
        if data.shape != (nper, nlay, nrow, ncol):
            raise ValueError(
                f"Data shape {data.shape} does not match expected tdis format ({nper}, {nlay}, {nrow}, {ncol})"
            )
    elif data.ndim == 3:
        if data.shape != (nlay, nrow, ncol):
            raise ValueError(
                f"Data shape {data.shape} does not match expected 3D format ({nlay}, {nrow}, {ncol})"
            )
    elif data.ndim == 2:
        if data.shape != (nrow, ncol):
            raise ValueError(
                f"Data shape {data.shape} does not match expected 2D format ({nrow}, {ncol})"
            )
    else:
        raise ValueError(f"Data must be a 2D, 3D, or 4D array. Current shape: {data.shape}, ndim: {data.ndim}")
    
def _add_tdis(data, nper):
    import numpy as np
    if nper == 1:
        data = data.reshape((nper, *data.shape))
    else:
        data = np.stack([data] * nper, axis=0)