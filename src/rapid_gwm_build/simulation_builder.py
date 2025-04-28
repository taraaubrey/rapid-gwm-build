class SimulationBuilder:
    @staticmethod
    def from_model_type(model_type):
        template = TemplateLoader.load(model_type)
        user_cfg = {}  # empty or default config
        return SimulationBuilder.merge_config(user_cfg, template)

    @staticmethod
    def from_user_config(path):
        user_cfg = load_yaml(path)
        model_type = user_cfg.get("model_type")
        template = TemplateLoader.load(model_type)
        return SimulationBuilder.merge_config(user_cfg, template)

    @staticmethod
    def merge_config(user_cfg, template):
        # Deep merge logic or whatever structure you’re using
        return deep_merge(template, user_cfg)
