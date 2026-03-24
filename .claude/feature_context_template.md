# Feature Context Template

> Copy this template to `.claude/features/<feature_name>.md` and fill in the sections.
> This provides Claude with focused context for working on a specific processor or feature.

---

# Feature: [name]

## Target File(s)
- `src/rapid_gwm_build/processors/<subpackage>/<file>.py` — [brief role]
- `tests/test_processors/test_<name>.py` — unit tests

## Registered Name & Config
- Processor name: `name_in_registry`
- dependency_args: `{ 'arg_name': '@node.id' }`
- context_required: `true` / `false`

## What It Does
[1-2 sentence description of the processor's purpose and when it runs in the pipeline]

## Use Cases in YAML Config
```yaml
# Show how this processor appears in a user's YAML file
modules:
  <module_type>:
    data:
      <field_name>:
        value: <input_data>
        processor: <processor_name>
        # any additional kwargs the processor accepts
```

## Current State
- [ ] Code complete
- [ ] Tests written
- [ ] Feature context doc written
- [ ] Known issues: [describe any bugs, dead code, security concerns, etc.]

## Expected Behavior

### Inputs
| Parameter | Type | Source | Description |
|---|---|---|---|
| `data` | `np.ndarray` / `scalar` / `dict` | pipe input | [what the processor receives] |
| `dep_arg` | `type` | dependency_args | [auto-injected from DAG] |

### Outputs
| Condition | Output |
|---|---|
| Normal case | [describe return value] |
| Edge case | [describe behavior] |
| Error case | [describe exception raised] |

## Dependencies
- **Requires:** [other processors, mesh data, node references that must be built first]
- **Used by:** [which MODFLOW modules typically use this processor]

## Test Plan
- [ ] [specific test case 1 — e.g., "scalar input expanded to idomain shape"]
- [ ] [specific test case 2 — e.g., "raises ValueError on shape mismatch"]
- [ ] [specific test case 3 — e.g., "dict input with per-layer values"]

## Notes
[Any additional context: design decisions, historical reasons, related processors, etc.]
