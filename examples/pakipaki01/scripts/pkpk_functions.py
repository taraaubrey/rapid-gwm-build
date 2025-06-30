

def extract_top_of_basement(outdir, res_data, column, res, crs, fill_depth=None, save=True, **kwargs):
    import numpy as np
    import rasterio
    from rasterio.transform import from_origin

    # get the basement Z values from the input data
    basement_z = res_data[res_data[column] < 15].groupby(['X', 'Y'])['Z'].max().reset_index()
    
    # Create grid
    x_coords = np.sort(basement_z['X'].unique())
    y_coords = np.sort(basement_z['Y'].unique())
    grid = np.full((len(y_coords), len(x_coords)), np.nan)
    # If fill_depth is specified, fill the grid with that value
    if fill_depth is not None:
        grid.fill(fill_depth)

    # Map X,Y to indices
    x_idx = {x: i for i, x in enumerate(x_coords)}
    y_idx = {y: i for i, y in enumerate(y_coords)}

    for _, row in basement_z.iterrows():
        xi = x_idx[row['X']]
        yi = y_idx[row['Y']]
        grid[yi, xi] = row['Z']

    # Rasterio expects origin at top-left, so flip y if needed
    grid = np.flipud(grid)

    # Define transform
    transform = from_origin(x_coords[0] - res/2, y_coords[-1] + res/2, res, res)

    # data + metadata
    metadata = {
        'driver': 'GTiff',
        'dtype': grid.dtype,
        'count': 1,
        'width': grid.shape[1],
        'height': grid.shape[0],
        'crs': f'EPSG:{crs}',
        'transform': transform,
        'nodata': np.nan
    }

    # Save with rasterio
    if save:
        out_path = f"{outdir}/basement_z.tif"
        with rasterio.open(
            out_path,
            'w',
            **metadata
        ) as dst:
            dst.write(grid, 1)

    metadata['out_path'] = out_path
    return grid, metadata

def make_layers():
    pass