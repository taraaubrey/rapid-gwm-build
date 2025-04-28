import logging

templates = {
    'mf6': r'src\rapid_gwm_build\mf6_template.yaml',
}

class TemplateLoader:
    @staticmethod
    def load_template(sim_type):
        from rapid_gwm_build.yaml_processor import template_processor
        
        filepath = templates.get(sim_type)
                       
        if filepath:
            return template_processor.load_and_validate(
                filepath
            )  # load the template file and validate it
        else:
            logging.debug("No sim template file.")
            return None

