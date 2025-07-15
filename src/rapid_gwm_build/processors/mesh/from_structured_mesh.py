from ...registries import register_processor

@register_processor("from_structured_mesh", dependency_args={'mesh': '@mesh.config'})
def from_structured_mesh(value, mesh):

    mesh_functions = {
        'nrow': get_nrow,
        'ncol': get_ncol,
        'delr': get_delr,
        'delc': get_delc,
        'xorigin': get_xorigin,
        'yorigin': get_yorigin,
    }
    if value not in mesh_functions:
        raise ValueError(f"Invalid value '{value}' for from_structured_mesh. Valid values are: {list(mesh_functions.keys())}")
    
    func = mesh_functions[value]
    return func(mesh)

def get_nrow(mesh):
    """Get the number of rows in the structured mesh."""
    from gridit import Grid
    if isinstance(mesh, Grid):
        return mesh.shape[0]
    else:
        raise NotImplementedError("The 'nrow' property is not implemented for this mesh type. Please provide a Grid object.")

def get_ncol(mesh):
    """Get the number of columns in the structured mesh."""
    from gridit import Grid
    if isinstance(mesh, Grid):
        return mesh.shape[1]
    else:
        raise NotImplementedError("The 'ncol' property is not implemented for this mesh type. Please provide a Grid object.")

def get_delr(mesh):
    """Get the cell widths in the x-direction (delr) of the structured mesh."""
    from gridit import Grid
    import numpy as np

    if isinstance(mesh, Grid):
        ncol = get_ncol(mesh)
        return np.ones(ncol) * mesh.resolution
    else:
        raise NotImplementedError("The 'delr' property is not implemented for this mesh type. Please provide a Grid object.")

def get_delc(mesh):
    """Get the cell widths in the y-direction (delc) of the structured mesh."""
    from gridit import Grid
    import numpy as np

    if isinstance(mesh, Grid):
        nrow = get_nrow(mesh)
        return np.ones(nrow) * mesh.resolution
    else:
        raise NotImplementedError("The 'delr' property is not implemented for this mesh type. Please provide a Grid object.")
    
def get_xorigin(mesh):
    """Get the x-origin of the structured mesh."""
    from gridit import Grid
    if isinstance(mesh, Grid):
        return mesh.top_left[0]
    else:
        raise NotImplementedError("The 'xorigin' property is not implemented for this mesh type. Please provide a Grid object.")
    
def get_yorigin(mesh):
    """Get the y-origin of the structured mesh."""
    from gridit import Grid
    if isinstance(mesh, Grid):
        _, ymin = get_lower_left(mesh)
        return ymin
    else:
        raise NotImplementedError("The 'yorigin' property is not implemented for this mesh type. Please provide a Grid object.")

def get_lower_left(mesh):
    """Get the lower left corner of the structured mesh."""
    from gridit import Grid
    if isinstance(mesh, Grid):
        min_x = min(coord[0] for coord in mesh.corner_coords)
        min_y = min(coord[1] for coord in mesh.corner_coords)
        return min_x, min_y
    else:
        raise NotImplementedError("The 'lower_left' property is not implemented for this mesh type. Please provide a Grid object.")