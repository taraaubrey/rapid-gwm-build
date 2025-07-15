import os
import json

DEFAULT_CONFIG = {
    "cache_enabled": True,
    "cache_dir": ".rmb_cache",
    "cache_processors": True,
    "cache_nodes": True,
    "io_mf6_format": {
        "with_stressperiod": "{modelname}.{pkgtype}-{pkgname}_{param}_{kper}.txt",
        "without_stressperiod": "{modelname}.{pkgtype}-{pkgname}_{param}.txt",
    }
}

def load_config():
    config_path = os.environ.get("YOUR_PACKAGE_CONFIG", "config.json")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            return {**DEFAULT_CONFIG, **json.load(f)}
    return DEFAULT_CONFIG

CONFIG = load_config()