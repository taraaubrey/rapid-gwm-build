from .base import BaseNodeBuilder
from ..io.input_classifier import input_classifier
from ..registry import register_builder
from ..result import BuildResult

@register_builder("input")
class InputBuilder(BaseNodeBuilder):

    def build(parsed_node, dependencies=None, build_context=None) -> BuildResult:
        # Extract configuration from parsed_node
        value = parsed_node.get("value", {})
        value_type = parsed_node.get("value_type", {})
        opening_kwargs = parsed_node.get("opening_kwargs", {})
        
        # Use the factory to classify and open the input
        input_spec = input_classifier.classify(
            value, 
            value_type=value_type, 
            opening_kwargs=opening_kwargs,
            )
        
        #get opener
        

        
        data = input_spec.open(build_context=build_context)
        
        return BuildResult(
            success=True,
            data=data,
        )