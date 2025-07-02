"""
Comparison: Before and After removing from_node dependency

NOTE: This is an illustrative comparison file showing code patterns.
Some variables like mesh_config are placeholders for the examples.
This file is not meant to be executed directly.
"""

from rapid_gwm_build.parsers.node_parser import NodeParser
from rapid_gwm_build.nodes.node_cfg import NodeFactory

# ==========================================
# BEFORE: Complex from_node approach
# ==========================================

def old_parse_module(self, module_key, module_config, from_node=None, attr=None):
    """Complex approach with from_node dependency"""
    
    # Create the module node - needs from_node for attribute building
    node = self.node_factory.build_node(
        node_type='module', 
        module_key=module_key,
        from_node=from_node,  # ← Complex dependency
        attr=attr or [module_key]
    )
    
    # Parse recursively - needs to pass from_node through
    updated_src = self.parse_dict(
        cfg_dict=module_config, 
        from_node=node,  # ← Passing node as context
        src_arg=True, 
        attr=[module_key]
    )
    node.src = updated_src
    
    return node.ref_id

def old_parse_dict(self, cfg_dict, from_node=None, src_arg=False, attr=None):
    """Complex recursive parsing with from_node dependency"""
    
    for k, v in cfg_dict.items():
        # Complex attribute building from parent
        if attr is not None:
            in_attr = attr + [k] if isinstance(attr, list) else [attr, k]
        else:
            in_attr = [k]
        
        # Context-dependent parsing - messy conditional logic
        if k in ['top', 'bottoms'] and from_node.type == 'mesh':  # ← Tight coupling
            mesh_ncfg = NodeFactory.build_node(
                node_type='mesh', 
                attr=in_attr, 
                from_node=from_node,  # ← More coupling
                src=v, 
                param=k
            )
            # ... more complex logic
        else:
            # ... even more conditionals based on from_node


# ==========================================
# AFTER: Clean context-path approach
# ==========================================

def new_parse_module(self, module_key, module_config, context_path=None):
    """Simplified approach with explicit context paths"""
    
    context_path = context_path or ['modules', module_key]
    
    # Clean node creation - no mysterious dependencies
    node = self.node_factory.build_node(
        node_type='module',
        module_key=module_key,
        attr=context_path  # ← Explicit, clear context
    )
    
    # Clean recursive parsing
    updated_src = self.parse_dict(
        cfg_dict=module_config,
        context_path=context_path,  # ← Clear context passing
        src_arg=True
    )
    node.src = updated_src
    
    return node.ref_id

def new_parse_dict(self, cfg_dict, context_path=None, src_arg=False):
    """Clean recursive parsing with explicit context"""
    
    context_path = context_path or []
    
    for k, v in cfg_dict.items():
        # Simple, predictable context building
        item_context = context_path + [k]
        
        # Clean value parsing with explicit context
        ref_id = self._parse_value(
            key=k,
            value=v,
            context_path=item_context,  # ← Clear context
            src_arg=src_arg
        )

def new_parse_value(self, key, value, context_path, src_arg=False):
    """Clean value parsing with explicit context checks"""
    
    # Simple, testable context checking
    if self._is_mesh_context(context_path) and key in ['top', 'bottoms']:
        return self._parse_mesh_component(key, value, context_path)
    
    # No mysterious from_node dependencies!

def _is_mesh_context(self, context_path):
    """Simple, testable context checking"""
    return len(context_path) > 0 and context_path[0] == 'mesh'


# ==========================================
# BENEFITS OF REMOVING from_node
# ==========================================

"""
✅ SIMPLICITY
- No complex from_node parameter threading
- Explicit context paths instead of implicit relationships
- Easier to understand and debug

✅ TESTABILITY  
- Each method can be tested independently
- Context paths are explicit and predictable
- No hidden state in from_node objects

✅ MAINTAINABILITY
- Cleaner method signatures
- Less coupling between parser methods
- Easier to add new node types

✅ FLEXIBILITY
- Context paths can be built programmatically
- No need to create dummy nodes for context
- Easier to implement different parsing strategies

✅ PERFORMANCE
- No need to create intermediate nodes for context
- Less object creation and memory usage
- Simpler call stacks

✅ CLARITY
- What you see is what you get
- No magic attribute inheritance
- Explicit rather than implicit relationships
"""


# ==========================================
# USAGE COMPARISON
# ==========================================

# Example configuration for illustrations
mesh_config = {'type': 'mesh', 'file': 'mesh.txt'}

# OLD WAY - Complex
def old_usage():
    parser = NodeParser(NodeFactory)  # ← Need to pass factory
    
    # Complex parsing with mysterious from_node handling
    mesh_ref = parser.parse_node('mesh', mesh_config)
    # Internal complexity hidden in from_node parameter passing


# NEW WAY - Simple  
def new_usage():
    parser = NodeParser()  # ← No factory needed
    
    # Clean, explicit parsing
    mesh_ref = parser.parse_node('mesh', mesh_config, context_path=['mesh'])
    # Clear what's happening, easy to debug and test
