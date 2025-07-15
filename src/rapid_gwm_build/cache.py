from joblib import Memory
from .config import CONFIG

if CONFIG["cache_enabled"]:
    memory = Memory(CONFIG["cache_dir"], verbose=0)
else:
    memory = Memory(location=None, verbose=0)  # No-op memory