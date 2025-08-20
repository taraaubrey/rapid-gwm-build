from typing import Any
from ...registries import register_builder
from ...result import BuildResult
from ...processors.processor_engine import processor_engine
from ..node_data import NodeData
from .base import BaseNodeBuilder
from ...build_registry import build_registry


@register_builder("pipe")
class PipeBuilder(BaseNodeBuilder):

    @classmethod
    def build(cls, node_data: NodeData) -> BuildResult:
        processor_name, pipe_input, processor_args, context_path = cls._extract_config_data(node_data)
        
        if context_path is None:
            result = processor_engine.execute(processor_name, pipe_input, **processor_args)
        else:
            result = processor_engine.execute(processor_name, pipe_input, context_path=context_path, **processor_args)
        
        cls._validate_result(result)
        
        return BuildResult(
            success=True,
            data=result,
        )
    
    @classmethod
    def _extract_config_data(cls, node_data: NodeData) -> tuple:
        # Extract configuration from node_data
        processor_name = node_data.get("processor")

        if processor_name =='top_only':
            pass
        
        pipe_input = cls.fetch_data(node_data)
        
        processor_args_cfg = node_data.get('processor_args', {})
        
        if isinstance(processor_args_cfg, dict) and 'context_path' in processor_args_cfg:
            context_path = processor_args_cfg.pop('context_path')
        else:
            context_path = None
        
        processor_args = {k: build_registry.result_from_id(v).data for k, v in processor_args_cfg.items()}
        
        return processor_name, pipe_input, processor_args, context_path
    

    @staticmethod
    def fetch_data(node_data: NodeData) -> Any:

        pipe_input = node_data.get('input')
        if isinstance(pipe_input, dict):
            # If input is a dictionary, recursively fetch data for each key
            return {key: build_registry.result_from_id(value).data for key, value in pipe_input.items()}
        elif pipe_input:
            # If input is a single value, fetch it directly
            return build_registry.result_from_id(pipe_input).data
        else:
            raise ValueError("Pipe input is not defined or is empty.")
