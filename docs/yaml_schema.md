# RMB YAML Schema Reference

The user-editable YAML config is the primary interface for `rmb`. This document defines the schema for all field types and covers every supported use case.

---

## Top-level Structure

```yaml
vars:          # variable substitution — ${vars.key} syntax
simulation:
  setup:       # sim_type, ws, sim_name
  mesh:        # spatial discretisation config
  modules:     # model packages
    <module_type>[-<name>]:
      data:    # spatial/array inputs for this module
      cmd:     # scalar kwargs passed directly to the flopy function
```

---

## Field Schema

Every field in `mesh:` or `data:` follows one of two forms.

### Form 1 — Flat (single source)

```yaml
field:
  src: <string>      # path, scalar, or @ref — omit if pipeline generates data
  load: {...}        # load-time options; only valid when src is a file path
  metadata: {...}    # parameterisation bounds: lb, ub
  pipeline: [...]    # ordered list of processors
```

**All keys are optional**, but at least one of `src` or `pipeline` must be present.

**Shorthand:** when no load options, metadata, or pipeline are needed, the field value can be written directly:

```yaml
field: value         # equivalent to src: value with no other keys
```

### Form 2 — Data block (named multi-source)

```yaml
field:
  data:
    <name>:          # named data entry — follows Form 1 schema
      src: ...
      load: {...}
      pipeline: [...]
    <name>: ...
  pipeline: [...]    # block-level pipeline — receives named entry outputs
  metadata: {...}    # optional parameterisation bounds on the combined output
```

`data:` entries are **recursive** — each named entry follows the same schema, including the ability to have its own `data:` block.

---

## Rules

| Rule | Detail |
|---|---|
| `src` is always a plain string | path, scalar value, or `@ref` — never a dict |
| `load:` only with file-path `src` | not valid for scalars or `@ref` |
| Flat form preferred | a single-entry `data:` block with no combining pipeline should be written as flat `src:` form instead |
| `@ref` syntax | `'@node.id'` references another node's output — dot-separated context path |
| `${vars.key}` syntax | variable substitution resolved before parsing |
| Processors are strings | built-in name, `path/to/file.function`, or `module.function` |

---

## Use Cases

### 1. Shorthand — scalar, path, or @ref

No wrapping needed. Use for simple values with no load options, metadata, or pipeline.

```yaml
# scalar
nlay: 8
resolution: 25

# file path (variable substituted)
top: ${vars.data_dir}/model2_dem.tif
domain: ${vars.data_dir}/model2_domain.shp

# cross-node reference
head: '@mesh.top'
nlay_ref: '@mesh.nlay'
```

---

### 2. src + load (no pipeline)

Load a file with non-default load-time options.

```yaml
elev:
  src: ${vars.data_dir}/model2_dem.tif
  load:
    resampling: min
```

---

### 3. src + pipeline (no load)

Load a file normally, then apply transforms.

```yaml
active_domain:
  src: ${vars.data_dir}/model2_domain.shp
  pipeline:
    - processor: tile_to_nlay
```

---

### 4. src + load + pipeline

Load with options, then transform.

```yaml
elev:
  src: ${vars.data_dir}/model2_dem.tif
  load:
    resampling: min
  pipeline:
    - processor: clip_to_domain
      domain: '@mesh.active_domain'
```

---

### 5. Full flat form — src + load + metadata + pipeline

```yaml
elev:
  src: ${vars.data_dir}/model2_dem.tif
  load:
    resampling: min
  metadata:
    lb: 0.01
    ub: 100
  pipeline:
    - processor: clip_to_domain
      domain: '@mesh.active_domain'
```

---

### 6. Scalar src + pipeline

A literal value fed into a pipeline. No `load:` needed.

```yaml
cond:
  src: 1
  pipeline:
    - processor: simple_math
      expression: "x**2 * y"
      variables: ['x', 'y']
      y: '@mesh.resolution'
```

---

### 7. @ref src + pipeline

Start from another node's computed output, then transform.

```yaml
k:
  src: '@mesh.active_domain'
  pipeline:
    - processor: pkpk_functions.k_layers
      nlay: '@mesh.nlay'
      layer_mapping:
        0: 1000
        1: 0.01
```

---

### 8. No src — pipeline generates data

Omit `src` entirely when the first processor creates data from scratch.

```yaml
idomain:
  pipeline:
    - processor: create_from_mesh
      shape: '@mesh.shape'
      fill_value: 1
```

---

### 9. Multi-step pipeline

Each processor's output is the next processor's input.

```yaml
mask:
  src: ${vars.data_dir}/model2_mbr.shp
  pipeline:
    - processor: domain_boundary
    - processor: make_inactive
      layers: [-2, -1]
```

---

### 10. data block — independent named entries

Each named entry is a separate parameter passed to the module. No block-level combining pipeline — entries are independent.

```yaml
drn-riv:
  data:
    mask: ${vars.data_dir}/model2_drains.shp    # shorthand
    elev:
      src: ${vars.data_dir}/model2_dem.tif
      load:
        resampling: min
      metadata:
        lb: 0.01
        ub: 100
    cond:
      src: 1
      metadata:
        lb: 0.01
        ub: 100
      pipeline:
        - processor: simple_math
          expression: "x**2 * y"
          variables: ['x', 'y']
          y: '@mesh.resolution'
  cmd:
    pname: drn-riv
```

---

### 11. data block — multi-input with block-level combining pipeline

Named entries each load independently. The block-level `pipeline:` receives them as named inputs and combines into a single output.

```yaml
bottoms:
  data:
    basement:
      src: ${vars.data_dir}/basement_z.tif
      load:
        resampling: min
    surface:
      src: ${vars.data_dir}/model2_dem.tif
      load:
        resampling: mean
  pipeline:
    - processor: build_bottoms
      basement: '@bottoms.data.basement'
      surface: '@bottoms.data.surface'
      nlay: '@mesh.nlay'
      group_nlay: [6, 1, 1]
      group_bottoms: [0, -10, -20]
      min_thickness: 1
```

---

### 12. data block — entries with individual pipelines feeding the block pipeline

Each named entry runs its own pipeline first. The block-level pipeline then receives the processed outputs.

```yaml
combined_k:
  data:
    marine:
      src: ${vars.data_dir}/marine_k.tif
      load:
        resampling: mean
      pipeline:
        - processor: log_transform
        - processor: clip_to_domain
          domain: '@mesh.active_domain'
    alluvial:
      src: ${vars.data_dir}/alluvial_k.tif
      load:
        resampling: mean
      pipeline:
        - processor: clip_to_domain
          domain: '@mesh.active_domain'
  pipeline:
    - processor: merge_zones
      marine: '@combined_k.data.marine'
      alluvial: '@combined_k.data.alluvial'
      zone_mask: '@mesh.active_domain'
```

---

### 13. Nested data blocks

A named entry inside `data:` can itself contain a `data:` block. The schema is fully recursive.

```yaml
hydraulic_params:
  data:
    k_layers:
      data:
        k_shallow:
          src: ${vars.data_dir}/k_shallow.tif
          load:
            resampling: mean
        k_deep:
          src: ${vars.data_dir}/k_deep.tif
          load:
            resampling: mean
      pipeline:
        - processor: merge_depth_zones
          shallow: '@hydraulic_params.data.k_layers.data.k_shallow'
          deep: '@hydraulic_params.data.k_layers.data.k_deep'
    sy:
      src: ${vars.data_dir}/sy.tif
      load:
        resampling: mean
  pipeline:
    - processor: apply_anisotropy
      k: '@hydraulic_params.data.k_layers'
      sy: '@hydraulic_params.data.sy'
      ratio: 0.1
```

---

### 14. Full module example

```yaml
npf:
  data:
    k:
      src: 1.0
      pipeline:
        - processor: ${vars.scripts}pkpk_functions.k_layers
          nlay: '@mesh.nlay'
          nrow: '@modules.dis.nrow'
          ncol: '@modules.dis.ncol'
          layer_mapping:
            0: 1000
            1: 0.01
            2: 0.01
            3: 1000
            4: 10000
  cmd:
    save_specific_discharge: True
    icelltype: 0
```

---

### 15. Full mesh example

Mix of shorthands and full forms within a single `mesh:` block.

```yaml
mesh:
  crs: 2193                                         # scalar shorthand
  nlay: 8                                           # scalar shorthand
  resolution: 25                                    # scalar shorthand
  domain: ${vars.data_dir}/model2_domain.shp        # path shorthand
  top: ${vars.data_dir}/model2_dem.tif              # path shorthand
  bottoms:
    data:
      basement:
        src: ${vars.data_dir}/basement_z.tif
        load:
          resampling: min
    pipeline:
      - processor: build_bottoms.build_bottoms
        basement: '@mesh.bottoms.data.basement'
        top: '@mesh.top'
        nlay: '@mesh.nlay'
        group_nlay: [6, 1, 1]
        group_bottoms: [0, -10, -20]
        min_thickness: 1
  active_domain:
    src: ${vars.data_dir}/model2_domain.shp
    pipeline:
      - processor: tile_to_nlay
      - processor: ${vars.scripts}pkpk_functions.make_bottom_inactive
        mask: ${vars.data_dir}/confining_area.shp
        inactive_indices: [-2, -1]
```

---

## Schema Summary

```
field: <value>                    # shorthand — scalar, path, or @ref

field:
  src: <string>                   # single source
  load:                           # load-time options (file paths only)
    resampling: <method>
    # ... other loader kwargs
  metadata:                       # parameterisation bounds
    lb: <float>
    ub: <float>
  pipeline:                       # ordered processors
    - processor: <name>
      <arg>: <value>
      <arg>: '@node.id'           # cross-node reference as processor arg

field:
  data:                           # named multi-source entries
    <name>: <value>               # shorthand entry
    <name>:
      src: <string>
      load: {...}
      pipeline: [...]
      data: {...}                 # recursive — entries can have their own data block
  pipeline:                       # block-level combining pipeline
    - processor: <name>
      <name>: '@field.data.<name>'
  metadata: {...}
```

---

## Processor Reference Format

Processors can be specified as:

| Format | Example | Resolved from |
|---|---|---|
| Built-in name | `tile_to_nlay` | built-in processor registry |
| Local file function | `${vars.scripts}pkpk_functions.k_layers` | path/to/file.function |
| Installed package | `scikit.learn.smooth` | installed Python package |
