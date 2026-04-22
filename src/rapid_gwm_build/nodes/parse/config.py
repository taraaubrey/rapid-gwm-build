

CONFIG_BLOCK_KEYS = {'simulation'} # maybe add 'data' later

SIMULATION_BLOCK_KEYS = {
    'simulation',
    }
NODE_BLOCK_KEYS = {'mesh', 'modules'}

MESH_CONFIG_KEYS = {
    'crs',
    'nrow', 'ncol',
    'nlay', 'resolution',
    'delr', 'delc',
    'dx', 'dy',
    'x_length', 'y_length',
    'xorigin', 'yorigin', 'angrot',
    'extent',
}
MESH_DATA_KEYS = {'domain', 'top', 'bottoms'}

VALUE_KEYS = {'src', 'resolution_mode', 'use_mesh_build_context', 'load_options'}

PIPELINE_KEYS = {'pipeline', 'builtin', 'levels'}
STEP_KEYS = {'processor', 'options', 'input', 'output'}

LEVEL_KEYS = {'inputs', 'steps', 'pre_pipeline', 'post_pipeline'}