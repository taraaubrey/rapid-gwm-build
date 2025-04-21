

from cerberus import Validator
import yaml
import logging

from rapid_gwm_build.template_schema import top_level_schema, default_keys

class YamlProcessor:
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

    def load_and_validate(self, yaml_path: str) -> dict:
        with open(yaml_path, 'r') as f:
            template = yaml.safe_load(f)
        
        if not self.validate(template):
            logging.error(f"Template validation failed: {self.get_errors()}")
            raise ValueError(f"Template validation failed: {self.get_errors()}")
        
        return template


template_processor = YamlProcessor(module_schema=top_level_schema, default_keys=default_keys)
