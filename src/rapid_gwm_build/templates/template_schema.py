# Schema for each module
module_schema = {
    "type": {"type": "string", "required": True},
    "build_dependencies": {
        "nullable": True,
        "type": "dict",
        "keysrules": {
            "type": "string",
        },
        # "valuesrules": {"type": "string"},
        "required": False,
        "default": None,
    },
    "allowed_to_build_default": {"type": "boolean", "required": False, "default": True},
    "runtime_dependencies": {
        "nullable": True,
        "type": "list",
        "schema": {"type": "string"},
        "required": False,
        "default": None,
    },
    "cmd": {"type": "string", "required": True},
    "pipe_kwargs": {
        "nullable": True,
        "type": "dict",
        "keysrules": {"type": "string",},
        "valuesrules": {"type": "list", "schema": {"type": "string"}},
        "required": False,
        "default": None,
    },
    "duplicates_allowed": {"type": "boolean", "required": False, "default": False},
    "data": {
        "nullable": True,
        "type": "dict",
        "keysrules": {"type": "string",}, #ex. cond, elev, etc
        "valuesrules": { #TODO not sure this is working
            "type": "list",
            "keysrules": {"type": "string",}, #name of pipeline
            "valuesrules": {"type": "list", "schema": {"type": "string"}, "required": False}, #inputs
        "required": False,
        "default": None,
    },
    },
    # "pipes": {
    #     "nullable": True,
    #     "type": "dict",
    #     "valuesrules": {
    #         "type": "dict",
    #         "schema": pipe_schema,
    #         # 'keysrules': {
    #         #     'type': 'string',
    #         # },
    #         # 'valuesrules': {
    #         #     'type': 'dict',
    #         #     'schema': pipe_schema
    #         # },
    #     },
    #     "required": False,
    #     "default": None,
    # },
}


top_level_schema = {
    "module_templates": {
        "type": "dict",
        "keysrules": {
            "type": "string",
        },
        "valuesrules": {"type": "dict", "schema": module_schema},
    }
}

pipeline_schema = {
    "type": "dict",
    "keysrules": {
        "type": "string",
    },
    "valuesrules": {
        "type": "list",
        "schema": {
            "type": "dict",
            "keysrules": {"type": "string"},
            "valuesrules": { "type": "list"},
        },
    }
}