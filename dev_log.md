# Development Log — `rapid-gwm-build` (`rmb`)

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
