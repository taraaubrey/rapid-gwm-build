"""File extension constants for different file types."""

# From fiona.drvsupport.vector_driver_extensions()
VECTOR_EXTENSIONS = {
    'dxf', 'csv', 'tsv', 'psv', 'gdb', 'shp', 'dbf', 'shz',
    'shp.zip', 'fgb', 'json', 'geojson', 'geojsonl', 'geojsons',
    'gpkg', 'gpkg.zip', 'gml', 'xml', 'gmt', 'gpx', 'tab', 'mif',
    'mid', 'dgn', 'pix', 'sqlite', 'db'
}

# From rasterio.drivers.raster_driver_extensions()
RASTER_EXTENSIONS = {
    'vrt', 'tif', 'tiff', 'ntf', 'img', 'asc', 'dt0', 'dt1',
    'dt2', 'png', 'jpg', 'jpeg', 'gif', 'xpm', 'bmp', 'pix',
    'map', 'mpr', 'mpl', 'rgb', 'hgt', 'ter', 'nc', 'lbl', 'cub',
    'xml', 'ers', 'jp2', 'j2k', 'grb', 'grb2', 'grib2', 'rsw',
    'rst', 'grd', 'rda', 'kml', 'kmz', 'webp', 'pdf', 'sqlite',
    'mbtiles', 'cal', 'ct1', 'mrf', 'pgm', 'ppm', 'pnm', 'hdr',
    'bt', 'lcp', 'gtx', 'gsb', 'gvb', 'kro', 'byn', 'err', 'dem',
    'bag', 'gen', 'blx', 'sdat', 'sg-grd-z', 'xyz', 'hf2', 'dat',
    'sigdem', 'gpkg', 'gpkg.zip', 'gdb', 'bil'
}

# Combined sets for convenience
ALL_SPATIAL_EXTENSIONS = VECTOR_EXTENSIONS | RASTER_EXTENSIONS


def is_vector_file(filepath: str) -> bool:
    """Check if file extension indicates a vector file."""
    from pathlib import Path
    ext = Path(filepath).suffix.lstrip('.').lower()
    return ext in VECTOR_EXTENSIONS

def is_raster_file(filepath: str) -> bool:
    """Check if file extension indicates a raster file."""
    from pathlib import Path
    ext = Path(filepath).suffix.lstrip('.').lower()
    return ext in RASTER_EXTENSIONS

def get_file_type(filepath: str) -> str:
    """Return 'vector', 'raster', or 'unknown' based on file extension."""
    if is_vector_file(filepath):
        return 'vector'
    elif is_raster_file(filepath):
        return 'raster'
    else:
        return 'unknown'