# Parser System Guide

## Overview
This document explains the current parser file structure after refactoring and removal of `src_arg` complexity.

## File Structure and Status

### ✅ **ACTIVE FILES** (Use These)

#### **Main Entry Point**
- **`node_parser_refactored.py`** - Main orchestrator for all parsing operations
  - Use: `from rapid_gwm_build.parsers.node_parser_refactored import NodeParser`
  - Main class: `NodeParser()`
  - Purpose: Context-path based parsing without `from_node` complexity

#### **Supporting Modules**
- **`specialized_parsers.py`** - Modular parsers for specific node types
  - Contains: `InputNodeParser`, `PipeNodeParser`, `MeshNodeParser`, etc.
  - Managed by: `NodeParserRegistry` class
  
- **`pipeline_parser.py`** - Dedicated pipeline parsing logic
  - Handles: Built-in and custom pipeline configurations
  - Used by: `NodeParser` for pipeline-specific logic
  
- **`node_schemas.py`** - Schema definitions and validation
  - Contains: `NodeSchema` class and validation rules
  - Purpose: Centralized configuration validation

#### **Utility Files**
- **`config_parser.py`** - YAML loading and variable substitution
  - Updated to use: `node_parser_refactored.NodeParser`
  - Purpose: Load and preprocess configuration files

### ❌ **LEGACY FILES** (Should be removed)
- **`node_parser.py`** - Original parser with `from_node` complexity
- **`simplified_node_parser.py`** - Intermediate version during refactoring

### 📚 **DOCUMENTATION/EXAMPLES**
- **`src/rapid_gwm_build/parsers/ss/usage_examples.py`** - Example usage patterns
- **`src/rapid_gwm_build/parsers/ss/comparison_before_after.py`** - Before/after comparison (illustrative)

## Key Changes Made

### 1. Removed `src_arg` Parameter
- **Old**: `src_arg=True/False` to distinguish between parameter values and file paths
- **New**: Auto-detection by default (`src_arg=False`), command parameters handled via 'cmd' key
- **Benefit**: Simpler API, less confusion

### 2. Replaced `from_node` with `context_path`
- **Old**: `from_node` parameter created complex dependency chains
- **New**: `context_path: List[str]` explicitly shows parsing hierarchy
- **Example**: `context_path=['mesh', 'top']` instead of mysterious parent node references

### 3. Modular Architecture
- Each node type has its own specialized parser
- Clear separation of concerns
- Easier to test and maintain

## How to Use

### Basic Usage
```python
from rapid_gwm_build.parsers.node_parser_refactored import NodeParser

# Initialize parser
parser = NodeParser()

# Parse different node types
mesh_ref = parser.parse_node('mesh', mesh_config, context_path=['mesh'])
module_ref = parser.parse_node('module', module_config, context_path=['modules', 'my_module'])

# Get all created nodes
all_nodes = parser.get_all_nodes()
```

### Configuration Parsing
```python
from rapid_gwm_build.parsers.config_parser import ConfigParser

# Load and parse YAML configuration
config = ConfigParser.parse('config.yaml')

# Parse nodes from configuration
parser = NodeParser()
for node_type, node_config in config.items():
    if node_type in ['mesh', 'modules', 'pipeline']:
        parser.parse_node(node_type, node_config)
```

## Migration from Old System

### Old Way (Don't use)
```python
# DON'T USE - Legacy approach
from rapid_gwm_build.parsers.node_parser import NodeParser  # ❌ Old file

parser = NodeParser()
node = parser.parse_input(src=data, src_arg=True, from_node=parent)  # ❌ Complex
```

### New Way (Use this)
```python
# ✅ NEW APPROACH
from rapid_gwm_build.parsers.node_parser_refactored import NodeParser

parser = NodeParser()
node = parser.parse_input(config=data, context_path=['input'])  # ✅ Simple and clear
```

## Context Path Examples

Context paths provide clear hierarchy information:

- `['mesh']` - Root mesh node
- `['mesh', 'top']` - Top layer of mesh
- `['modules', 'solver']` - Solver module
- `['pipeline', 'preprocessing']` - Preprocessing pipeline
- `['modules', 'solver', 'input', 'parameters']` - Parameters for solver input

## Recommended Cleanup Steps

1. **Remove legacy files**:
   ```bash
   rm src/rapid_gwm_build/parsers/node_parser.py
   rm src/rapid_gwm_build/parsers/simplified_node_parser.py
   ```

2. **Update all imports** to use `node_parser_refactored`

3. **Update client code** to use `context_path` instead of `from_node`

4. **Remove any remaining `src_arg` usage** in custom code

## Benefits of New System

1. **Clearer**: Explicit context paths vs. mysterious parent node references
2. **Simpler**: No more `src_arg` confusion
3. **Modular**: Each node type has its own parser
4. **Testable**: Easy to unit test individual parsers
5. **Maintainable**: Clear separation of concerns
6. **Extensible**: Easy to add new node types

## Next Steps

1. **Archive/remove legacy files** to avoid confusion
2. **Update documentation** to reflect new patterns
3. **Update tests** to use new parser interface
4. **Consider adding type hints** for better IDE support
