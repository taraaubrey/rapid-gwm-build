# Schema & Config Design Improvements

**Status:** Complete  
**Date:** 2026-04-17

## Problem

The schema and config design had several quality issues:

1. **Naming convention inconsistency** — the `drn` module in `mf6_template.yaml` had an unquoted `func` value while all other modules used quoted strings.

2. **Falsy-value default bug** — `node_data.py` used `if not self.get(key)` to detect missing values, which incorrectly overwrote valid falsy values (`False`, `0`, `[]`) with schema defaults.

3. **Late processor validation** — invalid processor names were only caught at runtime (deep in the build), not at parse time. A typo in a processor name surfaced as a cryptic `TypeError: 'NoneType' is not callable`.

4. **Error path readability** — `validate_config_strict` displayed context paths as Python lists (`['modules', 'dis', 'top']`) instead of the YAML-native dot-notation (`modules.dis.top`).

5. **No scalar type checking for mesh fields** — `nlay: "five"` or `resolution: -10` passed schema validation silently and only failed at runtime with opaque errors.

6. **Defaults are invisible** — users had no way to inspect what effective parameters would be passed to flopy functions without actually running a build.

## Changes

### A. Template consistency (`mf6_template.yaml`)

Added quotes to the `drn` module `func` value:

```yaml
# Before
func: flopy.mf6.ModflowGwfdrn

# After
func: 'flopy.mf6.ModflowGwfdrn'
```

### B1. Falsy-value default fix (`nodes/node_data.py`)

```python
# Before
if not self.get(key):
    self.metadata.update({key: default_value})

# After — use `is None` so falsy-but-valid values (False, 0, []) are not overwritten
if self.get(key) is None:
    self.metadata.update({key: default_value})
```

### B2. Parse-time processor validation (`nodes/parse/node_parser.py`)

Added validation in `_parse_pipe` before the build step:

```python
# Built-in processors must be registered
if built_in and processor not in BUILTIN_PROCESSORS:
    raise ValueError(
        f"Unknown built-in processor '{processor}' at '{context_str}'. "
        f"Available: {list(BUILTIN_PROCESSORS.keys())}"
    )

# Custom processors must use 'module.function' dot-notation
elif processor not in BUILTIN_PROCESSORS and '.' not in processor:
    raise ValueError(
        f"Invalid processor name '{processor}' at '{context_str}'. "
        f"Must be a registered built-in name or use 'module.function' dot-notation. "
        f"Available built-in processors: {list(BUILTIN_PROCESSORS.keys())}"
    )
```

### B3. Dot-notation error paths (`nodes/parse/node_schemas.py`)

`validate_config_strict` now normalises context to dot-notation:

```python
# Before
context_str = f"for {context}" if context else ""

# After
if isinstance(context, (list, tuple)):
    context_str = f"at '{'.'.join(str(p) for p in context)}'"
elif context:
    context_str = f"at '{context}'"
else:
    context_str = ""
```

Error message example:
```
# Before: Invalid mesh configuration for ['modules', 'dis', 'top']: ...
# After:  Invalid mesh configuration at 'modules.dis.top': ...
```

### C. Scalar type checking (`nodes/parse/node_schemas.py`)

Added `field_types` validation rule to `MESH_SCHEMA` and wired it into the `validate_config` method:

```python
MESH_SCHEMA = NodeSchema(
    ...
    validation_rules={
        ...
        'field_types': {
            'nlay':       (int,),
            'resolution': (int, float),
            'crs':        (int, str),
            'nrow':       (int,),
            'ncol':       (int,),
        },
        ...
    }
)
```

Now catches at parse time:
```yaml
mesh:
  nlay: "five"    # ValueError: Field 'nlay' must be of type (int), got str ('five')
  resolution: -10 # passes (range validation is future work)
```

### D. Config inspection (`simulation.py`)

Added `Simulation.show_resolved_config()` method. Returns the fully-merged effective `cmd` for each module, with a `sources` map showing where each value came from:

```python
sim = Simulation.from_yaml("model.yaml")
resolved = sim.show_resolved_config()

# Example output:
{
    "sim": {
        "func": "flopy.mf6.MFSimulation",
        "effective_cmd": {
            "sim_name": "pakipaki02",
            "sim_ws": "examples/models/pakipaki02",
            "version": "mf6",
        },
        "sources": {
            "sim_name": "user_cmd",
            "sim_ws": "user_cmd",
            "version": "user_cmd",
        }
    },
    "tdis": {
        "func": "flopy.mf6.ModflowTdis",
        "effective_cmd": {
            "time_units": "DAYS",    # user_cmd overrides template default
            "nper": 1,               # from template default_build
        },
        "sources": {
            "time_units": "user_cmd",
            "nper": "template",
        }
    },
    ...
}
```

Priority (lowest → highest): function defaults < template `build_dependencies` < user `cmd`.

## Pre-existing Test Failures (not introduced by this work)

`tests/test_parsers/test_node_schema.py` had 2 failing tests before this change:

- `test_validate_config_input`: expects nested input-dict content validation (e.g. `{'input': {'data': 25}}` should fail), but that validation is commented out in `INPUT_SCHEMA`.
- `test_validate_config`: passes `all_fields` kwarg to `validate_config` which is not a recognised `NodeSchema` attribute.

## Remaining Gaps (future work)

- **Range validation** — `nlay: -1` or `resolution: 0` pass type checking but should be rejected.
- **Nested input-dict validation** — `{'input': {'data': 25}}` (missing `src`) should be caught at parse time.
- **File existence pre-check** — opt-in `validate_files: true` flag to check input paths exist before building.
- **`sim_ws` duplication** — users must specify the workspace path in both `simulation.setup.ws` and `modules.sim.cmd.sim_ws`. These could be auto-wired.
- **Two required-field registries** — `NODE_TYPE_SCHEMAS` in `node_data.py` and `NodeSchemas` in `node_schemas.py` both define required fields and could drift.

## Files Modified

| File | Change |
|---|---|
| `src/rapid_gwm_build/templates/mf6_template.yaml` | Quote `drn.func` value |
| `src/rapid_gwm_build/nodes/node_data.py` | Fix falsy-value default check |
| `src/rapid_gwm_build/nodes/parse/node_parser.py` | Validate processor names at parse time |
| `src/rapid_gwm_build/nodes/parse/node_schemas.py` | Dot-notation error paths; `field_types` rule and validation |
| `src/rapid_gwm_build/simulation.py` | Add `show_resolved_config()` |
| `dev_log.md` | Updated |
