pipe_schema = {
    "input": {"type": "list", "required": True},
    "cmd_key": {"type": "string", "required": True},
}

# Schema for each module
module_schema = {
    "type": {"type": "string", "required": True},
    "build_dependencies": {
        "nullable": True,
        "type": "dict",
        "keysrules": {
            "type": "string",
        },
        "valuesrules": {"type": "string"},
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
        "valuesrules": {"type": "string"},
        "required": False,
        "default": None,
    },
    "duplicates_allowed": {"type": "boolean", "required": False, "default": False},
    "discretized_data": {
        "nullable": True,
        "type": "list",
        "schema": {"type": "string"},
        "required": False,
        "default": None,
    },
    "pipes": {
        "nullable": True,
        "type": "dict",
        "valuesrules": {
            "type": "dict",
            "schema": pipe_schema,
            # 'keysrules': {
            #     'type': 'string',
            # },
            # 'valuesrules': {
            #     'type': 'dict',
            #     'schema': pipe_schema
            # },
        },
        "required": False,
        "default": None,
    },
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
