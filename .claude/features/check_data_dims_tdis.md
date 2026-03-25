# Feature: check_data_dims_tdis

## Target File(s)
- `src/rapid_gwm_build/processors/data/checkdims_andor_tdis.py` — dimension validation/transformation for MF6 spatial data
- `tests/test_processors/test_check_data_dims_tdis.py` — 28 unit tests

## Registered Name & Config
```python
@register_processor(
    "check_data_dims_tdis",
    dependency_args={
        "nper": "@modules.tdis.nper",
        "idomain": "@mesh.active_domain",
    },
)
```

## What It Does
Central dimension validation/transformation for all spatial data flowing through the MF6 pipeline. Called from the template for every module parameter that needs grid-conforming data (dis.top, dis.botm, npf.k, wel.stress_period_data, etc.).

Transformation matrix:

| data | exp_dims=2 | exp_dims=3 | exp_dims=4 |
|------|-----------|-----------|-----------|
| **scalar** | `np.full((nrow,ncol))` | `np.full((nlay,nrow,ncol))` | `np.full((nper,nlay,nrow,ncol))` |
| **list** | convert to ndarray, then as array | same | same |
| **2D** | validate shape, return | tile to nlay layers | tile to 3D, wrap nper (nper=1 only) |
| **3D** | **Error** (can't reduce) | validate shape, return | wrap nper (nper=1 only) |
| **4D** | **Error** | **Error** | validate shape, return |

Key rules:
- Scalars always expand to target shape (any nper)
- Upward promotion allowed only when nper=1 (single stress period = unambiguous)
- nper>1 + wrong dims = error (user must provide correctly shaped data)
- Downward reduction is never allowed

## Current State (living updates)
- [x] Code complete
- [x] Tests written (28 tests, all passing)
- [x] Feature context doc written
- [x] Known issues: None

## Expected Behavior

### Inputs
| Parameter | Type | Source | Description |
|---|---|---|---|
| `data` | `np.ndarray` / `scalar` / `list` / `dict` | pipe input | data to validate/transform |
| `nper` | `int` | dependency_args | number of stress periods, auto-injected from DAG |
| `idomain` | `np.ndarray` (3D) | dependency_args | active domain array, auto-injected from DAG |
| `expected_dims` | `int` (2, 3, or 4) | processor kwargs | target dimensionality |
| `**kwargs` | any | processor kwargs | extra kwargs (ignored, for template flexibility) |

### Outputs
| Condition | Output |
|---|---|
| Normal case | ndarray with shape matching expected_dims and grid dimensions |
| Dict input | dict with each value conformed individually |
| Reduction attempt | ValueError |
| nper>1 promotion | ValueError |
| Wrong spatial dims | ValueError |

## Dependencies
- **Requires:** `@modules.tdis.nper`, `@mesh.active_domain`
- **Used by:** all MF6 module data parameters (dis.top, dis.botm, npf.k, etc.)

## Test Plan
- [x] Scalar expansion (int/float → 2D/3D/4D, value preservation, nper>1)
- [x] Array identity (ndim==expected_dims → validate and return)
- [x] Array promotion (2D→3D, 2D→4D, 3D→4D, nper=1 only)
- [x] Reduction errors (3D→2D, 4D→3D, 4D→2D)
- [x] nper>1 promotion errors
- [x] Shape validation errors
- [x] Dict input (arrays, mixed types)
- [x] List input conversion
- [x] Edge cases (invalid expected_dims, **kwargs passthrough)
