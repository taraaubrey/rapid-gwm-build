from cerberus import Validator
import yaml
import logging

from rapid_gwm_build.template_schema import top_level_schema


class YamlProcessor:
    def __init__(
        self,
        schema: dict,
    ):
        self.schema = schema

        logging.debug(f"Initializing YamlProcessor with schema: {self.schema}")

        self.validator = Validator(self.schema)

    def validate(self, template: dict) -> bool:
        return self.validator.validate(template)

    def get_errors(self) -> dict:
        return self.validator.errors

    def load_and_validate(self, yaml_path: str) -> dict:
        with open(yaml_path, "r") as f:
            template = yaml.safe_load(f)

        if not self.validate(template):
            logging.error(f"Template validation failed: {self.get_errors()}")
            raise ValueError(f"Template validation failed: {self.get_errors()}")

        return self.validator.normalized(template)


template_processor = YamlProcessor(schema=top_level_schema)
