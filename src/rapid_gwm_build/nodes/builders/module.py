from ...processors.processor_engine import processor_engine
from ...registries import register_builder
from ...result import BuildResult
from ..node_data import NodeData

@register_builder("module")
class ModuleBuilder:

    @classmethod
    def build(cls, node_data: NodeData) -> BuildResult:
        module_path, cmd_args = cls._extract_config_data(node_data)

        data = processor_engine.execute(module_path, **cmd_args)
        
        return BuildResult(
            success=True,
            data=data,
        )
    
    @staticmethod
    def _extract_config_data(node_data: NodeData) -> tuple:
        # Extract configuration from node_data
        cmd_cfg = node_data.get("cmd")
        cmd_args = {k: node_data.get_dependency_data(v) for k, v in cmd_cfg.items()}

        module_path = node_data.get("func_path", {})
        
        return module_path, cmd_args