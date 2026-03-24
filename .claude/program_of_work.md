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
| 3 | Test Coverage | Stabilization | Not started | Week 3-4 |
| 4 | Template & Module Expansion | Feature | Not started | Week 4-5 |
| 5 | Demo Preparation | Polish | Not started | Week 5-7 |
| 6 | Parameter Filling (Design) | Feature/Design | Not started | Week 7-8 |

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

## Phase 3 — Test Coverage

**Goal:** Get tests running and cover the critical path.

### Phase 3.1 — Fix Test Infrastructure
- [ ] Fix `ModuleNotFoundError` — ensure package is importable in test environment
- [ ] Re-enable commented-out tests in `test_node_parser.py` and `test_node_schema.py`
- [ ] Verify all existing test scaffolding passes

### Phase 3.2 — Core Pipeline Tests
- [ ] Unit tests for `ConfigParser` (variable substitution, edge cases)
- [ ] Unit tests for `NodeParser` (each node type parsing)
- [ ] Unit tests for `GraphBuilder` (DAG construction, cycle detection, subgraphs)
- [ ] Unit tests for `NodeBuildEngine` (builder dispatch)
- [ ] Unit tests for `ProcessorEngine` (built-in, file-based, package-based resolution)

### Phase 3.3 — Integration Tests
- [ ] End-to-end test using `simple_freyburg` example YAML
- [ ] End-to-end test using `pakipaki02` example YAML
- [ ] Test the new `rmb.build()` API end-to-end
- [ ] Mark integration tests with `@pytest.mark.integration`

### Phase 3.4 — Processor Tests
- [ ] Test each of the 11 built-in processors individually
- [ ] Test processor pipeline chains
- [ ] Test custom processor loading (from file path)

---

## Phase 4 — Template & Module Expansion

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

## Phase 5 — Demo Preparation

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

## Phase 6 — Parameter Filling (Design Phase)

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
