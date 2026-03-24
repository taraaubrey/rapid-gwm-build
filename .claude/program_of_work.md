# Program of Work — `rapid-gwm-build` (`rmb`)

> **Living document.** Update phase statuses, add sub-phases, and refine scope as work progresses.
> Tracks implementation phases for the `rmb` project, alternating between stabilization and feature work.

**Created:** 2026-03-25
**Target milestone:** Architecture & extensibility demo (~May 2026)

---

## Phase Summary

| Phase | Focus | Type | Status | Target |
|---|---|---|---|---|
| 1 | Foundation & Cleanup | Stabilization | **Complete** | 2026-03-25 |
| 2 | Public API & CLI | Feature | **Complete** | 2026-03-25 |
| 3.0 | Test Infrastructure & Core Fixes | Stabilization | Not started | — |
| 3.1 | `check_data_dims_tdis` processor | Feature | Not started | — |
| 3.2 | `simple_math` processor | Feature | Not started | — |
| 3.3 | `hierarchical_levels` processor | Feature | Not started | — |
| 3.4 | `top_only` / `specific_layer` processors | Feature | Not started | — |
| 3.5 | Mesh processors (4 processors) | Feature | Not started | — |
| 3.6 | `array_to_file` processor | Feature | Not started | — |
| 4 | Template & Module Expansion | Feature | Deferred | — |
| 5 | Demo Preparation | Polish | Deferred | — |
| 6 | Parameter Filling (Design) | Feature/Design | Deferred | — |

---

## Phase 1 — Foundation & Cleanup

**Goal:** Remove dead code, fix tech debt, establish CI — make the codebase trustworthy.

### Phase 1.1 — Remove `ss/` Legacy Code
- [x] Delete `src/rapid_gwm_build/ss/` directory entirely
- [x] Delete `src/rapid_gwm_build/nodes/ss_node_types.py`
- [x] Delete `examples/ss/` legacy example data
- [x] Update PRD.md §8.5 — mark decision as resolved
- [x] Update PRD.md §9 — remove `ss/` tech debt entry

### Phase 1.2 — Dependency Cleanup
- [x] Remove unused dependencies: cerberus, modflow-setup, netcdf4, setuptools, pyemu, pyshp, scikit-learn
- [x] Move debugpy → `[debug]`, dvc → `[data]`, ipykernel → `[notebook]` optional groups
- [x] Widen flopy pin: `==3.9.2` → `>=3.9.2`
- [x] Remove HACK/TODO comments from dependency lines
- [ ] Consider optional extras: `rmb[mf6]` for flopy dependencies (deferred)

### Phase 1.3 — Bug Fixes & Small Debt
- [x] Fix `yorigin` copy-paste bug in `mf6_template.yaml:158`
- [x] Add missing `slow` pytest marker to `pyproject.toml`
- [x] Fix Windows-hardcoded paths in example YAMLs (make relative/portable)
- [x] Clean up TODO/HACK comments in active codebase

### Phase 1.4 — CI/CD Setup
- [x] Create GitHub Actions workflow (`.github/workflows/ci.yml`)
  - Lint (`ruff check`) and test (`pytest`) jobs
  - Triggers on push to develop/master and PRs
  - Python 3.12 with `astral-sh/setup-uv`

**Commit message template:**
```
Phase 1.X: [description]

- [bullet points of changes]
```

---

## Phase 2 — Public API & CLI

**Goal:** Replace manual client code with a clean, demonstrable entry point.

### Phase 2.1 — High-Level Python API
- [x] Create `rmb.build(yaml_path)` function — `api.py:build()`
- [x] Encapsulate the current client code pattern — `simulation.py:Simulation` class
- [x] Handle `Path.mkdir` and workspace setup internally
- [x] Return a meaningful result object — `SimulationResult` dataclass
- [ ] Update PRD.md §8.2 — mark API design as resolved

### Phase 2.2 — CLI Entrypoint
- [x] Add CLI via `argparse`: `rmb build model.yaml` — `cli.py`
- [x] Register as console script in `pyproject.toml`
- [x] Support key options: `--ws` override, `--no-cache`, `--verbose`, `--input`, `--input_ext`
- [x] Add `rmb validate model.yaml` command

### Phase 2.3 — Error Messages & User Experience
- [x] Add user-friendly error messages — custom exceptions in `errors.py`
- [x] Add progress output during build — logging in `rmb_runner.py` and `simulation.py`
- [x] Add `--dry-run` / `--graph` flags to CLI

### Phase 2.4 — Cleanup & Documentation
- [x] Replace manual client code with new API (`examples/pakipaki02/client_code.py`)
- [x] Add debug runner (`examples/pakipaki02/debug_run.py`)
- [x] Rewrite README.md with CLI reference and Python API usage
- [x] Fix `build_context.reset()` bug (clear_context missed mesh_grid/mesh_id)

---

## Phase 3 — Processor Test Infrastructure & Core Fixes

**Goal:** Get tests running, set up shared fixtures, and fix known cross-cutting bugs so that per-processor phases can proceed cleanly.

### Phase 3.0 — Test Infrastructure
- [ ] Fix `ModuleNotFoundError` — ensure package is importable in test environment (`uv sync --group dev`)
- [ ] Re-enable commented-out tests in `test_node_parser.py` and `test_node_schema.py`
- [ ] Create shared test fixtures in `tests/conftest.py`:
  - Mock `idomain` (2D and 3D numpy arrays)
  - Mock mesh config dict (nlay, nrow, ncol, resolution, crs)
  - Mock `sim_ws` temp directory
  - Mock `tdis` perioddata list
- [ ] Verify all existing test scaffolding passes
- [ ] Unit tests for `ProcessorEngine` (built-in, file-based, package-based resolution)

### Phase 3.1 — `check_data_dims_tdis` (data validation)
> **File:** `processors/data/checkdims_andor_tdis.py`
> **Registry:** `check_data_dims_tdis`, dependency_args: `{idomain: @mesh.active_domain, tdis: @modules.tdis.perioddata}`

- [ ] Fix/complete processor (audit current implementation)
- [ ] Unit tests: scalar→array expansion, shape validation against idomain, tdis wrapping, dict input handling, error cases
- [ ] Create feature context doc (`.claude/features/check_data_dims_tdis.md`)

### Phase 3.2 — `simple_math` (expression evaluator)
> **File:** `processors/data/simple_math.py`
> **Registry:** `simple_math`, no dependency_args

- [ ] Address `eval()` security concern — restrict to safe math operations
- [ ] Unit tests: expression parsing, variable substitution, numpy array inputs, error on invalid expressions
- [ ] Create feature context doc

### Phase 3.3 — `hierarchical_levels` (layer interpolation)
> **File:** `processors/data/hierarchical_levels.py`
> **Registry:** `hierarchical_levels`, dependency_args (TBD — check implementation)

- [ ] Audit current state — determine if placeholder or functional
- [ ] Implement or document intended behavior
- [ ] Unit tests
- [ ] Create feature context doc

### Phase 3.4 — `top_only` / `specific_layer` (layer selection)
> **File:** `processors/data/specific_layer_selection.py`
> **Registry:** `top_only` (no deps), `specific_layer` (no deps)

- [ ] Clean up dead code paths
- [ ] Unit tests: 3D input extraction, keep_dims parameter, scalar passthrough, out-of-bounds index
- [ ] Create feature context doc

### Phase 3.5 — Mesh Processors
> **Files:** `processors/mesh/from_structured_mesh.py`, `get_domain_boundary.py`, `to_3d.py`, `make_inactive.py`
> **Registry:** `from_structured_mesh` (dep: `@mesh.config`), `domain_boundary` (dep: `@mesh.active_domain`), `tile_to_nlay` (dep: `@mesh.nlay`), `make_inactive` (no deps)

- [ ] Fix unreachable code in `domain_boundary`
- [ ] Fix in-place mutation in `make_inactive` (should return new array)
- [ ] Unit tests for `from_structured_mesh`: mesh config → structured grid
- [ ] Unit tests for `domain_boundary`: active domain → boundary cells
- [ ] Unit tests for `tile_to_nlay`: 2D array → 3D tiled to nlay
- [ ] Unit tests for `make_inactive`: mask modification by layer/row/col
- [ ] Create feature context docs (one per processor or combined)

### Phase 3.6 — `array_to_file` (MF6 output writer)
> **File:** `processors/mf6/array_to_txtfile.py`
> **Registry:** `array_to_file`, dependency_args: `{sim_ws: @modules.sim.sim_ws, idomain: @mesh.active_domain}`

- [ ] Clean up dead code paths
- [ ] Unit tests: array format output, table format output, by_layer, by_stress_period, file path construction
- [ ] Create feature context doc

---

## Phase 4 — Template & Module Expansion *(deferred)*

**Goal:** Broaden MODFLOW 6 support and demonstrate extensibility.

### Phase 4.1 — New Module Support
- [ ] Implement `sto` (storage) module in template
- [ ] Implement `sfr` (streamflow routing) module in template
  - **Unknown:** What level of SFR complexity to support initially?
- [ ] Implement `rch` (non-array recharge) module in template
- [ ] Add tests for each new module

### Phase 4.2 — Transient Stress Period Support
- [ ] Design how multi-period data flows through the pipeline
  - **Unknown:** How should time-varying boundary conditions be specified in YAML?
- [ ] Implement transient data handling in relevant builders
- [ ] Add transient example YAML
- [ ] Test transient build end-to-end

### Phase 4.3 — Template Extensibility
- [ ] Allow users to supply custom template YAML (extend or override `mf6_template.yaml`)
- [ ] Document how to add a new module type
- [ ] Create a "how to extend rmb" guide or example
- [ ] Update PRD.md §8.4 — mark template extensibility as resolved

---

## Phase 5 — Demo Preparation *(deferred)*

**Goal:** Polish for architecture & extensibility demo (~May 2026).

### Phase 5.1 — Working Examples
- [ ] Ensure `pakipaki02` example runs end-to-end via `rmb build`
- [ ] Ensure `simple_freyburg` example runs end-to-end via `rmb build`
- [ ] Create a minimal "hello world" example (simplest possible model)
- [ ] All examples use relative paths and work cross-platform

### Phase 5.2 — Architecture Documentation
- [ ] Create architecture diagram (pipeline flow, node types, extension points)
- [ ] Document the processor registration pattern with a worked example
- [ ] Document the builder registration pattern with a worked example
- [ ] Update README.md with current API usage and installation instructions

### Phase 5.3 — Demo Script
- [ ] Prepare a walkthrough showing:
  1. YAML config → DAG visualization
  2. `rmb build` execution with progress output
  3. Adding a custom processor (extensibility)
  4. Adding a custom module template entry (extensibility)
- [ ] Ensure all demo steps work reliably

---

## Phase 6 — Parameter Filling (Design Phase) *(deferred)*

**Goal:** Design the parameter filling feature (PRD §7.2) — implementation in a later program.

### Phase 6.1 — Resolve Open Design Questions
- [ ] Answer PRD §8.1 questions (source model types, referencing, build timing, etc.)
- [ ] Decide: which source model types to support first?
- [ ] Decide: how does spatial interpolation/resampling work between grids?
- [ ] Decide: priority chain (`explicit value → source_model → default`)?

### Phase 6.2 — Technical Design Document
- [ ] Write a design doc covering:
  - Data flow through the DAG for parameter filling
  - New node type(s) needed, if any
  - Processor requirements
  - YAML syntax proposal
- [ ] Review with stakeholders
- [ ] Update PRD.md with finalized design

### Phase 6.3 — Proof of Concept
- [ ] Implement the simplest case (e.g., reference another rmb YAML)
- [ ] Validate the design works with the existing pipeline
- [ ] Identify gaps for full implementation

---

## Unknowns & Decision Points

These items need input before the relevant phase can proceed. They are also flagged inline above.

| # | Question | Blocking | Status |
|---|---|---|---|
| U1 | What does `modflow-setup` dependency provide? Audit imports before removing | Phase 1.2 | Open |
| U2 | What reads NetCDF in the pipeline? | Phase 1.2 | Open |
| U3 | Does codebase use flopy APIs that changed after 3.9.2? | Phase 1.2 | Open |
| U4 | What level of SFR complexity to support initially? | Phase 4.1 | Open |
| U5 | How should transient BCs be specified in YAML? | Phase 4.2 | Open |

---

## How to Use This Document

- **Starting a phase:** Read the phase, enter plan mode, create a phase-specific plan
- **Completing a phase:** Update status in the summary table, create commit message, update `dev_log.md`
- **Adding work:** Add new sub-phases (e.g., Phase 2.4) or new phases as needed
- **Resolving unknowns:** Fill in the answer, update the blocking phase's tasks

---

*Last updated: 2026-03-25*
