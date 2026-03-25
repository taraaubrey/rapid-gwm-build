# Fix: IC strt External File Writing & Add Load Validation

## Problem

The pakipaki02 model built successfully (203 nodes) but the IC package's `strt` data was written incorrectly. When loading the model back via `flopy.mf6.MFSimulation.load()`, it failed with:

```
Expected data size 24400 but only found 0
```

**Root cause:** In `pakipaki02.yaml`, the user specified `strt: '@mesh.top'` in the IC `cmd` section. The node parser excludes any template `build_dependency` that matches a user `cmd` key, so the template's `strt` pipeline (`check_data_dims_tdis` → `array_to_file`) was completely bypassed. Flopy received the raw 2D `mesh.top` array instead of 3D data with external file references.

DIS botm and NPF k worked correctly because their template pipelines were not overridden by user cmd.

## Fix

### 1. `examples/pakipaki02/pakipaki02.yaml` — Remove cmd override

Replaced:
```yaml
ic:
  cmd:
    strt: '@mesh.top'
```
With:
```yaml
ic: {}
```

The template already defines `strt` with `input: '@mesh.top'` and the full pipeline. The empty dict is required (bare `ic:` yields None and fails validation).

### 2. `src/rapid_gwm_build/templates/mf6_template.yaml` — Add return_arg to IC strt

Added `return_arg` to IC's `array_to_file` builtin, matching the pattern used by DIS botm and NPF k:

```yaml
return_arg:
    filename: '{filename}'
```

### 3. `examples/pakipaki02/client_code.py` — Add load validation

Updated to use `result.workspace` for the load path, providing dynamic validation:

```python
sim = flopy.mf6.MFSimulation.load(sim_ws=str(result.workspace))
```

## Verification

- 8 external files created: `pakipaki.ic_strt_layer0.txt` through `pakipaki.ic_strt_layer7.txt`
- `pakipaki.ic` contains `OPEN/CLOSE` references (not `INTERNAL`)
- `flopy.mf6.MFSimulation.load()` succeeds without errors
- 28/28 tests pass (2 pre-existing failures in `test_node_schema.py` unrelated)

## Files Modified

- `examples/pakipaki02/pakipaki02.yaml`
- `src/rapid_gwm_build/templates/mf6_template.yaml`
- `examples/pakipaki02/client_code.py`
