from gridit import Grid

from .base import BaseNodeBuilder
from ...registries import register_builder
from ...result import BuildResult
from ...io.file_extensions import VECTOR_EXTENSIONS, RASTER_EXTENSIONS, get_file_type
from ...build_registry import build_registry

@register_builder("mesh_config")
class MeshConfigBuilder(BaseNodeBuilder):

    @classmethod
    def build(cls, parsed_node=None, build_context=None) -> BuildResult:
        mesh_type = parsed_node.get('mesh_type', 'structured')
        
        if mesh_type == 'structured':
            data = cls.build_structured(parsed_node, build_context)
        else:
            raise NotImplementedError(f"Mesh type '{mesh_type}' is not implemented.")
        
        return BuildResult(
            success=True,
            data=data,
        )
    
    @classmethod
    def build_structured(cls, parsed_node, build_context=None):
        """
        Create a Grid object based on the mesh parameters.
        """

        config = parsed_node.get('config', {})
        
        if 'domain' in config and 'resolution' in config:
            domain_fn = cls._get_data('domain', parsed_node)
            res = cls._get_data('resolution', parsed_node)

            file_type = get_file_type(domain_fn)
            
            if file_type == 'vector':
                return Grid.from_vector(fname=domain_fn, resolution=res)
            if file_type == 'raster':
                return Grid.from_raster(fname=domain_fn, resolution=res)
            else:
                raise ValueError(f"Unsupported file extension for domain:\n{domain_fn}\n\nSupported extensions: {VECTOR_EXTENSIONS + RASTER_EXTENSIONS}")


        elif 'ncol' in config and 'nrow' in config and 'xorigin' in config and 'yorigin'in config and 'resolution' in config:
            ncol = cls._get_data('ncol', parsed_node)
            nrow = cls._get_data('nrow', parsed_node)
            res = cls._get_data('resolution', parsed_node)
            xorigin = cls._get_data('xorigin', parsed_node)
            yorigin = cls._get_data('yorigin', parsed_node)
            crs = cls._get_data('crs', parsed_node, default=None)

            if isinstance(crs, int):
                from pyproj import CRS
                projection = CRS.from_epsg(crs).to_wkt()
            else:
                projection = None

            return Grid(
                resolution=res,
                shape=(ncol, nrow),
                top_left=(xorigin, yorigin),
                projection=projection,
            )
        
        else:
            raise ValueError("Insufficient parameters to create a Grid object. Provide either domain or ncol, nrow, xorigin, and yorigin.")
        
    
    @staticmethod
    def _get_data(key, parsed_node, default=None):
        """
        Extract the mesh data from the parsed node and its dependencies.
        """
        key_id = parsed_node.get('config', {}).get(key)
        
        if key_id is None and not default:
            raise ValueError(f"Key '{key}' not found in {parsed_node.id} config.")

        data = build_registry.result_from_id(key_id).data

        if data is None and not default:
            raise ValueError(f"Data for key '{key}' in {parsed_node.id} is None.")
        
        return data