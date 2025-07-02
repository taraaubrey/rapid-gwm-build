"""
Example usage of the refactored node parser system.
Shows how to parse different types of configurations and handle dependencies.
"""

from rapid_gwm_build.parsers.legacy.node_parser import NodeParser
from rapid_gwm_build.parsers.node_schemas import NodeSchemas
from rapid_gwm_build.nodes.node_cfg import NodeFactory


def example_usage():
    """Demonstrate the simplified node parser usage."""
    
    # Initialize the refactored parser (no NodeFactory needed as parameter)
    parser = NodeParser()
    
    # Example 1: Parse a simple input node
    print("=== Example 1: Simple Input Node ===")
    input_config = {
        'src': '/path/to/data.csv',
        'format': 'csv'
    }
    
    input_ref = parser.parse_node('input', input_config)
    print(f"Created input node: {input_ref}")
    
    # Example 2: Parse a mesh configuration
    print("\n=== Example 2: Mesh Configuration ===")
    mesh_config = {
        'nrow': 100,
        'ncol': 80,
        'nlay': 5,
        'delr': 250.0,
        'delc': 250.0,
        'top': {
            'pipeline': {
                'input': {'src': '/path/to/top.tif'},
                'pipeline': [
                    {'processor': 'load_raster'},
                    {'processor': 'resample_to_grid'}
                ]
            }
        },
        'bottoms': {
            'pipeline': {
                'input': {'src': '/path/to/bottoms.csv'},
                'pipeline': [
                    {'processor': 'load_csv'},
                    {'processor': 'interpolate_layers'}
                ]
            }
        }
    }
    
    mesh_ref = parser.parse_node('mesh', mesh_config)
    print(f"Created mesh node: {mesh_ref}")
    
    # Example 3: Parse modules configuration
    print("\n=== Example 3: Modules Configuration ===")
    modules_config = {
        'dis': {
            'src': {
                'nrow': '@mesh.nrow',
                'ncol': '@mesh.ncol',
                'nlay': '@mesh.nlay',
                'delr': '@mesh.delr',
                'delc': '@mesh.delc',
                'top': '@mesh.top',
                'botm': '@mesh.bottoms'
            }
        },
        'ic': {
            'src': {
                'strt': 0.0
            }
        },
        'chd': {
            'src': {
                'stress_period_data': {
                    'pipeline': {
                        'input': {'src': '/path/to/chd_data.csv'},
                        'pipeline': [
                            {'processor': 'load_csv'},
                            {'processor': 'format_chd_data'}
                        ]
                    }
                }
            }
        }
    }
    
    modules_refs = parser.parse_node('modules', modules_config)
    print(f"Created module nodes: {modules_refs}")
    
    # Example 4: Parse a standalone pipeline
    print("\n=== Example 4: Standalone Pipeline ===")
    pipeline_config = {
        'input': {
            'src': '/path/to/raw_data.nc',
            'format': 'netcdf'
        },
        'pipeline': [
            {'processor': 'load_netcdf'},
            {'processor': 'extract_variable', 'variable': 'precipitation'},
            {'processor': 'temporal_aggregate', 'method': 'mean'},
            {'processor': 'spatial_resample', 'target_grid': '@mesh.grid'}
        ]
    }
    
    pipeline_ref = parser.parse_node('pipeline', pipeline_config)
    print(f"Created pipeline node: {pipeline_ref}")
    
    # Example 5: Parse a built-in pipeline
    print("\n=== Example 5: Built-in Pipeline ===")
    builtin_pipeline_config = {
        'only_top': {
            'layer_index': 0
        }
    }
    
    builtin_ref = parser.parse_node('pipeline', builtin_pipeline_config)
    print(f"Created built-in pipeline node: {builtin_ref}")
    
    # Example 6: Validate configurations
    print("\n=== Example 6: Configuration Validation ===")
    
    # Valid pipeline config
    valid_pipeline = {
        'input': {'src': 'data.csv'},
        'pipeline': [{'processor': 'load_csv'}]
    }
    is_valid, msg = NodeSchemas.validate_config('pipeline', valid_pipeline)
    print(f"Valid pipeline config: {is_valid}")
    
    # Invalid pipeline config (missing required fields)
    invalid_pipeline = {
        'input': {'src': 'data.csv'}
        # Missing 'pipeline' field
    }
    is_valid, msg = NodeSchemas.validate_config('pipeline', invalid_pipeline)
    print(f"Invalid pipeline config: {is_valid}, Error: {msg}")
    
    # Example 7: Extract dependencies
    print("\n=== Example 7: Dependency Extraction ===")
    
    config_with_deps = {
        'nrow': '@mesh.nrow',
        'data': '@input_data',
        'nested': {
            'ref': '@another_node',
            'pipeline': {
                'input': {'src': '@source_data'},
                'pipeline': [
                    {'processor': 'process', 'param': '@parameter_node'}
                ]
            }
        }
    }
    
    dependencies = NodeSchemas.get_dependencies('module', config_with_deps)
    print(f"Extracted dependencies: {dependencies}")
    
    # Show all created nodes
    print(f"\n=== Summary ===")
    all_nodes = parser.get_all_nodes()
    print(f"Total nodes created: {len(all_nodes)}")
    for node in all_nodes:
        print(f"  - {node.type}: {node.ref_id}")


def example_client_code_integration():
    """Show how this integrates with your existing client code."""
    
    print("\n=== Client Code Integration Example ===")
    
    # Simulate your config structure
    config = {
        "simulations": {
            "test_sim": {
                "sim_type": "mf6",
                "ws": "/path/to/workspace",
                "mesh": {
                    "nrow": 100,
                    "ncol": 80,
                    "delr": 250.0,
                    "delc": 250.0
                },
                "modules": {
                    "dis": {"nrow": "@mesh.nrow", "ncol": "@mesh.ncol"},
                    "ic": {"strt": 0.0}
                },
                "pipelines": {
                    "data_processing": {
                        "input": {"src": "data.csv"},
                        "pipeline": [{"processor": "load_csv"}]
                    }
                }
            }
        }
    }
    
    # Initialize parser
    parser = NodeParser()
    all_sims = {}
    
    # Process each simulation block (similar to your current code)
    for sim_name, sim_cfg in config.get("simulations", {}).items():
        print(f"Processing simulation: {sim_name}")
        
        # Process each configuration block
        for key, val in sim_cfg.items():
            if key in ['sim_type', 'ws']:  # Skip simulation settings
                continue
            
            print(f"  Parsing {key} configuration...")
            
            try:
                # This is the main entry point - much cleaner than before!
                node_ref = parser.parse_node(node_type=key, config=val)
                print(f"    Created: {node_ref}")
                
                # Validate the configuration
                if parser.validate_config(key, val if isinstance(val, dict) else {'src': val}):
                    print(f"    ✓ Configuration valid")
                else:
                    print(f"    ✗ Configuration invalid")
                
                # Get dependencies
                deps = parser.get_dependencies_for_config(key, val if isinstance(val, dict) else {'src': val})
                if deps:
                    print(f"    Dependencies: {deps}")
                
            except Exception as e:
                print(f"    Error parsing {key}: {e}")
        
        # Get all nodes for this simulation
        all_nodes = parser.get_all_nodes()
        print(f"  Total nodes created: {len(all_nodes)}")
        
        # Store simulation data
        all_sims[sim_name] = {
            "sim_type": sim_cfg["sim_type"],
            "ws": sim_cfg["ws"],
            "nodes": {node.ref_id: node for node in all_nodes}
        }
        
        # Clear for next simulation
        parser.clear_all_nodes()
    
    return all_sims


if __name__ == "__main__":
    # Run examples
    example_usage()
    example_client_code_integration()
