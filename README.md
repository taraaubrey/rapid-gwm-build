# rmb — Rapid Groundwater Model Builder

A Python package for building groundwater model input files from YAML configuration. Currently supports MODFLOW 6 via [flopy](https://github.com/modflowpy/flopy).

**Status:** Under active development.

## Installation

```bash
# Clone and install in development mode
git clone https://github.com/taraaubrey/rapid-gwm-build.git
cd rapid-gwm-build
uv sync                    # install dependencies
uv sync --group dev        # with dev tools (ruff)
```

After installation, the `rmb` CLI command is available.

## Quick Start

### CLI

```bash
# Build a model from a YAML config
rmb build examples/pakipaki02/pakipaki02.yaml

# Build with verbose output
rmb build examples/pakipaki02/pakipaki02.yaml --verbose

# Validate config without building
rmb validate examples/pakipaki02/pakipaki02.yaml

# Dry run — parse and build the DAG without executing
rmb build examples/pakipaki02/pakipaki02.yaml --dry-run

# Visualize the dependency graph
rmb build examples/pakipaki02/pakipaki02.yaml --graph
```

### Python API

```python
from rapid_gwm_build import build

result = build("examples/pakipaki02/pakipaki02.yaml")
print(result)
```

For interactive use (notebooks, debugging):

```python
from rapid_gwm_build import create_simulation

sim = create_simulation("examples/pakipaki02/pakipaki02.yaml")
sim.build()
sim.write()

# Inspect results
print(sim.result)
```

## CLI Reference

```
rmb build <yaml_path> [options]    Build model from YAML config
rmb validate <yaml_path> [options] Validate config without building
```

### `rmb build` options

| Flag | Description |
|---|---|
| `--ws DIR` | Override workspace (output) directory |
| `--no-cache` | Disable node caching |
| `--verbose, -v` | Enable verbose/debug output |
| `--input FILE` | Additional YAML file(s) to merge (repeatable) |
| `--input-ext EXT` | Load all files with this extension from config directory |
| `--dry-run` | Parse and build graph without executing |
| `--graph` | Visualize the dependency graph and exit |

### `rmb validate` options

| Flag | Description |
|---|---|
| `--verbose, -v` | Enable verbose output |

## YAML Config Format

User configs follow this structure (see `examples/pakipaki02/pakipaki02.yaml`):

```yaml
vars:
  ws: examples/models
  data_dir: examples/data

simulation:
  setup:
    sim_type: mf6           # required — selects backend template
    ws: ${vars.ws}/my_model  # output directory
    sim_name: my_sim         # simulation name

  mesh:
    crs: 2193
    nlay: 8
    resolution: 25
    domain: ${vars.data_dir}/domain.shp
    top: ${vars.data_dir}/dem.tif
    bottoms:
      input: ${vars.data_dir}/basement.tif
      pipeline:
        - processor: tile_to_nlay

  modules:
    sim:
      sim_name: my_sim
      exe_name: mf6
    gwf:
      modelname: my_model
    dis:
      length_units: meters
    # ... additional modules (tdis, ims, npf, etc.)
```

Key concepts:
- **`${vars.key}`** — Variable substitution from the `vars:` block
- **`@node.id`** — Cross-references between nodes
- **`pipeline`** — Data processing chains with registered processors
- **Module keys** — Can be `type` (e.g., `dis`) or `type-name` (e.g., `dis-mydis`)

## Debugging

For development/debugging, use the debug runner which exposes each pipeline stage:

```bash
# Step through with debugpy (VS Code)
uv run python -m debugpy --listen 5678 --wait-for-client examples/pakipaki02/debug_run.py

# Or run directly with print output at each stage
uv run python examples/pakipaki02/debug_run.py
```

See `examples/pakipaki02/debug_run.py` for the VS Code `launch.json` snippet.

## Architecture

The core pipeline: **YAML config → NodeParser → DAG → RMBRunner → model files**

- **Nodes** — typed data units (input, pipe, pipeline, mesh_config, mesh_data, module)
- **Processors** — registered data-transformation functions (`@register_processor`)
- **Builders** — one per node type, registered with `@register_builder`
- **Templates** — define which flopy functions to call for each module type

See `.claude/CLAUDE.md` for detailed architecture documentation.

## Development

```bash
uv sync --group dev               # install dev dependencies
uv run ruff check .               # lint
uv run ruff check . --fix         # lint and auto-fix
uv run pytest                     # run tests
uv run pytest -m unit             # run unit tests only
```
