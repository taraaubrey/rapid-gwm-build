from copy import deepcopy
from rapid_gwm_build.nodes.node_cfg import NodeFactory

class NodeParser:
    """
    A class to parse node data from a given string.
    """

    def __init__(self):
        self.nodes = []
        self.factory = NodeFactory()

        self.parsers = {
            'input': self.parse_input,
            'pipe': self.parse_pipe,
            'pipeline': self.parse_pipeline,
            'mesh': self.parse_mesh,
            'modules': self.parse_modules,
            'src': self.parse_src,
        }
    
    def get_parser(self, key):
        """
        Returns the parser function for the given key.
        """
        return self.parsers.get(key, None)
        

    #     self._setup_node_types()

    
    # def _setup_node_types(self):
    #     types = ['module', 'input', 'pipe', 'mesh']
    #     for node_type in types:
    #         ref_id[node_type] = {}
    

    def parse_node(self, node_type, **node_cfg):
        """
        Factory method to create a parser for the given node type.
        """
        if node_cfg is None:
            print(f"Node configuration for {node_type} is None.")
            return None

        if node_type == 'modules':
            return self.parse_modules(node_cfg)
        # elif node_type == 'input':
        #     return self.parse_input(node_cfg, from_node=from_node, **kwargs)
        elif node_type == 'pipeline':
            return self.parse_pipeline(**node_cfg)
        elif node_type == 'pipe':
            return self.parse_pipe(**node_cfg)
        elif node_type == 'mesh':
            return self.parse_mesh(**node_cfg)
        elif node_type == 'src':
            return self.parse_src(**node_cfg)
        else:
            return self.parse_input(**node_cfg)
    
    def parse_src(self, from_node=None, **node_cfg):
        updated_refs = {}
        for attr, src_val in node_cfg.items():
            cfg = {
                'attr': ['src', attr],
                'src': src_val,
                'src_arg': True,
                'from_node': from_node,
            }
            ref_id = self.parse_node(attr, **cfg)
            # src_node = self.factory.build_node(node_type='input', from_node=from_node, attr='src')
            # ref_id = self.parse_node('input', src_val, from_node=src_node, attr=attr, src=src_val, src_arg=False)
            # # ref_id = self.parse_input(from_node=src_node, attr=attr, src=src_val, src_arg=False)
            updated_refs[attr] = ref_id
        return updated_refs

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
        node = self.factory.build_node(node_type='module', module_key=module_key)
        
        module_refs = {}
        for k, k_cfg in node_cfg.items():
            parser = self.get_parser(k)
            if isinstance(k_cfg, dict) and parser:
                refs = parser(from_node=node, **k_cfg)
            else:
                parser = self.get_parser('input')
                refs = parser(from_node=node, src=k_cfg)
            module_refs[k] = refs

        node.src = module_refs

        self.nodes.append(node)
        
    
    def parse_input(self, src=None, src_arg=True, **cfg):
        node = self.factory.build_node(node_type='input', src_arg=src_arg, src=src, **cfg)
        
        if src_arg and isinstance(src, dict):
            for k, v in src.items():
                cfg = {
                    'attr': k,
                    'src': v,
                    'param': v, #TODO might not need this?
                    'from_node': node,
                    'src_args': True
                }
                ref_id = self.parse_node(k, **cfg)
                node.src = ref_id
        self.nodes.append(node)

        return node.ref_id
            

    def parse_pipeline(self, src=None, from_node=None, **ncfg):
        src_input = src.pop('input')
        in_cfg = {
            'attr': ['pipeline', 'input'],
            'src': src_input,
            'src_arg': True,
            'from_node': from_node,
        }
        in_ref_id = self.parse_node('input', **in_cfg)
        # in_refid = self.parse_input(ncfg, attr=['pipeline', 'input'], src=src_input, src_arg=False)
        cfg = {
            'attr': 'pipeline',
            'src': src,
            'src_arg': True,
            'from_node': from_node,
        }
        pipeline_node = self.factory.build_node(node_type='pipeline', **cfg)
        pipes = []
        for pipe_src in src.get('pipes'):
            ref_id = self.parse_node('pipe', from_node=pipeline_node, input_id=in_ref_id, **pipe_src)
            
            in_ref_id = ref_id # update the input reference for the next pipe
            pipes.append(ref_id) # update the input reference for the next pipe
        
        pipeline_node.src = src
        pipeline_node.pipes = pipes

        self.nodes.append(pipeline_node)
        return pipeline_node.ref_id


    def parse_pipe(self, processor:str=None, from_node=None, input_id=None, src={}, **cfg):
        pipe_ncfg = self.factory.build_node(node_type='pipe', from_node=from_node, attr=processor, input_id=input_id, src=cfg)
        
        new_src = {}
        for attr, src_val in cfg.items():
            ref_id = self.parse_node(node_type=attr, from_node=pipe_ncfg, attr=attr, src=src_val, src_arg=True)
            # ref_id = self.parse_input(ncfg=pipe_ncfg, attr=attr, src=src_val, src_arg=True)
            new_src[attr] = ref_id

        pipe_ncfg.src = new_src

        self.nodes.append(pipe_ncfg)
        return pipe_ncfg.ref_id
    
    
    # def parse_pipe_input(self, ncfg, src_cfg):
    #     updated_refs = {}
    #     for attr, src_val in src_cfg.items():
    #         src_ncfg = self.factory.build_node(node_type='input', ncfg=ncfg, attr='src')
    #         ref_id = self.parse_input(ncfg=src_ncfg, attr=attr, src=src_val)
    #         updated_refs[attr] = ref_id
    #     return updated_refs
    
    
    
    def parse_mesh(self, **node_cfg):
        mesh_ncfg = self.factory.build_node(node_type='mesh')
        updated_refs = {}
        for k, v in node_cfg.items():
                cfg = {
                    'attr': ['mesh', k],
                    'src': v,
                    'param': v,
                    'from_node': mesh_ncfg,
                    'src_args': True
                }
                ref_id = self.parse_node(k, **cfg)
                updated_refs[k] = ref_id
        mesh_ncfg.src = updated_refs
        self.nodes.append(mesh_ncfg)

        # mesh_cfg = sim_cfg.get(section, {})
        # if mesh_cfg:
        #     mesh_cfg, nodes = cls.parse_input(nodes, section, mesh_cfg)
        #     nodes['mesh'].update(mesh_cfg)
        # return nodes
    