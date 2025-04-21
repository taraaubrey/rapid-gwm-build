

# Schema for each module
module_schema = {
    'build_dependancies': {
        'nullable': True,
        'type': 'dict',
        'keysrules': {
            'type': 'string',
        },
        'valuesrules': {
            'type': 'string'
            },
        'required': False,
        'default': None
    },
    'allowed_to_build_default': {
        'type': 'boolean',
        'required': False,
        'default': True
    },
    'runtime_dependancies': {
        'nullable': True,
        'type': 'list',
        'schema': {'type': 'string'},
        'required': False,
        'default': None
    },
    'cmd': {
        'type': 'string',
        'required': True
    },
    'special_kwargs': {
        'nullable': True,
        'type': 'list',
        'schema': {'type': 'string'},
        'required': False,
        'default': None
    },
    'duplicates_allowed': {
        'type': 'boolean',
        'required': False,
        'default': False
    }
}

top_level_schema = {
    'module_templates': {
        'type': 'dict',
        'keysrules': {
        'type': 'string',
        },
        'valuesrules': {
            'type': 'dict',
            'schema': module_schema
        },
    }
}
