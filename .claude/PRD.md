# Product Requirements Document — `rapid-gwm-build` (`rmb`)

> **Living document.** Update this file as decisions are made, features change, or new requirements emerge.
> See [How to Update This Document](#how-to-update-this-document) at the bottom.

---

## Table of Contents
1. [Product Overview](#1-product-overview)
2. [Current Architecture](#2-current-architecture)
3. [YAML Config Structure](#3-yaml-config-structure)
4. [Node System](#4-node-system)
5. [Processor System](#5-processor-system)
6. [Template System](#6-template-system)
7. [Feature Roadmap](#7-feature-roadmap)
8. [Open Questions & TBD](#8-open-questions--tbd)
9. [Known Tech Debt](#9-known-tech-debt)
10. [How to Update This Document](#10-how-to-update-this-document)

---

## 1. Product Overview

**`rapid-gwm-build`** (`rmb`) is a Python library for building numerical groundwater model input files from a declarative YAML configuration. It currently targets MODFLOW 6 (via `flopy`), with the architecture designed to support other simulators in future.

**Core value proposition:** Users describe *what* they want (domain, layers, boundary conditions, data sources) in a YAML file. `rmb` handles *how* to get there — fetching and preprocessing spatial data, wiring dependencies between model packages, and writing model-ready files.

**Primary user:** A groundwater modeller who can write YAML and Python, but wants to avoid boilerplate flopy setup and data preprocessing scripts.

**Current working state:** The pipeline runs end-to-end for the `pakipaki02` example. Client code (see `examples/pakipaki02/client_code.py`) manually orchestrates the pipeline steps.

---

## 2. Current Architecture

### Pipeline

```
YAML file
  └─► ConfigParser          (variable substitution: ${vars.x})
        └─► NodeParser       (YAML sections → NodeData objects)
              └─► GraphBuilder  (NodeData set → networkx DAG)
                    └─► RMBRunner   (topological traversal)
                          └─► NodeBuildEngine  (dispatches to typed builders)
                                └─► flopy objects + written files
```

### Key Classes

| File | Class | Role |
|---|---|---|
| `parsers/config_parser.py` | `ConfigParser` | Loads YAML, resolves `${vars.x}` |
| `nodes/parse/node_parser.py` | `NodeParser` | Converts YAML sections into `NodeData` |
| `nodes/node_data.py` | `NodeData` | Core dataclass for a parsed node |
| `graph_builder.py` | `GraphBuilder` | Builds networkx DAG from `NodeData` set |
| `rmb_runner.py` | `RMBRunner` | Orchestrates build via topological traversal |
| `node_engine.py` | `NodeBuildEngine` | Dispatches each node to its typed builder |
| `registries.py` | — | `@register_builder`, `@register_processor` decorators |
| `processors/processor_engine.py` | `ProcessorEngine` | Resolves processor callables |
| `build_registry.py` | `build_registry` | Stores `Result` objects for built nodes |
| `cache.py` | — | `joblib.Memory` cache (toggled via `CONFIG`) |

### Client Code Pattern (current)

```python
config = ConfigParser.parse(input_yaml)
parser = NodeParser(sim_template=config.get("template", {}))
for key, val in config.get("simulation", {}).items():
    parser.parse_node(node_type=key, config=val)
all_nodes = parser.get_all_nodes()

graphbuilder = GraphBuilder(all_nodes)
G = graphbuilder.build()
sG = graphbuilder.get_subgraph(ntype='module')
cG = graphbuilder.get_subgraph(ntype='mesh_config')

engine = NodeBuildEngine(registry=BUILDER_REGISTRY)
runner = RMBRunner(graph=sG, mesh_graph=cG, engine=engine)
runner.run()
```

> **TBD:** Whether this client code becomes a high-level API function or CLI entrypoint. See [§8](#8-open-questions--tbd).

---

## 3. YAML Config Structure

```yaml
vars:                          # variable substitution (${vars.key})
  ws: /path/to/output
  data_dir: examples/data

simulation:
  setup:                       # sim_type, ws, sim_name
    sim_type: mf6
    ws: ${vars.ws}/mymodel
    sim_name: mymodel

  mesh:                        # spatial discretization
    crs: 2193
    nlay: 8
    resolution: 25
    domain: path/to/domain.shp
    active_domain: ...         # pipeline or input
    top: path/to/dem.tif
    bottoms: ...               # pipeline or input

  modules:                     # model packages
    sim:
      cmd: { ... }             # scalar kwargs to flopy
    tdis-mytdis:               # type-name for multiple instances
      cmd: { ... }
    dis:
      cmd: { ... }
    npf:
      data:                    # spatial/array data processed before flopy call
        k: ...
      cmd: { ... }
    drn-riv:
      data:
        mask: path/to/drains.shp
        elev: ...
        cond: ...
```

### Cross-node references
- `@mesh.top` — reference to a node in the mesh block
- `@modules.dis.nrow` — reference to a built module output
- `@modules.wel.data.flux` — reference to data within a module

---

## 4. Node System

### Node Types

| Type | Description |
|---|---|
| `input` | Raw scalar value or file path |
| `pipe` | Single processing step (processor + input) |
| `pipeline` | Ordered chain of pipes; output = last pipe's output |
| `mesh_config` | Scalar mesh parameters (crs, nlay, resolution, etc.) |
| `mesh_data` | Spatial arrays for the mesh (top, bottoms, active_domain) |
| `module` | A model package (maps to a flopy function via the template) |

### Node IDs
Derived from `context_path` joined with dots:
- `['mesh', 'top']` → `mesh.top`
- `['modules', 'dis', 'top']` → `modules.dis.top`

### Builders
Each node type has a registered builder in `nodes/builders/`. The `NodeBuildEngine` dispatches via `BUILDER_REGISTRY`.

---

## 5. Processor System

Processors are callable data-transformation functions. They can be:
- **Built-in** (by name string): registered via `@register_processor` in `registries.py`
- **Local file** (by path): `examples/scripts/myfuncs.make_inactive`
- **Installed package** (by module path): `mypackage.module.function`

The `ProcessorEngine` resolves and caches them.

### Built-in Processors (current)
| Name | Purpose |
|---|---|
| `tile_to_nlay` | Tile a 2D array to nlay layers |
| `from_structured_mesh` | Extract mesh properties (nrow, ncol, delr, delc, etc.) |
| `domain_boundary` | Get active domain boundary cells |
| `make_inactive` | Mark specific layers as inactive |
| `simple_math` | Apply expression to arrays |
| `check_data_dims_tdis` | Validate array dimensions vs tdis |
| `array_to_file` | Write array to external file for flopy |

### Processor Pipeline Syntax
```yaml
bottoms:
  input: path/to/basement.tif
  pipeline:
    - processor: scripts/build_bottoms.build_bottoms
      top: '@mesh.top'
      nlay: '@mesh.nlay'
      group_nlay: [6, 1, 1]
```

---

## 6. Template System

`templates/mf6_template.yaml` defines:
- Which flopy function to call for each module type (`func`)
- Auto-wired `build_dependencies` (inputs resolved from the graph automatically)
- Whether duplicates are allowed (`duplicates_allowed`)
- Default parameters if user doesn't specify (`default_build`)

### Currently Templated Modules
`obs`, `sim`, `tdis`, `ims`, `gwf`, `npf`, `dis`, `ic`, `wel`, `drn`, `ghb`, `rcha`, `chd`, `oc`

### Commented-Out / Planned Modules
- `sto` (storage)
- `sfr` (streamflow routing)
- `rch` (recharge, non-array version)

---

## 7. Feature Roadmap

### 7.1 Implemented / Working
- [x] YAML parsing with variable substitution
- [x] Node graph construction and topological execution
- [x] Pipeline processor chains (built-in + custom)
- [x] Cross-node references (`@node.id`)
- [x] MF6 module building via flopy template
- [x] External file writing (arrays and tables)
- [x] Cache system (joblib, togglable)
- [x] Multiple instances of a package (`drn-riv`, `wel-mbr`, etc.)

### 7.2 Planned — Parameter Filling from Other Models

**Goal:** Allow parameters for a node to be sourced from another model (rather than requiring explicit spatial data files) when a parameter is missing or needs to be derived.

**Two entry points being considered:**

#### Option A — Reference an external YAML definition
```yaml
modules:
  npf:
    data:
      k:
        source_model:
          yaml: path/to/parent_model.yaml   # another rmb yaml
          node: modules.npf.data.k          # which node to pull from
          transform: ...                    # optional scaling/mapping
```

#### Option B — Inline model definition
```yaml
modules:
  npf:
    data:
      k:
        source_model:
          type: geostatistical              # or: regression, kriging, nn, etc.
          inputs: ['@mesh.top', ...]
          parameters: { ... }
```

**Key design questions for this feature:** See [§8.1](#81-parameter-filling-feature).

**What "model" could mean:**
- Another `rmb` YAML (parent model, regional model)
- A calibrated flopy model output (reading from `.hds`, `.cbc`, etc.)
- A geostatistical/interpolation model (kriging from borehole data)
- A machine-learning model (regression, random forest on spatial covariates)

### 7.3 Planned — Other

- [ ] High-level Python API (`rmb.build(yaml_path)`) to replace manual client code
- [ ] CLI entrypoint (`rmb build mymodel.yaml`)
- [ ] Transient stress period support (multi-period data pipelines)
- [ ] `sto` module support
- [ ] `sfr` module support
- [ ] `obs` module full integration
- [ ] Support for non-structured grids (DISV)
- [ ] Multiple GWF models in one simulation
- [ ] `PEST`/`pyemu` integration for parameterization (template structure already has `parameterization` blocks in `drn`, `chd`)
- [ ] Simulator-agnostic interface (targets beyond mf6)

---

## 8. Open Questions & TBD

### 8.1 Parameter Filling Feature
> **This is the primary new feature under design.**

- [ ] What types of "source models" should be supported first? (rmb yaml, calibrated flopy output, geostatistical, ML?)
- [ ] How is a source model referenced — by file path, by name, by URL?
- [ ] Should the source model be built as part of the same pipeline run, or pre-built?
- [ ] If built in the same run: does it become a subgraph in the DAG, or a separate RMBRunner call?
- [ ] How is spatial interpolation/resampling handled when grids differ?
- [ ] What happens if the source model fails to produce a value — fallback? error?
- [ ] Should there be a priority chain: `explicit value → source_model → default`?
- [ ] How does this interact with the cache system?

### 8.2 API / Entrypoint Design
- [ ] Should client code be replaced with a single `rmb.build(yaml)` function?
- [ ] Should there be a CLI (`rmb build mymodel.yaml`)?
- [ ] Should setup (`Path.mkdir` etc.) be handled by `rmb` or left to the user?

### 8.3 Multi-Simulation Support
- [ ] Current YAML has a single `simulation` block. Should multiple simulations (e.g., steady-state + transient) be supported in one YAML?
- [ ] How should parent/child model relationships be expressed (TMR-style)?

### 8.4 Template Extensibility
- [ ] Can users supply their own template YAML to extend or override `mf6_template.yaml`?
- [ ] How should custom (non-standard) flopy packages be handled?

### 8.5 `ss/` Directory
> **[2026-03-25] Resolved:** Removed in Phase 1.1. No active code depended on `ss/`. The entire `src/rapid_gwm_build/ss/` directory, `nodes/ss_node_types.py`, and `examples/ss/` were deleted.

### 8.6 Dependency Management
> **[2026-03-25] Partially resolved in Phase 1.2:**
> - `modflow-setup`, `netcdf4`, `cerberus`, `pyemu`, `pyshp`, `scikit-learn`, `setuptools` removed (zero imports found)
> - `debugpy`, `dvc`, `ipykernel` moved to optional dependency groups
> - `flopy` pin widened from `==3.9.2` to `>=3.9.2`
- [ ] Should simulator-specific deps (flopy) be optional extras (`rmb[mf6]`)?

### 8.7 Testing
> **[2026-03-25] Partially resolved:** `slow` marker added to pyproject.toml in Phase 1.3.
- [ ] What level of integration test coverage exists? What's the target?
- [ ] Should examples (`pakipaki02`) be runnable as integration tests?

---

## 9. Known Tech Debt

| Item | Location | Notes |
|---|---|---|
| Manual `Path.mkdir` in client code | `client_code.py:40-41` | Should be handled by rmb internals |

---

## 10. How to Update This Document

This PRD is a living document. Update it as the project evolves — do not let it drift from reality.

### What to update when

| Event | What to update |
|---|---|
| A feature is implemented | Move it to §7.1 (Implemented), mark `[x]` |
| A design decision is made | Remove the question from §8, add a note to the relevant section |
| A new feature is requested | Add to §7.2 or §7.3 with description |
| Architecture changes | Update §2 (pipeline diagram, class table) |
| New node type or processor | Update §4 or §5 table |
| New template module | Update §6 module list |
| Tech debt resolved | Remove from §9 |
| New tech debt identified | Add to §9 with file:line reference |
| New open question | Add to the relevant subsection in §8 |

### Updating for AI context

When using this document to inform AI assistant context (e.g., via CLAUDE.md), paste a summary or the relevant sections. Key sections to keep current:
- **§2** — Architecture (pipeline and class table)
- **§7.1** — What's actually implemented
- **§7.2** / **§7.3** — What's planned
- **§8** — Open design questions (especially §8.1 for the parameter filling feature)

To link this from CLAUDE.md, add:
```
See PRD.md for full product requirements, feature roadmap, and open design questions.
```

### Versioning
- No formal versioning required — this is a dev-stage document
- Use git history to track how decisions evolved
- When a major direction changes, add a brief `> **[DATE] Decision:**` note inline rather than deleting old content, so context is preserved

---

*Last updated: 2026-02-19*
