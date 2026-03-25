# Development Log — `rapid-gwm-build` (`rmb`)

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
