from .base import BaseNodeBuilder
from ...registries import register_builder
from ...result import BuildResult
from ..node_data import NodeData

@register_builder("input")
class InputBuilder(BaseNodeBuilder):
    
    @classmethod
    def build(cls, node_data: NodeData, build_context=None) -> BuildResult:
        # Extract configuration from node_data
        value, resolution_mode, opening_kwargs, use_mesh_build_context = cls._extract_config_data(node_data)
        
        # Use the factory to classify and open the input
        data = cls._get_data(
            value, 
            resolution_mode, 
            opening_kwargs, 
            use_mesh_build_context, 
        )
        
        return BuildResult(
            success=True,
            data=data,
        )
    
    @staticmethod
    def _extract_config_data(node_data: NodeData) -> tuple:
        # Extract configuration from node_data
        value = node_data.get("value", {})
        resolution_mode = node_data.get("resolution_mode", {})
        opening_kwargs = node_data.get("opening_kwargs", {})
        use_mesh_build_context = node_data.get("use_mesh_build_context", False)
        return value, resolution_mode, opening_kwargs, use_mesh_build_context

    @staticmethod
    def _get_data(value, resolution_mode, opening_kwargs, use_mesh_build_context):
        from ...io.input_classifier import input_classifier
        
        input_spec = input_classifier.classify(
            value, 
            resolution_mode=resolution_mode, 
            opening_kwargs=opening_kwargs,
            )
        
        if use_mesh_build_context:
            from ...build_context import build_context
            return input_spec.open(build_context=build_context)
        else:
            return input_spec.open()