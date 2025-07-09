from ..io.input_classifier import input_classifier
from ..registry import register_builder
from ..result import BuildResult

@register_builder("pipe")
class PipeBuilder:

    @classmethod
    def build(cls, parsed_node, dependencies=None, build_context=None) -> BuildResult:
        # Extract configuration from parsed_node
        value = parsed_node.get("config", {}).get("src")
        
        # Use the factory to classify and open the input
        input_spec = input_classifier.classify(value)
        data = input_spec.open()
        
        return BuildResult(
            success=True,
            data=data,
        )
    
    def _fetch_processor(self, processor):
