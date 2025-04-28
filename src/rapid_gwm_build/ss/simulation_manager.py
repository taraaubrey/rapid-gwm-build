
from rapid_gwm_build.ss.runners import (
    Simulation,
    # MODFLOWRunner,
    # MT3DMSRunner,
    # SUTRA5Runner,
    # SUTRA7Runner,
)

class SimManager:
    def __init__(self):
        self.runners = {
            'mf6': [Simulation, r'src\rapid_gwm_build\mf6_template.yaml'],
            # 'modflow': MODFLOWRunner,
            # 'mt3dms': MT3DMSRunner,
            # 'sutra5': SUTRA5Runner,
            # 'sutra7': SUTRA7Runner,
        }

    def register_runner(self, model_type, runner_class):
        self.runners[model_type] = runner_class

    def get(self, model_type:str):
        if model_type not in self.runners.keys():
            raise ValueError(f"Invalid model type: {model_type}")
        return self.runners[model_type]