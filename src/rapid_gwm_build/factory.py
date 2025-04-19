from os import PathLike

from rapid_gwm_build.simulation_manager import SimManager

def create_simulation(name:str, cfg:dict, ws:PathLike, model_type:str='generic'):

    sim_manager = SimManager()
    sim_cls, _defaults = sim_manager.get(model_type)

    return sim_cls(name=name, model_type=model_type, cfg=cfg, ws=ws, _defaults=_defaults)