class TemplateLoader:
    @staticmethod
    def load(model_type):
        path = f"templates/{model_type}.yaml"
        return load_yaml(path)
