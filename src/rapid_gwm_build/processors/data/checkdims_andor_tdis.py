import numpy as np

from ...registries import register_processor


@register_processor(
    "check_data_dims_tdis",
    dependency_args={
        "nper": "@modules.tdis.nper",
        "idomain": "@mesh.domain",
    },
)
def check_data_dims_tdis(data, nper, idomain, expected_dims, **kwargs):
    """Validate and conform data dimensions for MF6 grid-based packages.

    Transformation matrix:
        scalar  → expand to target shape (any nper)
        2D + exp=2 → validate, return
        2D + exp=3 → tile across nlay
        2D + exp=4 → tile to 3D, wrap nper (nper=1 only)
        3D + exp=3 → validate, return
        3D + exp=4 → wrap nper (nper=1 only)
        4D + exp=4 → validate, return
        reduction (higher ndim → lower expected) → error
    """
    if isinstance(data, dict):
        return {
            key: _conform_data(val, idomain, nper, expected_dims)
            for key, val in data.items()
        }
    return _conform_data(data, idomain, nper, expected_dims)


def _conform_data(data, idomain, nper, expected_dims):
    """Route data through scalar expansion, list conversion, or array conformance."""
    if expected_dims not in (2, 3, 4):
        raise ValueError(
            f"expected_dims must be 2, 3, or 4. Got: {expected_dims}"
        )

    if isinstance(data, (int, float)):
        return _scalar_to_array(data, idomain, nper, expected_dims)

    if isinstance(data, list):
        data = np.asarray(data)

    if not isinstance(data, np.ndarray):
        raise TypeError(
            f"Data must be a scalar, list, or numpy array. Got: {type(data)}"
        )

    return _conform_array(data, idomain, nper, expected_dims)


def _scalar_to_array(value, idomain, nper, expected_dims):
    """Expand a scalar to the target shape, preserving dtype (int vs float)."""
    nlay, nrow, ncol = idomain.shape
    dtype = type(value)

    if expected_dims == 2:
        return np.full((nrow, ncol), value, dtype=dtype)
    elif expected_dims == 3:
        return np.full((nlay, nrow, ncol), value, dtype=dtype)
    else:  # 4
        return np.full((nper, nlay, nrow, ncol), value, dtype=dtype)


def _conform_array(data, idomain, nper, expected_dims):
    """Promote or validate an ndarray to match expected_dims."""
    nlay, nrow, ncol = idomain.shape
    ndim = data.ndim

    # Identity — already correct dimensionality
    if ndim == expected_dims:
        _validate_shape(data, idomain, nper)
        return data

    # Reduction — never allowed
    if ndim > expected_dims:
        raise ValueError(
            f"Cannot reduce {ndim}D data to expected_dims={expected_dims}. "
            f"Data shape: {data.shape}"
        )

    # Promotion — only allowed when nper == 1 (unambiguous temporal dimension)
    # except scalar-like promotions handled above
    if expected_dims == 4 and nper != 1:
        raise ValueError(
            f"Cannot promote {ndim}D data to 4D when nper={nper} > 1. "
            f"Provide correctly shaped (nper, nlay, nrow, ncol) data."
        )

    # 2D → 3D: tile across nlay layers
    if ndim == 2 and expected_dims >= 3:
        if data.shape != (nrow, ncol):
            raise ValueError(
                f"2D data shape {data.shape} does not match grid (nrow={nrow}, ncol={ncol})"
            )
        data = np.tile(data, (nlay, 1, 1))
        if expected_dims == 3:
            return data
        # fall through to 3D → 4D

    # 3D → 4D: wrap with nper=1 temporal dimension
    if data.ndim == 3 and expected_dims == 4:
        if data.shape != (nlay, nrow, ncol):
            raise ValueError(
                f"3D data shape {data.shape} does not match grid "
                f"(nlay={nlay}, nrow={nrow}, ncol={ncol})"
            )
        data = data[np.newaxis, ...]  # (1, nlay, nrow, ncol)

    _validate_shape(data, idomain, nper)
    return data


def _validate_shape(data, idomain, nper):
    """Validate that data shape matches the expected grid dimensions."""
    nlay, nrow, ncol = idomain.shape

    expected_shapes = {
        2: (nrow, ncol),
        3: (nlay, nrow, ncol),
        4: (nper, nlay, nrow, ncol),
    }

    expected = expected_shapes.get(data.ndim)
    if expected is None:
        raise ValueError(
            f"Data must be 2D, 3D, or 4D. Got {data.ndim}D with shape {data.shape}"
        )

    if data.shape != expected:
        raise ValueError(
            f"{data.ndim}D data shape {data.shape} does not match "
            f"expected {expected}"
        )
