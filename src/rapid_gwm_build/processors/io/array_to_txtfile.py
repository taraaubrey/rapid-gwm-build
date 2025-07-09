"""Processor for saving arrays to files."""

import numpy as np
from pathlib import Path
from typing import Any, Union
from ..base import BaseProcessor

class ArrayToTxtProcessor(BaseProcessor):
    """Save array data to various file formats."""
    
    def __init__(self, format: str = "numpy", **kwargs):
        self.format = format.lower()
        self.kwargs = kwargs
    
    def process(self, data: np.ndarray, filepath: Union[str, Path], **kwargs) -> bool:
        """Save array to file."""
        filepath = Path(filepath)
        merged_kwargs = {**self.kwargs, **kwargs}
        
        if self.format == "numpy":
            np.save(filepath, data, **merged_kwargs)
        elif self.format == "csv":
            np.savetxt(filepath, data, delimiter=',', **merged_kwargs)
        elif self.format == "geotiff":
            self._save_as_geotiff(data, filepath, **merged_kwargs)
        else:
            raise ValueError(f"Unsupported format: {self.format}")
        
        return filepath.exists()
    
    def _save_as_geotiff(self, data: np.ndarray, filepath: Path, **kwargs):
        """Save array as GeoTIFF using rasterio."""
        import rasterio
        from rasterio.transform import from_bounds
        
        # Default transform if not provided
        transform = kwargs.get('transform', from_bounds(0, 0, data.shape[1], data.shape[0], data.shape[1], data.shape[0]))
        crs = kwargs.get('crs', 'EPSG:4326')
        
        with rasterio.open(
            filepath,
            'w',
            driver='GTiff',
            height=data.shape[0],
            width=data.shape[1],
            count=1,
            dtype=data.dtype,
            crs=crs,
            transform=transform
        ) as dst:
            dst.write(data, 1)