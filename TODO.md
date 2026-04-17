# TODO — `rapid-gwm-build`

Tracked gaps from the schema & config design review (2026-04-17).
Each item below has a corresponding `# TODO` comment at the relevant code location.

---

## Validation

### Range validation for mesh scalar fields
**File:** [src/rapid_gwm_build/nodes/parse/node_schemas.py](src/rapid_gwm_build/nodes/parse/node_schemas.py) — `MESH_SCHEMA.validation_rules['field_types']`

Type checking for `nlay`, `resolution`, etc. is in place, but range constraints are not.
Values like `nlay: -1` or `resolution: 0` pass silently.

**What to build:**
- Add a `field_constraints` rule to `NodeSchema` (parallel to `field_types`)
- In `validate_config`, apply constraints after type checks
- Constraints: `nlay > 0`, `resolution > 0`, `ncol > 0`, `nrow > 0`

```python
# Example schema addition:
'field_constraints': {
    'nlay':       lambda v: v > 0,
    'resolution': lambda v: v > 0,
    'nrow':       lambda v: v > 0,
    'ncol':       lambda v: v > 0,
}
```

---

### Nested input-dict validation (missing `src` key)
**File:** [src/rapid_gwm_build/nodes/parse/node_schemas.py](src/rapid_gwm_build/nodes/parse/node_schemas.py) — `INPUT_SCHEMA.validation_rules['nested_validation']`

When an `input` value is a dict, the schema does not validate its contents.
`{'input': {'data': 25, 'resampling': 'min'}}` (missing `src`) passes silently and produces wrong results.

**What to build:**
- Uncomment and implement the `'input': {'nest_type': 'str', 'schema': 'value'}` nested validation
- Define a `VALUE_SCHEMA` that requires `src` when the value is a dict
- Also fixes the pre-existing `test_validate_config_input` test failure

---

### File existence pre-check
**File:** [src/rapid_gwm_build/nodes/parse/node_parser.py](src/rapid_gwm_build/nodes/parse/node_parser.py) — `_parse_value`

Input file paths are not checked for existence at parse time — a missing file is only caught deep in execution when the file is opened.

**What to build:**
- After extracting `value` in `_parse_value`, if `value` is a string path (not an `@ref`, not a scalar number/bool), optionally check `Path(value).exists()`
- Gate behind `CONFIG['validate_files']` (default `False`) so it doesn't add overhead to every parse
- Raise a `ConfigError` with the node context path if the file is missing

---

## Config Design

### `sim_ws` duplication
**File:** [src/rapid_gwm_build/simulation.py](src/rapid_gwm_build/simulation.py) — `Simulation.from_yaml`

Users must specify the workspace directory twice:
- `simulation.setup.ws` — used by rmb to create the output directory
- `modules.sim.cmd.sim_ws` — passed to `flopy.mf6.MFSimulation`

Both should point to the same path, but there is no auto-wiring.

**What to build:**
- In `from_yaml`, after parsing config, check if `modules.sim.cmd.sim_ws` is absent
- If so, populate it from `simulation.setup.ws`
- Users who need different values can still override explicitly

---

## Architecture

### Two required-field registries
**File:** [src/rapid_gwm_build/nodes/node_data.py](src/rapid_gwm_build/nodes/node_data.py) — `NODE_TYPE_SCHEMAS`  
**File:** [src/rapid_gwm_build/nodes/parse/node_schemas.py](src/rapid_gwm_build/nodes/parse/node_schemas.py) — `NodeSchemas`

`required` fields are declared in `NODE_TYPE_SCHEMAS` (used by `NodeData.__post_init__` for runtime checks) and also in `NodeSchema.required_fields` (used by `validate_config` for parse-time checks). These can drift.

**What to build:**
- Decide on a single source of truth: `NodeSchemas` for parse-time validation, `NODE_TYPE_SCHEMAS` for runtime defaults only
- Remove `'required'` keys from `NODE_TYPE_SCHEMAS` (keep only `'defaults'`)
- Add tests that verify the two systems stay in sync, or eliminate the duplication entirely
