

# Schema for each module
module_schema = {
    'build_dependancies': {
        'type': 'dict',
        'keysrules': {
            'type': 'string',
        },
        'valuesrules': {
            'type': 'string'
            },
        'required': False
    },
    'runtime_dependancies': {
        'type': 'list',
        'schema': {'type': 'string'},
        'required': False
    },
    'cmd': {
        'type': 'string',
        'required': True
    },
    'special_kwargs': {
        'type': 'list',
        'schema': {'type': 'string'},
        'required': False
    },
    'duplicates_allowed': {
        'type': 'boolean',
        'required': False
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

default_keys = {
    'build_dependancies': None,
    'runtime_dependancies': None,
    'special_kwargs': None,
    'duplicates_allowed': None
}
