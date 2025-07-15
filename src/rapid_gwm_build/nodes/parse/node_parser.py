"""
Refactored NodeParser that orchestrates specialized parsers and handles dependencies.
Removed from_node complexity in favor of explicit context paths.
Now supports both NodeCFG object creation and dict-based node data extraction.
"""

import logging
from typing import Dict, Any, List, Union

from ..node_data import NodeData
from .node_schemas import NodeSchemas

class NodeParser:
    """
    Main orchestrator for parsing all node types with dependency management.
    Uses explicit context paths instead of from_node for cleaner architecture.
    
    Can operate in two modes:
    1. Object mode: Creates NodeCFG objects (legacy compatibility)
    2. Data mode: Returns structured dict data (new workflow)
    """
    
    def __init__(self, sim_template=None):
        """
        Initialize the parser.
        
        Args:
            node_factory: Factory for creating NodeCFG objects (kept for compatibility)
        """
        self.sim_template = sim_template or {}
        self.node_data = set()  # Parsed node data
        self.modules = []
        
    
    def parse_node(self, node_type: str, config: Union[Dict[str, Any], Any], 
                   context_path: List[str] = None, **kwargs) -> Dict[str, Any]:
        """
        Main entry point for parsing any node type.
        
        Args:
            node_type: Type of node to create ('mesh', 'module', 'pipeline', etc.)
            config: Node configuration (dict or raw value for simple nodes)
            context_path: Current parsing context path (replaces from_node)
            **kwargs: Additional arguments specific to node type
            
        Returns:
            Dict: Node data with validation and dependencies
        """
        if config is None:
            logging.warning(f"Node configuration for {node_type} is None.")
            return None
        
        # Set default context if not provided
        context_path = context_path or [node_type]
        
        # Convert simple values to dict format
        if not isinstance(config, dict):
            config = {'src': config}

       
        # For specific node types, use specialized parsing
        # Each specialized parser handles its own validation and dependency extraction
        if node_type == 'mesh':
            self._parse_mesh(config, context_path)
        elif node_type == 'modules':
            return self._parse_modules(config, context_path, **kwargs)
        else:
            raise ValueError(f'Unsupported node type: {node_type}. Supported types are: mesh, pipeline, modules, input.')

    
    def _parse_modules(self, modules_config: Dict[str, Any], 
                     context_path: List[str] = None):
        if not isinstance(modules_config, dict):
            raise ValueError(f"Modules configuration must be a dictionary, got {type(modules_config)}")
        
        context_path = context_path or ['modules']

        self.modules = set(modules_config.keys())
        
        for module_key, module_cfg in modules_config.items():

            if module_key == 'default_build':
                # Skip default build for now
                continue

            module_context = context_path + [module_key]
            self._parse_module(module_key, module_cfg, module_context)
    
    
    def _parse_module(self, module_key: str, module_config: Dict[str, Any], 
                     context_path: List[str] = None):
        """
        Parse a single module configuration.
        
        Args:
            module_key: Module identifier
            module_config: Module configuration dict
            context_path: Current parsing context path
            
        Returns:
            str: Reference ID of created module node
        """
        context_path = context_path or ['modules', module_key]

        # module key split
        cmd_module_name = module_key.split('-')[0] if '-' in module_key else module_key

        # validate the overall module configuration
        NodeSchemas.validate_config_strict('module', module_config, context_path)

        # data collection
        data_config = module_config.get('data')
        template_config = self.sim_template.get('modules', {}).get(cmd_module_name, {})
        
        # 2. Parse the data nodes ------------------------------------------------
        if data_config:
            # get valid data fields
            data_required_fields = template_config.get('data', [])
            # validate with allowed fields from template
            NodeSchemas.validate_config_strict('module_data', data_config, context_path, required_fields=data_required_fields)
            # add nodes
            data_context = context_path + ['data']
            data_ids = self._parse_input_collection(data_config, data_context)
        else:
            data_ids = {}

        # 3. Parse the template nodes ------------------------------------------------
        # Validate template
        if not template_config:
            raise ValueError(f"Module '{module_key}' is missing a valid 'template' configuration.")
        if cmd_module_name != module_key:
            template_config = self._replace_template_references(template_config, old_ref=cmd_module_name, new_ref=module_key)
        
        # cmd validation
        func_path = template_config.get('func')
        param_data = self._extract_function_parameters(func_path)
        param_names = [i for i in param_data.keys() if i != 'kwargs']

        # Validate command section of user input if present
        if 'cmd' in module_config:
            cmd_config = module_config['cmd']
            
            if func_path:
                # validate user input kwargs
                for key in cmd_config.keys():
                    if key not in param_names:
                        raise ValueError(f"Invalid command argument '{key}' for function '{func_path}'. Valid parameters are: {param_names}")
            else:
                raise ValueError(f"Module '{module_key}' is missing a valid 'func' in its template configuration.")
        
        # get config dict
        input_cmd_config = module_config.get('cmd', {})
        temp_build_dep_config = {
            k:v for k, v in template_config.get('build_dependencies', {}).items() if k not in input_cmd_config
            }
        default_config = {
            k: v['default'] for k, v in param_data.items() if ('default' in v) and (v['default'] is not None) and k not in input_cmd_config and k not in temp_build_dep_config
            }

        # combine dict -> order of importane default_config < template < cmd
        cmd_config = default_config | temp_build_dep_config | input_cmd_config

        # validate cmd schema
        NodeSchemas.validate_config_strict(
            'template_build_dependencies',
            cmd_config,
            context_path,
            optional_fields=param_names)
        
        default_ids = {}
        for k, v in default_config.items():
            k_context = context_path + [k]
            k_node_id = self._parse_value(v, k_context, resolution_mode='literal')
            default_ids[k] = k_node_id
        
        input_cmd_ids = {}
        for k, v in input_cmd_config.items():
            k_context = context_path + [k]
            k_node_id = self._parse_value(v, k_context, resolution_mode='literal')
            input_cmd_ids[k] = k_node_id
        
        tmp_config = {k:v for k, v in temp_build_dep_config.items() if k not in input_cmd_config}
        template_ids = self._parse_input_collection(tmp_config, context_path)

        all_dependencies = set(template_ids.values()) | set(input_cmd_ids.values())

        module_config = {
            'data': data_ids,
            'cmd': {**template_ids, **input_cmd_ids},
        }

        meta = {
            'cmd': module_config.get('cmd'),
            'func_path': func_path,
        }
        
        module_node = NodeData(
            node_type='module',
            config=module_config,
            context_path=context_path,
            dependencies=all_dependencies,
            metadata=meta,
        )

        self._add_to_node_data(module_node)

    def _add_to_node_data(self, node):

        if isinstance(node, list):
            # check if duplicate node in self.node_data
            for n in node:
                if isinstance(n, NodeData) and n not in self.node_data:
                    self.node_data.add(n)
                else:
                    raise ValueError(f"Unsupported node type in list: {type(n)}. Expected NodeData.")
        
        elif isinstance(node, NodeData) and node.id not in self.node_data:
            self.node_data.add(node)
        else:
            raise ValueError(f"Unsupported node type: {type(node)}. Expected dict or list of dicts.")
    
    
    def _replace_template_references(self, template_data, old_ref, new_ref):
        """Replace all node references in template data."""
        import re
        
        def replace_refs(obj):
            if isinstance(obj, str) and obj.startswith('@'):
                # Use regex for precise matching of module references
                pattern = rf'@modules\.{re.escape(old_ref)}.'
                return re.sub(pattern, f'@modules.{new_ref}.', obj)
            elif isinstance(obj, dict):
                return {k: replace_refs(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [replace_refs(item) for item in obj]
            return obj
        
        return replace_refs(template_data)
    
    
    #TODO utils?
    def _extract_function_parameters(self, func_path: str) -> dict:
        """Extract all parameters from a function given its module path."""
        import inspect

        # Import the function dynamically
        module_parts = func_path.split('.')
        module_name = '.'.join(module_parts[:-1])
        func_name = module_parts[-1]
        
        module = __import__(module_name, fromlist=[func_name])
        func = getattr(module, func_name)
        
        # Get function signature
        sig = inspect.signature(func)
        
        # Extract parameter information
        parameters = {}
        for name, param in sig.parameters.items():
            param_info = {
                'name': name,
                'kind': param.kind.name,
                'default': param.default if param.default != inspect.Parameter.empty else None,
                'annotation': param.annotation if param.annotation != inspect.Parameter.empty else None
            }
            parameters[name] = param_info
        
        return parameters


    @staticmethod
    def _replace_module_reference(reference: str, available_modules: List[str]) -> str:
        """
        Replace a module reference with the most similar available module.
        
        Args:
            reference: Original reference like 'modules.tdis.nper'
            available_modules: List of available module names like ['tdis-mytdis', 'dis-mydis']
        
        Returns:
            str: Updated reference like 'modules.tdis-mytdis.nper'
            
        Raises:
            ValueError: If no matches found or multiple similar matches found
        """
        import re
        from difflib import SequenceMatcher
        
        # Extract the module part from the reference
        # 'modules.tdis.nper' -> 'tdis'
        if not reference.startswith('@modules.'):
            raise ValueError(f"Reference must start with '@modules.', got: {reference}")
        
        parts = reference.split('.')
        if len(parts) < 3:
            raise ValueError(f"Reference must have at least 3 parts (modules.module.property), got: {reference}")
        
        original_module = parts[1]  # 'tdis'
        if original_module in available_modules:
            return reference  # No change needed if module is already correct

        
        property_part = '.'.join(parts[2:])  # 'nper' or 'stress_period_data.period_1'
        
        # Find modules that start with the original module name
        base_pattern = f"{original_module}-"
        candidates = [mod for mod in available_modules if mod.startswith(base_pattern)]
        
        if not candidates:
            raise ValueError(f"No modules found matching pattern '{base_pattern}*' in available modules: {available_modules}")
        
        if len(candidates) > 1:
            raise ValueError(f"Multiple modules found matching pattern '{base_pattern}*': {candidates}. Cannot determine which to use.")
        
        # Use the single match
        new_module = candidates[0]
        new_reference = f"@modules.{new_module}.{property_part}"
        
        return new_reference
    
    
    
    def _parse_mesh(self, mesh_config: Dict[str, Any], 
                context_path: List[str] = None):
        """
        Parse mesh configuration with schema validation.
        """
        from .node_schemas import NodeSchemas  # Import at top of file
        
        context_path = context_path or ['mesh']
        
        # First validate the overall mesh configuration
        NodeSchemas.validate_config_strict('mesh', mesh_config, context_path)
        
        
        # 1. Prepping ------------------------------------------------
        # Define what constitutes mesh config vs mesh data
        config_keys = {'crs', 'nrow', 'ncol', 'nlay', 'resolution', 'delr', 'delc', 'xorigin', 'yorigin', 'domain'}
        data_keys = {'active_domain', 'top', 'bottoms'}
        
        # Separate config from data
        mesh_cfg = {k: v for k, v in mesh_config.items() if k in config_keys}
        mesh_data = {k: v for k, v in mesh_config.items() if k in data_keys}
        
        # 2. Parse the mesh nodes ------------------------------------------------      
        mesh_cfg_node_ids = {}
        for k, v in mesh_cfg.items():
            k_context = context_path + [k]
            k_node_id = self._parse_value(v, k_context, resolution_mode='literal')
            mesh_cfg_node_ids[k] = k_node_id
        

        cfg_meta = {
            'mesh_type': mesh_config.get('mesh_type')
        }
        
        mesh_cfg_node = NodeData(
            node_type='mesh_config',
            config=mesh_cfg_node_ids,
            context_path=context_path + ['config'],
            dependencies=mesh_cfg_node_ids.values(),
            metadata=cfg_meta,
        )

        self._add_to_node_data(mesh_cfg_node)
        
        # 3. Parse the data nodes ------------------------------------------------
        mesh_data_node_ids = self._parse_input_collection(mesh_data, context_path)
        
        mesh_data_node = NodeData(
            node_type='mesh_data',
            config=mesh_data_node_ids,
            context_path=context_path + ['data'],
            dependencies=mesh_data_node_ids.values(),
        )

        self._add_to_node_data(mesh_data_node)
        
        # 4. Combine  ------------------------------------------------
        # Create composite mesh node that references both config and data
        # main_meta = {
        #     'config_keys': list(mesh_cfg.keys()),
        #     'data_keys': list(mesh_data.keys())
        # }

        # main_mesh_node = NodeData(
        #     node_type='mesh',
        #     config=mesh_config,
        #     context_path=context_path,
        #     dependencies=set([mesh_cfg_node.id, mesh_data_node.id]),
        #     metadata=main_meta,
        # )

        # self._add_to_node_data(main_mesh_node)
        

    def _is_node_type(self, node_type: str, value: Any) -> bool:
        """Check if a value represents an input node using schema validation."""
        is_valid, _ = NodeSchemas.validate_config(node_type, value)
        return is_valid
    

    def _parse_input_collection(self, data: Dict[str, Any], 
                              context_path: List[str]) -> List[Dict[str, Any]]:
        # Parse mesh data arrays (each can be Input or Pipeline)
        node_ids = {}
        
        for d_key, d_value in data.items():
            d_context = context_path + [d_key]

            # get type of node
            if isinstance(d_value, dict) and 'levels' in d_value.keys() and 'input' in d_value.keys():              
                # parse levels
                node_id = self._parse_levels(d_value, d_context)
            elif isinstance(d_value, dict) and ('pipeline' in d_value or 'builtin' in d_value) and 'input' in d_value:
                node_id = self._parse_pipeline(d_value, d_context)
            else:
                # dict as input value
                node_id = self._parse_value(d_value, d_context)
            
            if node_id:
                node_ids[d_key] = node_id
        
        return node_ids
    
    
    def _parse_levels(self, config: Any, context_path: List[str]):
        # reorganize into pipeline dict and send back to input_data_collection
        levels_config = config.copy().pop('levels')
        
        # already validated
        level_input = levels_config.get('input')
        hier_input = {f'level{i+1}': input for i, input in enumerate(level_input)}
        pipeline = [
            {'processor': 'hierarchical_levels',
             **hier_input
             }
        ]
        
        if 'pipeline' in levels_config:
            # merge with existing pipeline
            pipeline.extend(levels_config['pipeline'])

        # reconfigure
        pipeline_config = {
            **config,
            'pipeline': pipeline
        }

        return self._parse_pipeline(
            pipeline_config, 
            context_path, 
        )
        
    
    def _parse_value(self, config: Any,
                     context_path: List[str],
                     resolution_mode='auto',
                     use_mesh_build_context=True):
        
        if resolution_mode not in ['auto', 'literal']:
            raise ValueError(f"Invalid resolution_mode '{resolution_mode}'. Expected 'auto' or 'literal'.")
        
        # Handle different input formats
        if isinstance(config, dict):
            input_config = config.copy()
            if 'input' in input_config:
                if 'src' in input_config['input']:
                    value = input_config['input']['src']
                else:
                    value = input_config.get('input', {})
                load_options = input_config if input_config else None
            elif 'src' in input_config:
                # Format: {src: "file.txt"} or just {key: value}
                value = input_config.pop('src')
                resolution_mode = input_config.pop('resolution_mode', resolution_mode)
                use_mesh_build_context = input_config.pop('use_mesh_build_context', use_mesh_build_context)
                load_options = input_config if input_config else {}
            else:                # Assume it's a simple dict value
                value = input_config
                load_options = {}
        else:
            # Simple value
            value = config
            load_options={}
        
        if isinstance(value, str) and value.startswith('@'):
            return value[1:]
            # input_node = self.node_data.get(value[1:])
            # input_node.context_path = context_path  # Update context path

        meta = {
            'value': value,
            'resolution_mode': resolution_mode,
            'load_options': load_options,
            'use_mesh_build_context': use_mesh_build_context,
        }

        input_node = NodeData(
            node_type='input',
            config=config,
            context_path=context_path,
            metadata=meta,
        )

        self._add_to_node_data(input_node)
        
        return input_node.id

    
    def _parse_pipe(self, config: Any, context_path: List[str], built_in=False):
        from ...registries import BUILTIN_PROCESSORS
        resolved_builtin_dependencies = {}
        context_required = False
        
        pipe_config = config.copy()
        # Handle different input formats
        if isinstance(pipe_config, dict):
            pipe_input = pipe_config.pop('input', None) # this is a node_id
            processor = pipe_config.pop('processor')
        else:
            raise ValueError(f"Invalid pipe configuration: {pipe_config}. Expected dict format.")
        
        # check if processor is in the built-in registry
        if built_in:
            if processor not in BUILTIN_PROCESSORS:
                raise ValueError(f"Processor '{processor}' is not registered in the built-in processors registry. Available processors: {list(BUILTIN_PROCESSORS.keys())}")
        if processor in BUILTIN_PROCESSORS:
            # get built-in dependencies
            built_in_depargs = BUILTIN_PROCESSORS[processor].get('dependency_args', {})
            context_required = BUILTIN_PROCESSORS[processor].get('context_required', False)
            resolved_builtin_dependencies = {}
            for k, v in built_in_depargs.items():
                if isinstance(v, str) and v.startswith('@modules.'):
                    new_v = self._replace_module_reference(v, self.modules)
                    resolved_builtin_dependencies[k] = new_v[1:]
                else:
                    resolved_builtin_dependencies[k] = v[1:]
        
        # parse args
        node_ids = []
        for key, value in pipe_config.items():
            if isinstance(value, str) and value.startswith('@modules.'):
                value = self._replace_module_reference(value, self.modules)
            node_id = self._parse_value(value, context_path + [key], use_mesh_build_context=False)
            node_ids.append(node_id)
            pipe_config[key] = node_id
        
        dependencies = [pipe_input] + list(pipe_config.values()) + list(resolved_builtin_dependencies.values())
        
        context = {'context_path': context_path} if context_required else {}
        
        meta = {
            'processor': processor,
            'input': pipe_input,
            'processor_args': {
                **resolved_builtin_dependencies, 
                **pipe_config,
                **context,
            }
        }
        
        node = NodeData(
            node_type='pipe',
            config=config,
            context_path=context_path,
            dependencies=dependencies,
            metadata=meta,
        )

        self._add_to_node_data(node)
        
        return node.id

    
    def _parse_pipeline(
        self, 
        config: Dict[str, Any], 
        context_path: List[str], 
        ):
        pipeline_config = config.copy()
        # Handle different pipeline formats
        pipelines = []
        built_in = False
        if 'builtin' in pipeline_config:
            built_in = True
            pipes = []
            for processor_kwargs in pipeline_config['builtin']:
                if isinstance(processor_kwargs, str):
                    pipe = {
                        'processor': processor_kwargs
                    }
                
                elif isinstance(processor_kwargs, dict):
                    processor = list(processor_kwargs.keys())[0]
                    kwargs = processor_kwargs[processor]
                    pipe = {
                        'processor': processor
                    }
                    pipe.update(kwargs)
                
                else:
                    raise ValueError(f'Builtin pipeline in the wrong format. Expect either processor as type(str) or processor: kwargs as type(dict).')
                
                pipelines.append(pipe)
        
        if 'pipeline' in pipeline_config:
            pipes = pipeline_config.get('pipeline')
            pipelines.extend(pipes)
        
        input_part = pipeline_config.get('input')
        if input_part:
            input_context = context_path + ['input']
            input_node_id = self._parse_value(input_part, input_context)
        
        # Extract dependencies from pipeline steps
        pipe_ids = []
        for i, pipe in enumerate(pipelines):
            pipe['input'] = input_node_id
            pipe_context = context_path + [f'pipe{i}']
            pipe_node_id = self._parse_pipe(pipe, pipe_context, built_in=built_in)
            input_node_id = pipe_node_id # replace with pipe output for next step
            pipe_ids.append(pipe_node_id)
        
        meta = {
            'output': pipe_ids[-1],
        }

        pipeline_node = NodeData(
            node_type='pipeline',
            config=config,
            context_path=context_path,
            dependencies=pipe_ids,
            metadata=meta
        )

        self._add_to_node_data(pipeline_node)
        
        return pipeline_node.id


    def get_all_nodes(self) -> List[Dict[str, Any]]:
        """Get all parsed node data (data mode only)."""
        return self.node_data.copy()
    
    def clear_all_node_data(self):
        """Clear all parsed node data."""
        self.node_data.clear()