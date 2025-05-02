def inspect_class_defaults(cls_path: str, ignore=["self", "args", "kwargs"]) -> dict:
    import importlib
    import inspect

    try:
        # Try to import the class from the specified path
        module_name, class_name = cls_path.rsplit(".", 1)
        module = importlib.import_module(module_name)
        inspect_class = getattr(module, class_name)
    except ImportError as e:
        # Handle the case where the import fails
        raise ImportError(f"Could not import {cls_path}: {e}")

    signature = inspect.signature(inspect_class.__init__)

    cmd_kwargs = {
        "defaults": {},  # default values for the parameters
        "required": [],  # positional args are required
    }

    # Loop through the parameters and get the defaults and required ones
    for name, param in signature.parameters.items():
        if name not in ignore:
            cmd_kwargs["defaults"][name] = (
                param.default
            )  # can also checkout param.annotation or param.kind
            # if empty then it is a required parameter
            if param.default == inspect.Parameter.empty:
                cmd_kwargs["required"].append(name)

    return cmd_kwargs


def set_up_ws(ws_cfg: dict, name: str) -> str:
    import os
    import shutil

    # set up ws #TODO eventually move into a new class
    if ws_cfg is not None:
        ws_path = os.path.join(ws_cfg["path"], name)
        if ws_cfg["mode"] == "overwrite":
            import shutil

            if os.path.exists(ws_path):
                shutil.rmtree(ws_path)
            os.makedirs(ws_path)
        elif ws_cfg["mode"] == "append":
            if not os.path.exists(ws_path):
                os.makedirs(ws_path)
        else:
            raise ValueError(f"Invalid workspace mode {ws_cfg['mode']}")
    else:
        ws_path = os.path.join(os.getcwd(), name)  # TODO this is the default

    return ws_path


def _parse_module_usrkey(gkey: str):
    if "-" in gkey:
        kind = gkey.split("-")[0]
        usr_modname = gkey.split("-")[1]
    else:
        kind = gkey
        usr_modname = gkey
    return kind, usr_modname
