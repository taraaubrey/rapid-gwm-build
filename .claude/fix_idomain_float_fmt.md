# Fix: idomain saved as floats causes flopy MFDataException

## Problem

When building models with external array files, integer arrays like `idomain` were written in scientific notation (`0.000000000000000000e+00`) by `np.savetxt`. When flopy later read these files expecting integer values, it raised a `ValueError` / `MFDataException`.

**Error flow:**
1. `idomain` (int dtype, values 0/1) passes through `check_data_dims_tdis` — dtype preserved correctly
2. `array_to_file` → `_save_array` → `np.savetxt(path, data)` — writes floats (default `fmt='%.18e'`)
3. flopy reads external file for `idomain`, expects integers → **ValueError**

## Fix

**Approach:** Template-driven dtype control — the dtype is specified in the template where module schemas are defined, not detected at runtime.

### Template change (`mf6_template.yaml`)

Added `dtype: int` to `idomain`'s `array_to_file` entry:

```yaml
idomain:
    builtin:
        - array_to_file:
            dtype: int          # <-- new
            output_type: 'array'
            by_layer: True
```

### Processor change (`array_to_txtfile.py`)

- `_to_array` accepts `dtype='float'` param, resolves to `fmt` string (`'%d'` for int, `'%.18e'` for float)
- `_save_array` accepts `fmt='%.18e'` param, passes directly to `np.savetxt`

## Impact

- Fixes CHD (and any other package) construction failures caused by float-formatted idomain files
- No change to float array behavior (default `dtype='float'`)
- Future integer arrays can be configured by adding `dtype: int` in the template
- Works for both `by_layer=True` (2D slices) and full array paths
