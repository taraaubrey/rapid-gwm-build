# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

See PRD.md for full product requirements, feature roadmap, and open design questions.
See `.claude/program_of_work.md` for the phased development roadmap and task tracking.

## Project Overview

`rmb` (rapid model builder) is a Python package (`rapid-gwm-build`) for building groundwater model input files. It parses a user-defined YAML config, constructs a directed acyclic graph (DAG) of processing nodes, and executes them in topological order to generate model files (currently MODFLOW 6 via flopy).

## Commands

### Setup
```bash
uv sync                    # install dependencies
uv sync --group dev        # install with dev dependencies (ruff)
```

### Testing
```bash
uv run pytest              # run all tests
uv run pytest tests/test_parsers/test_node_parser.py  # run a single test file
uv run pytest -m unit      # run by marker (unit, integration, mesh, slow)
uv run pytest -k "test_name"  # run a specific test
```

### Linting
```bash
uv run ruff check .        # lint
uv run ruff check . --fix  # lint and auto-fix
```

## Architecture

The core pipeline is: **YAML config → NodeParser → NodeData set → GraphBuilder → DAG → RMBRunner → built results → write files**

### Key Concepts

**Node types** (defined in `nodes/node_data.py:NODE_TYPE_SCHEMAS`):
- `input` — a raw value or file path
- `pipe` — a single processing step (processor + input)
- `pipeline` — a chain of pipes; its output is the last pipe's output
- `mesh_config` — scalar mesh parameters (crs, nlay, resolution, etc.)
- `mesh_data` — spatial mesh data arrays (top, bottoms, active_domain)
- `module` — a model package (e.g., flopy's `ModflowGwf`, `ModflowDis`)

**Node IDs** are derived from `context_path` list joined with dots: `['modules', 'dis', 'top']` → `modules.dis.top`. Cross-node references in YAML use `@node.id` syntax.

**Template system** (`templates/mf6_template.yaml`): defines which flopy functions to call for each module type and their `build_dependencies` (inputs auto-wired between modules). The `sim_type: mf6` in the user YAML selects this template.

**Processors** (`processors/`): callable data-transformation functions registered with `@register_processor` in `registries.py`. Processors can be built-in (by name), from a local file (`path/to/file.function`), or from an installed package (`module.function`). The `ProcessorEngine` resolves and caches them.

**Builders** (`nodes/builders/`): one builder per node type, registered with `@register_builder`. The `NodeBuildEngine` dispatches each node to its typed builder during graph traversal.

**Global registries** (`registries.py`):
- `BUILDER_REGISTRY` — maps node type strings to builder instances
- `BUILTIN_PROCESSORS` — maps processor name strings to `{func, dependency_args, context_required}`
- `build_registry` (`build_registry.py`) — stores `Result` objects for already-built nodes (used for dependency data fetching)

**Caching** (`cache.py`, `config.py`): `joblib.Memory` cache controlled by `CONFIG['cache_nodes']` and `CONFIG['cache_enabled']`. Config can be overridden via `config.json` or `YOUR_PACKAGE_CONFIG` env var.

### Key Files

| File | Purpose |
|---|---|
| `src/rapid_gwm_build/nodes/parse/node_parser.py` | Parses YAML config sections into `NodeData` objects |
| `src/rapid_gwm_build/nodes/node_data.py` | `NodeData` dataclass — core parsed node representation |
| `src/rapid_gwm_build/graph_builder.py` | `GraphBuilder` — constructs networkx DAG from `NodeData` set |
| `src/rapid_gwm_build/rmb_runner.py` | `RMBRunner` — topological traversal and node build execution |
| `src/rapid_gwm_build/node_engine.py` | `NodeBuildEngine` — dispatches nodes to typed builders |
| `src/rapid_gwm_build/registries.py` | Centralized `@register_builder` / `@register_processor` decorators |
| `src/rapid_gwm_build/processors/processor_engine.py` | `ProcessorEngine` — resolves processor callables |
| `src/rapid_gwm_build/templates/mf6_template.yaml` | MODFLOW 6 module template (func paths, build_dependencies) |
| `src/rapid_gwm_build/parsers/config_parser.py` | YAML loading with `${vars.x}` variable substitution |

### YAML Config Structure

User YAML files follow this structure (see `examples/simple_freyburg/freyburg_1lyr_stress.yaml`):
```yaml
vars:          # variable substitution with ${vars.key} syntax
simulations:
  <sim_name>:
    sim_type: mf6
    ws: <output_dir>
    mesh:      # spatial discretization config
    modules:   # model packages (matched to template)
      <module_type>[-<user_name>]:
        data:  # spatial/array data for this module
        cmd:   # scalar kwargs passed directly to the flopy function
```

Module keys can be `type` (e.g., `dis`) or `type-name` (e.g., `dis-mydis`) to allow multiple instances.



# Instructions
- always display edits for review
- always update dev_log.md after any work on this project
- work in plan mode prior to any work completed
- always create a phase document which highlights changes
- create a git commit message after every phase completion for user to input manually
- unless explicitly asked, always load and assess entire datasets