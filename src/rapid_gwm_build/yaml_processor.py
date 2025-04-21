

from cerberus import Validator
import yaml
import logging

from rapid_gwm_build.template_schema import module_schema, default_keys

class TemplateProcessor:
    def __init__(
            self,
            module_schema: dict,
            default_keys: dict,
            ):
        self.schema = module_schema
        self.default_keys = default_keys

        logging.debug(f'Initializing YamlProcessor with schema: {self.schema}')

        self.validator = Validator(self.schema)

    def validate(self, template: dict) -> bool:
        return self.validator.validate(template)

    def get_errors(self) -> dict:
        return self.validator.errors

    def normalize(self, template: dict) -> dict:
        for module in template.values():
            for key, default in self.default_keys.items():
                module.setdefault(key, default)
        return template

    def load_and_validate(self, yaml_path: str) -> dict:
        with open(yaml_path, 'r') as f:
            template = yaml.safe_load(f)
        
        for key, value in template.items():
            if not self.validate(value):
                raise ValueError(f"Template validation failed: {self.get_errors()}")
        
        return self.normalize(template)


template_processor = TemplateProcessor(module_schema=module_schema, default_keys=default_keys)
