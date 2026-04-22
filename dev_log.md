# Development Log — `rapid-gwm-build` (`rmb`)

---

## 2026-04-22 — Mesh Schema Redesign (Type-Dispatched Validation)

**What:** Replaced the flat `MESH_SCHEMA` with a type-dispatched design. `MESH_SCHEMA` is now a thin router that requires `mesh_type` and delegates full validation to a per-type schema via a `MESH_TYPE_SCHEMAS` map. Added `STRUCTURED_MESH_SCHEMA` as the first concrete sub-schema with named `either_or` groups (`extent_source`, `spacing_source`), `mutually_exclusive` cross-rules, and `renamed_fields` for friendly rename errors.

**Field renames:**
- `active_domain` → `domain` (now the idomain data array)
- `domain` → `extent` (now strictly the geometry source file)
- `kind` → `mesh_type` (canonical YAML discriminator — freyburg previously silently dropped the user's declaration)

**Changes made:**

- **`src/rapid_gwm_build/nodes/parse/node_schemas.py`**: Added `STRUCTURED_MESH_SCHEMA`, `MESH_TYPE_SCHEMAS` registry, rewrote `MESH_SCHEMA` as dispatcher. Split `validate_config` into `_validate_against_schema` so the dispatcher can recurse. Added four new rule handlers: `dispatch_on`, named-group `either_or` (dict form, exactly-one-of per group — list form preserved for legacy), `mutually_exclusive`, `renamed_fields`. Extended `field_types` with `xorigin`, `yorigin`, `angrot`, `x_length`, `y_length`, `dx`, `dy`, `mesh_type`.
- **`src/rapid_gwm_build/nodes/parse/node_parser.py`**: `_parse_mesh` `config_keys` now includes `extent`, `angrot`, `x_length`, `y_length`, `dx`, `dy` (removed `domain`); `data_keys` renamed to `{'domain', 'top', 'bottoms'}`.
- **`src/rapid_gwm_build/nodes/parse/config.py`**: `MESH_CONFIG_KEYS` / `MESH_DATA_KEYS` mirrored to the same sets.
- **`src/rapid_gwm_build/nodes/builders/mesh.py`**: Rename-only — `'domain' in config` / `_get_data('domain', ...)` / error messages → `'extent'`. Builder logic unchanged; new mesh-config paths (length-based, `dx/dy`, `delr/delc`, `angrot` defaults) remain deferred.
- **`src/rapid_gwm_build/templates/mf6_template.yaml`**: `@mesh.active_domain` → `@mesh.domain`.
- **Processor idomain references updated** in `processors/data/checkdims_andor_tdis.py`, `processors/data/hierarchical_levels.py`, `processors/mf6/array_to_txtfile.py`, `processors/mesh/get_domain_boundary.py`.
- **Example YAMLs migrated**: `examples/ss/simple_freyburg/freyburg_1lyr_stress.yaml`, `examples/pakipaki02/pakipaki02.yaml` (includes `domain` → `extent` rename for the geometry shapefile), `examples/pakipaki02/national_test.yaml`, `tests/test_data/sample_configs/valid_mesh.yaml`.
- **`tests/test_parsers/test_node_parser.py`**: fixture updated with `mesh_type`, `nrow`, `ncol`, renamed `active_domain` → `domain`.
- **`tests/test_parsers/test_mesh_schema.py`** (new): 16 negative/positive tests covering the dispatcher, missing/unknown `mesh_type`, friendly rename errors, named-group validation, mutually-exclusive cross-rules, and scalar type checks.

**Verification:** `ruff check .` clean. `pytest` 44 passed; 2 pre-existing failures in `test_node_schema.py` are unrelated to this work (confirmed via stash). Parser round-trip on `pakipaki02.yaml` produces the expected node set under the new schema.

**Deferred to follow-up phase:** builder defaults for `xorigin`/`yorigin`/`angrot` (plan says these must reach the builder with `0` defaults); builder implementations for length-based, `dx/dy`, and `delr/delc` paths; top-level YAML key rename `mesh:` → `domain:`; concrete schemas for `unstructured`/`elements`/`areas`.

**Phase doc:** `.claude/phase_mesh_schema_redesign.md` (includes ready-to-paste git commit message).

---

## 2026-04-17 — GitBook Setup

**What:** Set up GitBook documentation site structure for the project, with Git sync support.

**Changes made:**

- **`.gitbook.yaml`** (new): Root config pointing GitBook to `docs/` as the content root with `SUMMARY.md` as the TOC.
- **`docs/README.md`** (new): GitBook landing page — brief overview of `rmb` and a link to the YAML Schema reference.
- **`docs/SUMMARY.md`** (new): GitBook table of contents — home page and YAML Schema reference entry.
- **`docs/yaml_schema.md`**: No changes — already in the right location, now referenced via `SUMMARY.md`.

**Next step (manual):** Connect the repo to GitBook.com via GitHub integration (New Space → Import from GitHub → select `docs/` as root).

**Files created:**
- `.gitbook.yaml`
- `docs/README.md`
- `docs/SUMMARY.md`

---

## 2026-04-17 — Schema Doc: Clarify `data` vs `inputs` keywords

**What:** Updated `docs/yaml_schema.md` to make the distinction between `data:` and `inputs:` explicit throughout the document.

**Changes made:**

- **Top-level structure**: Updated inline comment on `data:` to flag it as a module-only keyword.
- **New section — Module Block Structure**: Added dedicated section explaining that `data:` is only valid as a direct child of a module block (not in `mesh:` or field definitions), and that `cmd:` holds scalar flopy kwargs. Includes a worked example.
- **Form 2 renamed**: "Data block (named multi-source)" → "Multi-source field (inputs form)" to remove the misleading `data` label from the `inputs:` form.
- **Form 2 rules**: Added explicit statement that multiple `inputs:` entries **require** a block-level `pipeline:`.
- **Rules table**: Added two new rows — `data:` is module-only, and multiple `inputs:` require a pipeline.
- **Examples 10–13 retitled**: Example 10 now reads "Module `data:` block — independent named field entries"; examples 11–13 use "Multi-source field" prefix and include the pipeline-required note.
- **Schema Summary split**: Separated into "Module block structure" and "Field forms" subsections, with `REQUIRED` annotation on the pipeline in Form 2.

**Files modified:**
- `docs/yaml_schema.md`

---

## 2026-04-17 — Schema & Config Design Improvements

**What:** Review and hardening of the schema, config validation, and defaults system across the library.

**Changes made:**

- **[A] Template consistency** (`mf6_template.yaml`): Added quotes to the `drn` module's `func` value (`flopy.mf6.ModflowGwfdrn`) — all other modules were already quoted, this was the lone unquoted outlier.

- **[B1] Falsy-value default bug** (`nodes/node_data.py`): Fixed `_apply_type_schema` to use `if self.get(key) is None` instead of `if not self.get(key)`. The old check would incorrectly overwrite falsy-but-valid values like `False`, `0`, or `[]` with defaults.

- **[B2] Processor name validation** (`nodes/parse/node_parser.py`): Processor names are now validated at parse time in `_parse_pipe`. Built-in processors must be registered in `BUILTIN_PROCESSORS`; custom processors must use `module.function` dot-notation. Previously, an invalid name would only surface as a cryptic runtime error deep in the build.

- **[B3] Error path dot-notation** (`nodes/parse/node_schemas.py`): `validate_config_strict` now normalises list-style context paths (e.g. `['modules', 'dis', 'top']`) to YAML-style dot-notation (`'modules.dis.top'`) in all error messages. Previously the raw Python list was shown.

- **[C] Scalar type checking** (`nodes/parse/node_schemas.py`): Added a `field_types` rule to `MESH_SCHEMA` and wired it into `validate_config`. Catches type errors on scalar mesh fields (`nlay: int`, `resolution: int|float`, `crs: int|str`, `nrow/ncol: int`) at parse time instead of silently producing wrong results at runtime.

- **[D] Config inspection** (`simulation.py`): Added `Simulation.show_resolved_config()`. Returns a dict keyed by module name showing the effective `cmd` parameters that would be used at build time, with a `sources` map indicating whether each value came from the user `cmd`, template `build_dependencies`, or function-signature defaults.

**Tests:** 28 passing, 2 pre-existing failures in `test_node_schema.py` (not introduced by this work — nested `input` dict validation and `all_fields` kwarg not yet implemented).

**Pre-existing test notes:**
- `test_validate_config_input`: expects `{'input': {'data': 25, 'resampling': 'min'}}` to fail; nested input-dict content validation is not yet implemented.
- `test_validate_config`: passes `all_fields` kwarg to `validate_config` which is not a recognised `NodeSchema` attribute.

**Files modified:**
- `src/rapid_gwm_build/templates/mf6_template.yaml`
- `src/rapid_gwm_build/nodes/node_data.py`
- `src/rapid_gwm_build/nodes/parse/node_parser.py`
- `src/rapid_gwm_build/nodes/parse/node_schemas.py`
- `src/rapid_gwm_build/simulation.py`

---

## 2026-04-02 — YAML Schema Design and Documentation

**What:** Designed and documented the canonical YAML schema for the user-editable config file.

**Design decisions:**
- `src` is always a plain string (path, scalar, `@ref`) — never a dict
- `load:` holds load-time options (e.g. resampling) alongside `src:` at the field level
- `metadata:` holds parameterisation bounds (`lb`, `ub`)
- `pipeline:` is an ordered list of processors applied after loading
- `data:` block enables named multi-source inputs, each with their own `src`/`load`/`pipeline`; the block can have its own combining `pipeline:` — fully recursive
- Flat form is preferred over a single-entry `data:` block
- Shorthand (`field: value`) collapses the flat form for simple scalars, paths, and `@ref`s

**Files created:** `docs/yaml_schema.md`

---

## 2026-03-25 — Fix CI: pytest not installed in test job

**What:** CI test job failed with `Failed to spawn: pytest` because `uv sync` was run without the `test` extra.

**Root cause:** `pytest` is declared in `[project.optional-dependencies] test`, not in core dependencies. The CI test job ran bare `uv sync` which only installs core deps.

**Fix:** Changed `uv sync` → `uv sync --extra test` in `.github/workflows/ci.yml` (line 33).

**Files modified:** `.github/workflows/ci.yml`

---

## 2026-03-25 — Fix CI Ruff Lint Failures

**What:** CI failed on `uv run ruff check .` with 22 errors across three files after push.

**Root cause:** Two issues:
1. `pipeline.py:39` referenced undefined variable `linput` instead of `level_input`
2. `notebooks/` and `refs/` directories (reference/scratch files) were being linted unnecessarily

**Fix:**
1. Fixed `linput` → `level_input` in `src/rapid_gwm_build/nodes/parse/blocks/pipeline.py:39`
2. Added `[tool.ruff] exclude = ["notebooks", "refs"]` to `pyproject.toml`

**Verification:** `uv run ruff check .` returns 0 errors.

**Files modified:** `src/rapid_gwm_build/nodes/parse/blocks/pipeline.py`, `pyproject.toml`

---

## 2026-03-25 — Fix: IC strt External File Writing & Add Load Validation

**What:** Fixed the IC package's `strt` data being written incorrectly, causing `flopy.mf6.MFSimulation.load()` to fail with "Expected data size 24400 but only found 0".

**Root cause:** In `pakipaki02.yaml`, `strt: '@mesh.top'` was specified in the IC `cmd` section. The node parser excludes template `build_dependency` entries that match user `cmd` keys, so the template's `strt` pipeline (`check_data_dims_tdis` → `array_to_file`) was completely bypassed. Flopy received a raw 2D array instead of 3D data with external file references.

**Fix:**
1. Removed `cmd.strt` override from `pakipaki02.yaml` — the template already defines the full pipeline with `input: '@mesh.top'`
2. Added `return_arg` to IC strt's `array_to_file` in `mf6_template.yaml` for consistency with DIS botm and NPF k
3. Updated `client_code.py` to validate the build via `MFSimulation.load()` using `result.workspace`

**Verification:** 8 external `strt` files created, `pakipaki.ic` uses `OPEN/CLOSE` references, load succeeds. 28/28 tests pass.

**Files modified:** `examples/pakipaki02/pakipaki02.yaml`, `src/rapid_gwm_build/templates/mf6_template.yaml`, `examples/pakipaki02/client_code.py`
**Files created:** `.claude/fix_ic_strt_external_files.md`

---

## 2026-03-25 — Fix: idomain saved as floats causes flopy MFDataException

**What:** Fixed `_save_array` in `array_to_txtfile.py` writing integer arrays (e.g. `idomain`) in scientific notation (`0.000000000000000000e+00`), causing flopy to fail with `MFDataException` when parsing the external text file as integers.

**Root cause:** `np.savetxt` defaults to `fmt='%.18e'`, so integer arrays like `idomain` (values 0, 1) were written as floats. When flopy later read the file expecting integers, it raised a `ValueError`.

**Fix:** Template-driven dtype control. Added `dtype: int` to the `idomain` entry in `mf6_template.yaml`. The `array_to_file` processor now accepts a `dtype` param (default `'float'`) which determines the `fmt` string passed to `_save_array`. This keeps the dtype knowledge in the template where module schemas are defined, rather than relying on runtime detection.

**Files modified:**
- `src/rapid_gwm_build/processors/mf6/array_to_txtfile.py` — `_to_array` accepts `dtype` param, resolves to `fmt`, passes to `_save_array`
- `src/rapid_gwm_build/templates/mf6_template.yaml` — `idomain.array_to_file` entry gets `dtype: int`

**Files created:** `.claude/fix_idomain_float_fmt.md`

---

## 2026-03-25 — Phase 3.2: Lightweight Node Context for Processor Debugging

**What:** Added pre-build logging and error wrapping in `RMBRunner` so that processor failures always identify which DAG node triggered them.

**Changes:**
1. **Pre-build log line** — `logger.info("Building node: %s [%s]", node_id, ntype)` before each build call, so the last log entry before a crash identifies the node
2. **Error wrapping** — try/except around builder execution re-raises with `[node_id]` prefix, preserving original exception type and traceback chain

**Files modified:** `src/rapid_gwm_build/rmb_runner.py`
**Files created:** `.claude/phase3_node_debug_context.md`

**Verification:** 28/28 tests pass, ruff clean, no regressions (2 pre-existing failures in `test_node_schema.py` unrelated).

---

## 2026-03-25 — Phase 3.1.1: Document & Improve PipeBuilder

**What:** Added docstrings and minor quality improvements to `PipeBuilder` (`nodes/builders/pipe.py`).

**Changes:**
1. **Docstrings** — Added class-level, `build()`, `_extract_config_data()`, and `fetch_data()` docstrings
2. **Removed dead code** — `if processor_name == 'top_only': pass` no-op block (was lines 34-35)
3. **Fixed mutation side effect** — `processor_args_cfg` was mutated via `.pop('context_path')` on `node_data`'s internal dict. Now copies with `dict()` before popping
4. **Simplified context_path handling** — Replaced if/else branching with conditional dict insertion + single `execute()` call
5. **Explicit None check** — Changed `elif pipe_input` to `elif pipe_input is not None` in `fetch_data`

**Files modified:** `src/rapid_gwm_build/nodes/builders/pipe.py`

**Verification:** 28/28 processor tests pass, no regressions (2 pre-existing failures in `test_node_schema.py` unrelated).

---

## 2026-03-25 — Phase 3.1: Fix & Complete `check_data_dims_tdis` Processor

**What:** Rewrote the `check_data_dims_tdis` processor to fix 6 bugs and implement the full dimension transformation matrix.

**Bugs fixed:**
1. **Broken dimension promotion logic** — `else` branch always created 3D→4D regardless of `expected_dims`. Replaced with explicit `(ndim, expected_dims)` routing.
2. **`dtype=int` in `_number_to_array`** — scalar floats (k=1e-5) were expanded with int dtype. Now uses `type(value)` to preserve int/float.
3. **`*kwargs` → `**kwargs`** — was capturing positional args as tuple; extra keyword args caused TypeError.
4. **No list→ndarray conversion** — list inputs hit TypeError. Now converts via `np.asarray()`.
5. **numpy imported inside every helper** — moved to module-level import.
6. **`_add_tdis` on 2D data produced 3D not 4D** — `reshape((1, *data.shape))` on 2D `(nrow,ncol)` → 3D. Replaced with `np.newaxis` slicing on properly promoted 3D data.

**Architecture:** No changes to registration/plumbing. Kept `nper` dependency (not `perioddata`).

**Files modified:**
- `src/rapid_gwm_build/processors/data/checkdims_andor_tdis.py` — full rewrite
- `tests/conftest.py` — added `idomain_3d` shared fixture
- `.claude/features/check_data_dims_tdis.md` — updated status

**Files created:**
- `tests/test_processors/__init__.py`
- `tests/test_processors/test_check_data_dims_tdis.py` — 28 tests (all passing)

**Verification:** 28/28 tests pass, ruff clean, no regressions (2 pre-existing failures in `test_node_schema.py` unrelated).

---

## 2026-03-25 — Restructure Program of Work (Phase 3+)

**What:** Restructured Phase 3+ from category-focused (test coverage, template expansion) to feature-focused (one sub-phase per processor). Created a reusable feature context template for future Claude sessions.

**Why:** Phases 1-2 are complete. The next priority is fixing, testing, and documenting individual processors — the foundation for usable documentation and reliable builds.

**Changes:**
- Rewrote Phase 3 into 7 sub-phases (3.0–3.6), each targeting a specific processor or group:
  - 3.0: Test infrastructure & shared fixtures
  - 3.1: `check_data_dims_tdis` — data validation for MF6 packages
  - 3.2: `simple_math` — expression evaluator (eval() security concern)
  - 3.3: `hierarchical_levels` — layer interpolation (audit needed)
  - 3.4: `top_only` / `specific_layer` — layer selection
  - 3.5: Mesh processors (`from_structured_mesh`, `domain_boundary`, `tile_to_nlay`, `make_inactive`)
  - 3.6: `array_to_file` — MF6 output writer
- Phases 4-6 retained but marked as deferred
- Created `.claude/feature_context_template.md` — reusable template for describing a feature to Claude
- Created `.claude/features/` directory for per-processor context docs

**Files modified:** `.claude/program_of_work.md`
**Files created:** `.claude/feature_context_template.md`, `.claude/features/` (directory)

---

## 2026-03-25 — Bugfix: Empty processor/builder registries

**What:** Fixed `BUILTIN_PROCESSORS` and `BUILDER_REGISTRY` being empty at runtime, causing `ValueError: Processor 'from_structured_mesh' is not registered`.

**Root cause:** The `@register_processor` and `@register_builder` decorators only fire when their modules are imported. Nothing in the import chain triggered the auto-discovery in `processors/__init__.py` and `nodes/builders/__init__.py`, so the registries stayed empty.

**Fix:** Added auto-discovery imports at the bottom of `registries.py`:
```python
import rapid_gwm_build.nodes.builders  # populates BUILDER_REGISTRY
import rapid_gwm_build.processors      # populates BUILTIN_PROCESSORS
```

This ensures any code that imports from `registries` gets pre-populated registries.

**Files modified:** `src/rapid_gwm_build/registries.py`

---

## 2026-03-25 — Phase 2: Public API & CLI (Complete)

**What:** Added a clean Python API, CLI entrypoint, debug runner, and rewrote the README.

### Phase 2.1 — High-Level Python API
- Created `Simulation` class (`simulation.py`) — encapsulates the full pipeline (parse → graph → build → write)
- Created `api.py` with convenience functions: `build()`, `validate()`, `create_simulation()`
- Created `SimulationResult` dataclass (`simulation_result.py`) — returned after builds
- Created custom exceptions (`errors.py`): `RMBError`, `ConfigError`, `BuildError`, `ValidationError`
- Updated `__init__.py` to export public API: `from rapid_gwm_build import build, create_simulation, validate`
- Fixed `BuildContext.reset()` — existing `clear_context()` missed `mesh_grid`/`mesh_id`
- Replaced `print()` with `logging` in `rmb_runner.py`

### Phase 2.2 — CLI Entrypoint
- Created `cli.py` with argparse: `rmb build model.yaml` and `rmb validate model.yaml`
- Supports: `--ws`, `--no-cache`, `--verbose`, `--input`, `--input-ext`, `--dry-run`, `--graph`
- Registered console script in `pyproject.toml`: `rmb = "rapid_gwm_build.cli:main"`

### Phase 2.3 — Error Messages & UX
- User-friendly error wrapping in `Simulation.build()` with custom exceptions
- `--dry-run` flag: parse + build graph without executing
- `--graph` flag: visualize DAG and exit
- Progress logging throughout pipeline stages

### Phase 2.4 — Cleanup & Documentation
- Replaced 30-line manual pipeline in `examples/pakipaki02/client_code.py` with 3-line API call
- Created `examples/pakipaki02/debug_run.py` — step-through debug runner with VS Code launch.json snippet
- Updated `examples/simple_freyburg/client_code.py` with new API (note: YAML still needs format update)
- Rewrote `README.md` — installation, CLI reference, Python API, debugging, architecture overview

**Files created:** `api.py`, `simulation.py`, `simulation_result.py`, `errors.py`, `cli.py`, `debug_run.py`
**Files modified:** `__init__.py`, `build_context.py`, `rmb_runner.py`, `pyproject.toml`, `README.md`, `client_code.py` (both examples), `program_of_work.md`

---

## 2026-03-25 — Phase 1: Foundation & Cleanup (Complete)

**What:** Removed dead code, cleaned dependencies, fixed bugs, and added CI.

### Phase 1.1 — Remove ss/ Legacy Code
- Deleted `src/rapid_gwm_build/ss/` (17 files, ~2k lines) — confirmed zero imports from active code
- Deleted `src/rapid_gwm_build/nodes/ss_node_types.py`
- Deleted `examples/ss/` (pleasant/ example data)
- Updated CLAUDE.md and PRD.md §8.5, §9

### Phase 1.2 — Dependency Cleanup
- Removed 7 unused dependencies: cerberus, modflow-setup, netcdf4, setuptools, pyemu, pyshp, scikit-learn
- Moved debugpy, dvc, ipykernel to optional dependency groups (`[debug]`, `[data]`, `[notebook]`)
- Widened flopy pin: `==3.9.2` → `>=3.9.2`
- Removed HACK/TODO comments from pyproject.toml

### Phase 1.3 — Bug Fixes & Small Debt
- Fixed yorigin copy-paste bug in `mf6_template.yaml:158` (was using `xorigin` input)
- Added `slow` pytest marker to pyproject.toml
- Fixed Windows-hardcoded paths in `freyburg_1lyr_stress.yaml` and `national_test.yaml` (relative paths, forward slashes)
- Cleaned TODO/HACK comments in mf6_template.yaml, node_parser.py, node_schemas.py

### Phase 1.4 — CI/CD Setup
- Created `.github/workflows/ci.yml` (lint + test jobs, Python 3.12, uv)

**Files changed:**
- Deleted: `src/rapid_gwm_build/ss/` (17 files), `nodes/ss_node_types.py`, `examples/ss/`
- Modified: `pyproject.toml`, `mf6_template.yaml`, `node_parser.py`, `node_schemas.py`, `freyburg_1lyr_stress.yaml`, `national_test.yaml`, `CLAUDE.md`, `PRD.md`, `program_of_work.md`
- Created: `.github/workflows/ci.yml`, `.claude/phase1_foundation_cleanup.md`

**Note:** 31 pre-existing ruff errors remain (not introduced by Phase 1). Tests have a pre-existing `ModuleNotFoundError` (package not installed in dev mode).

---

## 2026-03-25 — Program of Work Created

**What:** Created the program of work document (`.claude/program_of_work.md`) and updated CLAUDE.md with a reference to it.

**Details:**
- Defined 6 phases alternating between stabilization and feature work
- Phase 1: Foundation & Cleanup (remove ss/, fix deps, CI)
- Phase 2: Public API & CLI (rmb.build(), CLI entrypoint)
- Phase 3: Test Coverage (fix tests, core pipeline tests, integration tests)
- Phase 4: Template & Module Expansion (sto, sfr, transient)
- Phase 5: Demo Preparation (examples, docs, demo script)
- Phase 6: Parameter Filling Design (design only, implementation deferred)
- Identified 5 unknowns/decision points that need input before specific sub-phases
- Target milestone: Architecture & extensibility demo (~May 2026)

**Files changed:**
- `.claude/program_of_work.md` — created (living roadmap document)
- `.claude/CLAUDE.md` — added reference to program of work
- `dev_log.md` — created (this file)
