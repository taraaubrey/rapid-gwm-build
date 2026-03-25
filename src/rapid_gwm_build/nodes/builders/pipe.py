from typing import Any
from ...registries import register_builder
from ...result import BuildResult
from ...processors.processor_engine import processor_engine
from ..node_data import NodeData
from .base import BaseNodeBuilder
from ...build_registry import build_registry


@register_builder("pipe")
class PipeBuilder(BaseNodeBuilder):
    """Builds 'pipe' nodes by resolving inputs, executing a named processor, and returning the result.

    A pipe node represents a single data-transformation step in the DAG.
    The processor is resolved by name via the ProcessorEngine and called with
    the pipe's resolved input data plus any additional processor_args.
    """

    @classmethod
    def build(cls, node_data: NodeData) -> BuildResult:
        """Orchestrate a pipe build: extract config, execute processor, validate, and return.

        Args:
            node_data: Parsed node containing processor name, input reference(s),
                       and optional processor_args.

        Returns:
            BuildResult with the processor's output stored in ``data``.
        """
        processor_name, pipe_input, processor_args, context_path = cls._extract_config_data(node_data)

        if context_path is not None:
            processor_args["context_path"] = context_path

        result = processor_engine.execute(processor_name, pipe_input, **processor_args)
        cls._validate_result(result)

        return BuildResult(
            success=True,
            data=result,
        )
    
    @classmethod
    def _extract_config_data(cls, node_data: NodeData) -> tuple:
        """Extract and resolve all configuration needed for processor execution.

        Returns:
            A tuple of (processor_name, pipe_input, processor_args, context_path)
            where processor_args values have been resolved from the build registry.
        """
        processor_name = node_data.get("processor")
        pipe_input = cls.fetch_data(node_data)

        processor_args_cfg = dict(node_data.get('processor_args', {}))

        context_path = processor_args_cfg.pop('context_path', None)

        processor_args = {k: build_registry.result_from_id(v).data for k, v in processor_args_cfg.items()}

        return processor_name, pipe_input, processor_args, context_path
    

    @staticmethod
    def fetch_data(node_data: NodeData) -> Any:
        """Resolve the pipe's input reference(s) from the build registry.

        Handles two forms:
        - Single reference string → returns the referenced node's built data.
        - Dict of {key: reference} → returns a dict of {key: built data}.

        Raises:
            ValueError: If no input is defined on the node.
        """
        pipe_input = node_data.get('input')
        if isinstance(pipe_input, dict):
            return {key: build_registry.result_from_id(value).data for key, value in pipe_input.items()}
        elif pipe_input is not None:
            return build_registry.result_from_id(pipe_input).data
        else:
            raise ValueError("Pipe input is not defined or is empty.")
