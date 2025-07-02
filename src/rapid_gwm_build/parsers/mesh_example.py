"""
Example usage of the new mesh parser with data mode.
Shows how mesh config and mesh data are separated and how Input/Pipeline nodes are extracted.
"""

from rapid_gwm_build.parsers.node_parser import NodeParser
import json

def test_mesh_parsing():
    """Test the mesh parser with a realistic configuration."""
    
    # Example mesh configuration from your YAML
    mesh_config = {
        # Mesh Config (metadata - no dependencies)
        'crs': 2193,
        'nlay': 6,
        'resolution': 25,
        
        # Mesh Data (arrays - can have Input/Pipeline nodes)
        'active_domain': {
            'input': 'active_domain.shp',
            'pipeline': [
                {
                    'processor': 'pkpk_functions.make_bottom_inactive',
                    'bottoms': '@mesh.bottoms',
                    'inactive_dims': [-2, -1]
                }
            ]
        },
        'top': {
            'input': 'C:/data/dem_clipped.tif'
        },
        'bottoms': {
            'input': 'examples/pakipaki01/models/derived_data/basement_z.tif',
            'pipeline': [
                {
                    'processor': 'utils.make_layers',
                    'confined_elev': -10,
                    'gravel_elev': -20,
                    'min_thickness': 1,
                    'top': '@mesh.top'
                }
            ]
        }
    }
    
    # Initialize parser in data mode
    parser = NodeParser(mode='data')
    
    # Parse the mesh
    mesh_node = parser.parse_mesh(mesh_config, ['mesh'])
    
    # Get all parsed node data
    all_nodes = parser.get_all_node_data()
    
    print("=== MESH PARSING RESULTS ===")
    print(f"Total nodes created: {len(all_nodes)}")
    print()
    
    # Show the structure
    for node in all_nodes:
        print(f"Node ID: {node['id']}")
        print(f"Type: {node['type']}")
        print(f"Dependencies: {node['dependencies']}")
        print(f"Context Path: {node['context_path']}")
        
        # Show type-specific info
        if node['type'] == 'mesh_config':
            print(f"Config keys: {list(node['config'].keys())}")
        elif node['type'] == 'mesh_data':
            print(f"Array keys: {node['parser_metadata']['array_keys']}")
        elif node['type'] == 'input':
            print(f"Array type: {node['parser_metadata'].get('array_type', 'unknown')}")
            print(f"Source: {node['parser_metadata'].get('src', 'unknown')}")
        elif node['type'] == 'pipeline':
            print(f"Array type: {node['parser_metadata'].get('array_type', 'unknown')}")
            print(f"Processors: {node['parser_metadata'].get('processors', [])}")
            print(f"Pipeline steps: {node['parser_metadata'].get('pipeline_steps', 0)}")
        
        print("-" * 50)
    
    # Show dependency graph
    dep_graph = parser.get_dependencies_graph()
    print("\n=== DEPENDENCY GRAPH ===")
    for node_id, deps in dep_graph.items():
        if deps:
            print(f"{node_id} depends on: {deps}")
    
    return all_nodes

def show_mesh_structure():
    """Show the structure that gets created."""
    print("=== MESH NODE STRUCTURE ===")
    print("""
    mesh (composite)
    ├── mesh.config (metadata only, no deps)
    │   ├── crs: 2193
    │   ├── nlay: 6
    │   └── resolution: 25
    │
    └── mesh.data (references to arrays)
        ├── mesh.active_domain (pipeline node)
        │   ├── mesh.active_domain.input (input node)
        │   └── pipeline with processor: make_bottom_inactive
        │       └── depends on: @mesh.bottoms
        │
        ├── mesh.top (input node)
        │   └── input: dem_clipped.tif
        │
        └── mesh.bottoms (pipeline node)
            ├── mesh.bottoms.input (input node)
            └── pipeline with processor: make_layers
                └── depends on: @mesh.top
    """)

if __name__ == "__main__":
    show_mesh_structure()
    print()
    test_mesh_parsing()
