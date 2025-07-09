from dataclasses import dataclass
from abc import ABC, abstractmethod
from .filetype_factory import filetype_factory
from ..file_extensions import VECTOR_EXTENSIONS, RASTER_EXTENSIONS
@dataclass
class FileOpener(ABC):
    @abstractmethod
    def get_data(self, filepath, opening_kwargs=None, mesh_context=None):
        pass


@filetype_factory.register("yaml")
@dataclass
class YamlOpener(FileOpener):
    def get_data(self, filepath, opening_kwargs=None, mesh_context=None):
        from yaml import load, BaseLoader
        opening_kwargs = opening_kwargs or {}
        
        with open(filepath, "r") as file:
            return load(file, Loader=BaseLoader, **opening_kwargs)


@filetype_factory.register_multiple(RASTER_EXTENSIONS)
@dataclass
class RasterOpener(FileOpener):
    def get_data(self, filepath, opening_kwargs={}, mesh_context=None):
        if mesh_context:
            self._with_mesh(filepath, opening_kwargs, mesh_context)
        
        else:
            import rasterio
            with rasterio.open(filepath, **opening_kwargs) as src:
                return src.read()
            
    
    def _with_mesh(self, filepath, opening_kwargs={}, mesh_context=None):
        from gridit import Grid

        if isinstance(mesh_context, Grid):
            return mesh_context.array_from_raster(fname=filepath, **opening_kwargs)
        else:
            raise NotImplementedError(
                "Mesh context must be a Grid object for vector files."
            )

@filetype_factory.register_multiple(VECTOR_EXTENSIONS)
@dataclass
class ShapefileOpener(FileOpener):
    def get_data(self, filepath, opening_kwargs={}, mesh_context=None):
        
        if mesh_context:
            self._with_mesh(filepath, opening_kwargs, mesh_context)

        else:
            import geopandas as gpd
            return gpd.read_file(filepath, **opening_kwargs)
    
    def _with_mesh(self, filepath, opening_kwargs={}, mesh_context=None):
        from gridit import Grid

        if isinstance(mesh_context, Grid):
            return mesh_context.array_from_vector(fname=filepath, **opening_kwargs)
        else:
            raise NotImplementedError(
                "Mesh context must be a Grid object for vector files."
            )


@filetype_factory.register("csv")
@dataclass
class CSVOpener(FileOpener):
    def get_data(self, filepath, opening_kwargs={}, mesh_context=None):
        import pandas as pd
        
        return pd.read_csv(filepath, **opening_kwargs)

@filetype_factory.register("txt")
@dataclass
class TxtOpener(FileOpener):
    def get_data(filepath, opening_kwargs={}, mesh_context=None):
        import numpy as np
        
        return np.loadtxt(filepath, **opening_kwargs)