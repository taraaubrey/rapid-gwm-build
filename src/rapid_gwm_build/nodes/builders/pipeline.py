from .base import BaseNodeBuilder
from ..node_data import NodeData
from ...build_registry import build_registry
from ...registries import register_builder
from ...result import BuildResult


@register_builder("pipeline")
class PipelineBuilder(BaseNodeBuilder):

    @classmethod
    def build(cls, node_data: NodeData) -> BuildResult:
        pipeline_output = cls._extract_config_data(node_data)
        
        cls._validate_result(pipeline_output)
        
        return BuildResult(
            success=True,
            data=pipeline_output,
        )
    
    @staticmethod
    def _extract_config_data(node_data: NodeData) -> tuple:
        # Extract configuration from node_data
        output_id = node_data.get("output")
        return build_registry.result_from_id(output_id).data