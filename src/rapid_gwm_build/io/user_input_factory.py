from typing import Dict
from rapid_gwm_build.io.input_types import (
    InputValueSpec,
    # RecursiveType,
    ValueInput,
    FilepathInput,
    # CachedInput,
    # PythonModuleInput,
    # MultiInput,
    # MathInput,
)

class UserInputFactory:
    def __init__(self):
        self._registry: Dict[str, InputValueSpec] = {}
        self._default: ValueInput = None

    @property
    def registry(self) -> Dict[str, InputValueSpec]:
        return self._registry
    @property
    def default(self) -> InputValueSpec:
        return self._default
    
    def register(self, name: str, definition: InputValueSpec):
        # TODO: error checking
        self._registry[name] = definition

    def register_default(self, name: str, definition: InputValueSpec):
        if self._default:
            raise ValueError("Default already set.")
        self._default = definition

    def get(self, value: str) -> Dict[str, type]:
        if value in self._registry:
            return self._registry[value]
        else:
            return self._default
   
    def classify_user_input(self, value: str, src_args=True) -> InputValueSpec:
        return self._get_type(value, src_args)

        # if isinstance(usertype, RecursiveType):
        #     return self._resolve_if_recursive(usertype)
        # else:
        #     return usertype
    
    def _get_type(self, value: str, src_args=True) -> InputValueSpec:
        if src_args:
            src_input = self._registry.get('value')
            return src_input.create(value)
        else:
            for input_type in self._registry.values():
                if input_type.is_type(value):
                    return input_type.create(value)

            return self._default.create(value)
    
    # def _resolve_if_recursive(self, input_spec: InputValueSpec):
    #     if isinstance(input_spec, RecursiveType):
    #         for arg in input_spec.arg_values:
    #             arg = self.classify_user_input(arg)
    #             input_spec.update_args(arg)
    #         return input_spec
    #     else:
    #         return input_spec

user_input_factory = UserInputFactory()  

# set default
user_input_factory.register_default("value", ValueInput)
# Register valid types of inputs in the yaml file
user_input_factory.register("filepath", FilepathInput)
user_input_factory.register("value", ValueInput)

# user_input_factory.register("cached", CachedInput)
# user_input_factory.register("python_module", PythonModuleInput)
# user_input_factory.register("multi", MultiInput)
# user_input_factory.register("math", MathInput)