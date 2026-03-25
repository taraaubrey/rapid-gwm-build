# from .named_inputs import parse_named_inputs

def parse_pipeline(block_config: dict, context_path: list = None) -> None:
    """
    Parse a composite value block configuration.

    Args:
        block_config (dict): The composite value block configuration.
        context_path (list, optional): Path to the current context in the configuration hierarchy.
    """
    inputs, levels, pipeline = _get_block_config(block_config)

    if levels:
        _parse_levels(levels, inputs)


    # parse inputs
    # parse_named_inputs(inputs, context_path=context_path)


def _get_block_config(block_config: dict) -> tuple:
    inputs = block_config.get('inputs', {})
    levels = block_config.get('levels', None)
    
    if 'builtins' in block_config:
        pipeline = block_config.get('builtins', None)
    elif 'pipeline' in block_config:
        pipeline = block_config.get('pipeline', None)

    return inputs, levels, pipeline


def _parse_levels(level_config: dict | list, initial_input) -> None:

    level_input = _resolve_level_input(level_config)
    ordered_input = _resolve_ordered_input(initial_input, level_input)
    steps = _resolve_level_steps(level_config, ordered_input)
    options = _resolve_level_options(level_config)
    return level_input, steps, options


def _resolve_level_input(level_config: list | dict) -> dict:
    if isinstance(level_config, dict):
        level_input = level_config.get('inputs', None)
        _validate_level_input(level_input)
        return level_input
    elif isinstance(level_config, list):
        return level_config


def _validate_level_input(level_input: list) -> None:
    if not level_input:
        raise ValueError("Levels must have 'inputs' defined.")
    if not isinstance(level_input, list):
        raise ValueError(f"Invalid level input type: {type(level_input)}. Expected list.")


def _parse_level_input(level_input: list) -> dict:
    return {i: val for i, val in enumerate(level_input)}


def _resolve_level_steps(level_config: list | dict, input_order: list) -> None:
    hier_options = {
        'input_order': input_order
        }
    hier_step = [{
            'processor': 'hierarchical_fill',
            'options': hier_options,
            'input': input_order,
            'output': 'hierarchical_output',
            }]
    
    if not isinstance(level_config, dict):
        return hier_step
    else:
        level_extra_steps = level_config.get('steps', [])

        # adjust the first input to be the hierarchical input
        if isinstance(level_extra_steps[0], dict):
            # if 'input' is given, replace it with the hierarchical output
            if 'input' in level_extra_steps[0]:
                level_extra_steps[0]['input'] = hier_step[0]['output']

        return hier_step + level_extra_steps


def _resolve_level_options(level_config: dict) -> dict:
    options = {
        'pre_pipeline': level_config.get('pre_pipeline', True),
        'post_pipeline': level_config.get('post_pipeline', False),
    }
    
    return options


def _resolve_ordered_input(initial_input: dict, level_input: list) -> list:
    if len(initial_input) > 1:
        raise ValueError(f"When combining a pipeline with levels, you can only include a single input in the pipeline input. There is {len(initial_input)} inputs in the pipeline input.")
    

    return []