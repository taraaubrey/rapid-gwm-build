# Phase — Mesh Schema Redesign (Type-Dispatched Input Validation)

Date: 2026-04-22
Branch: develop

## Summary

Replaced the flat `MESH_SCHEMA` with a thin dispatcher that delegates to a per-mesh-type schema. Introduced `STRUCTURED_MESH_SCHEMA` as the first concrete sub-schema. Renamed the geometry-source field `domain` → `extent` and the idomain data field `active_domain` → `domain` across the code, templates, processors, and example YAMLs. Extended the validator with three new rule types.

## Motivation

1. The old `MESH_SCHEMA` flagged `nlay`/`resolution`/`top`/`bottoms` as blanket-required, which is wrong for length-based and `delr`/`delc` paths.
2. No notion of `mesh_type` dispatch — future types (`unstructured`, `elements`, `areas`) had no plug-in point.
3. `freyburg_1lyr_stress.yaml` used `kind: structured` while the parser read `mesh_type` — user intent was silently dropped.
4. Field names overloaded `domain`: previously a geometry/extent source, but semantically better as the idomain. The geometry source is now `extent`.

## Changes

### Schema engine (`src/rapid_gwm_build/nodes/parse/node_schemas.py`)

- New `STRUCTURED_MESH_SCHEMA` with:
  - Required: `mesh_type`, `nlay`, `top`, `bottoms`.
  - Named `either_or` groups — exactly-one-of:
    - `extent_source`: `[extent]`, `[nrow, ncol]`, `[x_length, y_length]`.
    - `spacing_source`: `[resolution]`, `[dx, dy]`, `[delr, delc]`.
  - `mutually_exclusive` pairs for cross-rule guards (e.g. `delr`/`extent` cannot co-exist).
  - `renamed_fields` map gives friendly errors for `active_domain` / `kind`.
  - Extended `field_types`: added `xorigin`, `yorigin`, `angrot`, `x_length`, `y_length`, `dx`, `dy`, `mesh_type`.
- `MESH_TYPE_SCHEMAS` registry maps `'structured' → STRUCTURED_MESH_SCHEMA`. Placeholder comments for `UNSTRUCTURED_MESH_SCHEMA`, `ELEMENT_MESH_SCHEMA`, `AREA_MESH_SCHEMA`.
- `MESH_SCHEMA` is now a thin router: requires `mesh_type`, then `dispatch_on` forwards to the per-type schema.
- Split `validate_config` body into `_validate_against_schema` so the dispatcher can recurse with a sub-schema.
- New rule handlers added to the engine:
  - `dispatch_on` — look up `{field, map}`, re-run validator with the resolved sub-schema.
  - Named `either_or` groups (dict form) — exactly-one-of per group (list form preserved for backwards compatibility).
  - `mutually_exclusive` — list of pairs that cannot co-exist.
  - `renamed_fields` — friendly "X renamed to Y" error before required-field checks.

### Parser / config (`nodes/parse/node_parser.py`, `nodes/parse/config.py`)

- `_parse_mesh` `config_keys`: added `extent`, `angrot`, `x_length`, `y_length`, `dx`, `dy`; removed `domain`.
- `_parse_mesh` `data_keys`: `active_domain` → `domain`. Now `{'domain', 'top', 'bottoms'}`.
- `MESH_CONFIG_KEYS` / `MESH_DATA_KEYS` in `config.py` mirrored to the same sets.

### Builder (`nodes/builders/mesh.py`)

- Rename-only: `'domain' in config` → `'extent' in config`; `_get_data('domain', ...)` → `_get_data('extent', ...)`; error messages updated. No logic change — the length-based, `dx/dy`, `delr/delc`, and `angrot` paths still surface as a parse/build-time error (deferred to a follow-up phase).

### Template + processors (idomain reference updates)

- `templates/mf6_template.yaml`: `@mesh.active_domain` → `@mesh.domain`.
- `processors/data/checkdims_andor_tdis.py` (idomain dep).
- `processors/data/hierarchical_levels.py` (mesh dep).
- `processors/mf6/array_to_txtfile.py` (idomain dep).
- `processors/mesh/get_domain_boundary.py` (dependency_args value; kwarg name kept as `active_domain` to keep blast radius minimal).

### Example YAMLs migrated

- `examples/ss/simple_freyburg/freyburg_1lyr_stress.yaml`: `kind: structured` → `mesh_type: structured`; `active_domain:` → `domain:`.
- `examples/pakipaki02/pakipaki02.yaml`: added `mesh_type: structured`; geometry source `domain:` → `extent:`; idomain `active_domain:` → `domain:`; two cross-references `@mesh.active_domain` → `@mesh.domain`.
- `examples/pakipaki02/national_test.yaml`: added `mesh_type: structured`; `active_domain:` → `domain:`.
- `tests/test_data/sample_configs/valid_mesh.yaml`: added `mesh_type: structured`; `active_domain:` → `domain:`.

### Tests

- `tests/test_parsers/test_node_parser.py`: mesh fixture updated with `mesh_type`, `nrow`, `ncol`, and renamed `active_domain` → `domain`.
- `tests/test_parsers/test_mesh_schema.py` (new): 16 tests covering dispatcher behavior, missing/unknown `mesh_type`, renamed-field friendly errors, named-group exactly-one-of, mutually-exclusive pairs, scalar type checks.

## Verification

- `uv run ruff check .` — clean.
- `uv run --extra test pytest` — 44 passed, 2 pre-existing failures in `test_node_schema.py` unrelated to this phase.
- Parser round-trip: `pakipaki02.yaml` loads and `_parse_mesh` produces expected node set; `freyburg_1lyr_stress.yaml` mesh validates against the new dispatcher.

## Deferred (explicit non-goals this phase)

- Builder defaults for `xorigin`/`yorigin`/`angrot` (plan says these must reach the builder with `0` defaults — scoped to the next phase).
- Length-based (`x_length`/`y_length`), `dx`/`dy`, and `delr`/`delc` builder paths.
- Top-level YAML key rename `mesh:` → `domain:`.
- Placeholder schemas for `unstructured`/`elements`/`areas`.

## Git commit message (ready to paste)

```
feat(mesh-schema): type-dispatched mesh validation; rename active_domain→domain, domain→extent

Replace the flat MESH_SCHEMA with a thin dispatcher that routes on
`mesh_type` to a per-type schema. Introduce STRUCTURED_MESH_SCHEMA
with named either_or groups (extent_source, spacing_source) and
mutually_exclusive cross-rules, extending the validator engine with
`dispatch_on`, named-group either_or, `mutually_exclusive`, and
`renamed_fields` rule types.

Field renames (idomain semantics + geometry source clarity):
- active_domain -> domain (the idomain data array)
- domain -> extent (the geometry/extent source file)
- kind -> mesh_type (canonical YAML discriminator)

Propagated through the template, processor dependency_args, parser
key sets, builder lookups, and example YAMLs. Builder logic is
rename-only; new mesh-config paths (x_length/y_length, dx/dy,
delr/delc, angrot defaults) are deferred to a follow-up phase.

Add 16 negative tests in tests/test_parsers/test_mesh_schema.py
covering the new validation rules.
```
