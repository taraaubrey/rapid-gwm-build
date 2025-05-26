import logging
from copy import deepcopy
from rapid_gwm_build.nodes.node_cfg import NodeFactory

class NodeParser:
    """
    A class to parse node data from a given string.
    """

    def __init__(self):
        self.nodes = []
        # NodeFactory = NodeFactory()

        self.parsers = {
            'input': self.parse_input,
            'pipe': self.parse_pipe,
            'pipeline': self.parse_pipeline,
            'mesh': self.parse_mesh,
            'modules': self.parse_modules,
            'src': self.parse_dict,
        }

    
    def get_parser(self, k):
        """
        Returns the parser function for the given key.
        """
        parser = self.parsers.get(k)
        if not parser:
            parser = self.parsers.get('input')
        return parser
    

    def parse_node(self, node_type, **node_cfg):
        """
        Factory method to create a parser for the given node type.
        """
        if node_cfg is None:
            print(f"Node configuration for {node_type} is None.")
            return None

        if node_type == 'modules':
            return self.parse_modules(node_cfg)
        elif node_type == 'mesh':
            return self.parse_mesh(**node_cfg)
        elif node_type == 'pipes':
            return self.parse_pipes(**node_cfg)
        else:
            logging.warning(f"Unsupported node type: {node_type}")
            pass
            # raise NotImplementedError(f"Unsupported node type: {node_type}") #TODO: not implemented yet
    
    # def parse_src(self, from_node=None, src=None, **kwargs):
    #     updated_src = self.parse_dict(self, cfg_dict=node_cfg, from_node=from_node, src_arg=True)
    #     updated_refs = {}
    #     for attr, src_val in src.items():
    #         if isinstance(src_val, dict) and 'pipeline' in src_val:
    #             pipeline_src = src_val.get('pipeline')
    #             ref_id = self.parse_pipeline(attr=attr, src=pipeline_src, from_node=from_node)
    #         else:
    #             parser = self.get_parser(attr, src_val)
    #             ref_id = parser(attr=['src', attr], src=src_val, from_node=from_node)
    #         # ref_id = self.parse_node(attr, attr=['src', attr], src=src_val, from_node=from_node, src_arg=True)
    #         updated_refs[attr] = ref_id
    #     return updated_refs

    
    def parse_modules(self, modules_cfg:dict):
        if isinstance(modules_cfg, dict):
            for module_key, module_cfg in modules_cfg.items():
                self.parse_module(module_key, **module_cfg)
        else:
            raise NotImplementedError(f"Unsupported module configuration type: {type(modules_cfg)}") #TODO: not implemented yet

    def parse_module(self, module_key, **node_cfg):
        """
        Factory method to create a parser for the given module type.
        """
        node = NodeFactory.build_node(node_type='module', module_key=module_key)
        updated_src = self.parse_dict(cfg_dict=node_cfg, from_node=node, src_arg=True)
        # module_refs = {}
        # for k, k_cfg in node_cfg.items():
        #     parser = self.get_parser(k, k_cfg)
        #     ref_id = parser(attr=k, from_node=node, src=k_cfg, src_arg=True)
        #     module_refs[k] = ref_id

        node.src = updated_src

        self.nodes.append(node)


    def parse_template(self, module_key, attr, cfg):
        node = NodeFactory.build_node(node_type='template', module_key=module_key, attr=[attr])

        updated_src = self.parse_dict(cfg_dict=cfg, from_node=node, src_arg=False)
        # template_refs = {}
        # for k, k_cfg in cfg.items():
        #     parser = self.get_parser(k, k_cfg)
        #     ref_id = parser(src=k_cfg, from_node=node, attr=['template'], src_arg=False)
        #     template_refs[k] = ref_id

        node.src = updated_src

        self.nodes.append(node)

        return node
    
    def parse_input(self, src=None, src_arg=False, from_node=None, attr=None):
        node = NodeFactory.build_node(node_type='input', src_arg=src_arg, src=src, from_node=from_node, attr=attr)
        
        if not src_arg and isinstance(src, dict):
            updated_src = self.parse_dict(cfg_dict=src, from_node=node, src_arg=src_arg)
            # for k, v in src.items():
            #     parser = self.get_parser(k, v)
            #     ref_id = parser(attr=k, src=v, from_node=node, src_arg=src_arg)
            #     # ref_id = self.parse_node(k, attr=k, src=v, from_node=node, src_args=True)
            node.src = updated_src
        self.nodes.append(node)

        return node.ref_id
            

    def parse_pipeline(self, src=None, from_node=None, attr=None, **ncfg):
        in_attr = ['pipeline', 'input']
        if isinstance(attr, list):
            in_attr.extend(attr)
            
        if 'input' in src:
            src_input = src.pop('input')
            in_ref_id = self.parse_input(
                src=src_input, attr=in_attr, from_node=from_node, src_arg=False)
        else:
            in_ref_id = None
        
        pipeline_node = NodeFactory.build_node(
            node_type='pipeline', src=src, from_node=from_node, src_arg=True, attr=attr)

        pipes = []
        for pipe_cfg in src.get('pipes'):
            processor = pipe_cfg.pop('processor')
            ref_id = self.parse_pipe(
                from_node=pipeline_node, input_id=in_ref_id, processor=processor, src=pipe_cfg)
            in_ref_id = ref_id # update the input reference for the next pipe
            pipes.append(ref_id) # update the input reference for the next pipe
        
        pipeline_node.src = src
        pipeline_node.pipes = pipes
        self.nodes.append(pipeline_node)
        return pipeline_node.ref_id


    def parse_pipe(self, processor:str=None, from_node=None, input_id=None, src=None, attr=None):
        if len(processor.split('.')) > 1:
            # If the processor is a module, we need to parse it differently
            module_path = processor
            processor = processor.split('.')[-1]
        else:
            module_path = None
        
        if attr:
            pipe_attr = [processor, attr]
        else:
            pipe_attr = processor
        
        pipe_ncfg = NodeFactory.build_node(node_type='pipe', from_node=from_node, attr=pipe_attr, input_id=input_id, src=src, module_path=module_path)
        updated_src = self.parse_dict(cfg_dict=src, from_node=pipe_ncfg, src_arg=False)
        pipe_ncfg.src = updated_src
        self.nodes.append(pipe_ncfg)
        
        return pipe_ncfg.ref_id
    
    
    def parse_mesh(self, **node_cfg):
        mesh_ncfg = NodeFactory.build_node(node_type='mesh')
        updated_src = self.parse_dict(cfg_dict=node_cfg, from_node=mesh_ncfg, src_arg=False)
        # updated_refs = {}
        # for k, v in node_cfg.items():
        #         if isinstance(v, str) and v.startswith('@'):
        #             # If the value is a reference, we need to parse it differently
        #             ref_id = v
        #         parser = self.get_parser(k)
        #         ref_id = parser(
        #             attr=['mesh', k], src=v, from_node=mesh_ncfg, src_arg=False)
        #         updated_refs[k] = ref_id
        mesh_ncfg.src = updated_src
        self.nodes.append(mesh_ncfg)


    def parse_dict(self, cfg_dict, from_node=None, src_arg=False):
        updated_refs = {}
        for k, v in cfg_dict.items():
            
            if isinstance(v, str) and v.startswith('@'):
                ref_id = v
            elif isinstance(v, dict) and 'pipeline' in v:
                pipeline_src = v.get('pipeline')
                ref_id = self.parse_pipeline(attr=k, src=pipeline_src, from_node=from_node)
            else:
                parser = self.get_parser(k)
                if isinstance(v, dict) and 'src' in v:
                    src_val = v.get('src')
                    ref_id = parser(attr=['src', k], src=src_val, from_node=from_node, src_arg=src_arg)
                elif from_node.type == 'template':
                    ref_id = parser(attr=['template', k], src=v, from_node=from_node, src_arg=src_arg)
                elif from_node.type == 'mesh':
                    ref_id = parser(attr=['mesh', k], src=v, from_node=from_node, src_arg=src_arg)
                else:
                    ref_id = parser(attr=k, src=v, from_node=from_node, src_arg=src_arg)
            
            updated_refs[k] = ref_id
        return updated_refs
