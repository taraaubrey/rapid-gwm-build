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
