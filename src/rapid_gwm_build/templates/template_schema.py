pipeline_schema = {
    "pipes": {
        "type": "dict",
        "keysrules": {
            "type": "string",
        },
        "valuesrules": {
            "type": "dict",
            "schema": {
                "type": "list",
                "keysrules": {"type": "dict"},
                "valuesrules": {"type": "dict"},
            },
        },
    },
}

# Schema for each module
module_schema = {
    "build_dependencies": {
        "nullable": True,
        "type": "dict",
        "keysrules": {
            "type": "string",
        },
        # "valuesrules": {"type": "string"},
        "required": False,
        "default": {},
    },
    "src_data_input": {"type": "dict", "required": False},
    "allowed_to_build_default": {"type": "boolean", "required": False, "default": True},
    "runtime_dependencies": {
        "nullable": True,
        "type": "list",
        "schema": {"type": "string"},
        "required": False,
        "default": None,
    },
    "func": {"type": "string", "required": True},
    "duplicates_allowed": {"type": "boolean", "required": False, "default": False},
    "data": {
        "nullable": True,
        "type": "dict",
        # "keysrules": {"type": "string",}, #ex. cond, elev, etc
        # "valuesrules": {"type": "string",}, #ex. cond, elev, etc
        # "schema": pipeline_schema,
        "required": False,
        "default": None,
    },
    "default_build": {
        "type": "dict",
    }
}


top_level_schema = {
    'write': {'type': 'dict'},
    "module_templates": {
        "type": "dict",
        "keysrules": {
            "type": "string",
        },
        "valuesrules": {"type": "dict", "schema": module_schema},
    }
}
