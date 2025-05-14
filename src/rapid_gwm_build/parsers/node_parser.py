from copy import deepcopy
from rapid_gwm_build.nodes.node_cfg import NodeBuilder

class NodeParser:
    """
    A class to parse node data from a given string.
    """

    def __init__(self):
        self.nodes = []
        self.node_builder = NodeBuilder()

    #     self._setup_node_types()

    
    # def _setup_node_types(self):
    #     types = ['module', 'input', 'pipe', 'mesh']
    #     for node_type in types:
    #         ref_id[node_type] = {}
    

    def parse_node(self, node_type, node_cfg):
        """
        Factory method to create a parser for the given node type.
        """
        if node_cfg is None:
            print(f"Node configuration for {node_type} is None.")
            return None

        if node_type == 'modules':
            return self.parse_modules(node_cfg)
        elif node_type == 'input':
            return self.parse_input(node_cfg)
        elif node_type == 'pipe':
            return self.parse_pipe(node_cfg)
        elif node_type == 'mesh':
            return self.parse_mesh(node_cfg)
        else:
            raise ValueError(f"Unknown node type: {node_type}")
    
    def parse_src(self, ncfg, src_cfg):
        updated_refs = {}
        for attr, src_val in src_cfg.items():
            src_ncfg = self.node_builder.create(node_type='input', ncfg=ncfg, attr='src')
            ref_id = self.parse_input(ncfg=src_ncfg, attr=attr, src=src_val, src_arg=False)
            updated_refs[attr] = ref_id
        return updated_refs

    def parse_modules(self, modules_cfg):
        if isinstance(modules_cfg, dict):
            for module_key, module_cfg in modules_cfg.items():
                ncfg = self.node_builder.create(node_type='module', module_key=module_key)
                
                module_refs = {}
                for k, v in module_cfg.items():
                    if k == 'src':
                        new_cfg = self.parse_src(ncfg, v)
                        module_refs.update(new_cfg)
                    else:
                        ref_id = self.parse_input(ncfg=ncfg, attr=k, src=v)
                        module_refs[k] = ref_id

                ncfg.src = module_refs

                self.nodes.append(ncfg)
        else:
            raise NotImplementedError(f"Unsupported module configuration type: {type(modules_cfg)}") #TODO: not implemented yet

    
    def parse_input(self, ncfg, attr, src, src_arg=True):
        new_ncfg = self.node_builder.create(node_type='input', ncfg=ncfg, attr=attr, src_arg=src_arg)
        
        if isinstance(src, dict) and src.get('pipeline'):
            ref_id = self.parse_pipeline(ncfg=new_ncfg, src=src['pipeline'])
        else:
            new_ncfg.src = src
            self.nodes.append(new_ncfg)
            ref_id = new_ncfg.ref_id
        
        return ref_id
            

    def parse_pipeline(self, ncfg, src):
        src_input = src.pop('input')
        in_refid = self.parse_input(ncfg, attr=['pipeline', 'input'], src=src_input, src_arg=False)

        pipeline_ncfg = self.node_builder.create(node_type='pipeline', ncfg=ncfg)
        pipes = []
        for pipe_src in src.get('pipes'):
            ref_id = self.parse_pipes(pipeline_ncfg, pipe_src, pipe_input=in_refid)
            pipes.append(ref_id)
            in_refid = ref_id # update the input reference for the next pipe
        
        pipeline_ncfg.src = src
        pipeline_ncfg.pipes = pipes

        self.nodes.append(pipeline_ncfg)
        return pipeline_ncfg.ref_id


    def parse_pipes(self, ncfg, src, pipe_input):
        # create a pipe_ncfg
        processor = src.pop('processor')
        pipe_ncfg = self.node_builder.create(node_type='pipe', ncfg=ncfg, attr=processor, input=pipe_input)
        
        new_src = {}
        for attr, src_val in src.items():
            ref_id = self.parse_input(ncfg=pipe_ncfg, attr=attr, src=src_val, src_arg=False)
            new_src[attr] = ref_id

        pipe_ncfg.src = new_src

        self.nodes.append(pipe_ncfg)
        return pipe_ncfg.ref_id
    
    
    def parse_pipe_input(self, ncfg, src_cfg):
        updated_refs = {}
        for attr, src_val in src_cfg.items():
            src_ncfg = self.node_builder.create(node_type='input', ncfg=ncfg, attr='src')
            ref_id = self.parse_input(ncfg=src_ncfg, attr=attr, src=src_val)
            updated_refs[attr] = ref_id
        return updated_refs
    
    
    
    def parse_mesh(self, mesh_cfg):
        # for key, cfg in mesh_cfg.items():


        mesh_cfg = sim_cfg.get(section, {})
        if mesh_cfg:
            mesh_cfg, nodes = cls.parse_input(nodes, section, mesh_cfg)
            nodes['mesh'].update(mesh_cfg)
        return nodes
    