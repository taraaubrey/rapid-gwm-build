from rapid_gwm_build.parsers.yaml_processor import template_processor

import importlib.resources
import logging

templates = {
    'mf6': r'mf6_template.yaml',
}

class TemplateLoader:
    @staticmethod
    def load_template(sim_type):
        
        filename = templates.get(sim_type)
                       
        if filename:
            with importlib.resources.path('rapid_gwm_build.templates', filename) as filepath:
                return template_processor.load_and_validate(str(filepath))
        else:
            logging.debug("No sim template file.")
            return None

