# Phase 3.1: Fix & Complete `check_data_dims_tdis` Processor

## Summary
Rewrote the central dimension validation/transformation processor that all MF6 spatial data flows through. Fixed 6 bugs ranging from critical (broken promotion logic, wrong output dimensions) to medium (dtype loss, kwargs syntax) to low (no list support, style).

## Bugs Fixed

| # | Bug | Fix |
|---|-----|-----|
| 1 | Broken dimension promotion — `else` branch always 3D→4D | Explicit `(ndim, expected_dims)` routing via `_conform_array` |
| 2 | `dtype=int` for scalar floats | `np.full(..., dtype=type(value))` preserves int/float |
| 3 | `*kwargs` captures positional args | Changed to `**kwargs` |
| 4 | Lists raise TypeError | Added `np.asarray()` conversion |
| 5 | numpy imported inside helpers | Module-level `import numpy as np` |
| 6 | `_add_tdis` 2D→3D not 4D | Replaced with `data[np.newaxis, ...]` on pre-promoted 3D |

## Files Changed

| File | Change |
|---|---|
| `src/rapid_gwm_build/processors/data/checkdims_andor_tdis.py` | Full rewrite — 4 helpers replaced with 3 cleaner ones |
| `tests/test_processors/__init__.py` | New (empty, package marker) |
| `tests/test_processors/test_check_data_dims_tdis.py` | New — 28 tests across 9 categories |
| `tests/conftest.py` | Added `idomain_3d` fixture |
| `.claude/features/check_data_dims_tdis.md` | Updated to reflect completed state |

## Test Results
```
28 passed in 0.27s
ruff: All checks passed!
Full suite: 28 passed, 2 failed (pre-existing, unrelated)
```

## Commit Message
```
Phase 3.1: Fix & complete check_data_dims_tdis processor

Rewrite the central dimension validation/transformation processor,
fixing 6 bugs: broken promotion logic, int dtype for floats, *kwargs
syntax, no list support, repeated numpy imports, and wrong output
dimensions from _add_tdis. Add 28 unit tests covering scalar expansion,
array identity/promotion, reduction errors, nper>1 guards, shape
validation, dict/list inputs, and edge cases.
```
