from ..io.input_classifier import input_classifier
from ..registry import register_builder
from ..result import BuildResult

@register_builder("module")
class ModuleBuilder:

    def build(parsed_node: dict) -> BuildResult:

        
        data = []
        
        return BuildResult(
            success=True,
            data=data,
        )