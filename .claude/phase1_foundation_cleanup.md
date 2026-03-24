# Phase 1 — Foundation & Cleanup

**Date:** 2026-03-25
**Goal:** Remove dead code, fix tech debt, establish CI — make the codebase trustworthy.

---

## Phase 1.1 — Remove `ss/` Legacy Code

### Changes
- **Deleted** `src/rapid_gwm_build/ss/` — entire directory (17 files, ~2k lines of dead code)
- **Deleted** `src/rapid_gwm_build/nodes/ss_node_types.py` — only imported by ss/
- **Deleted** `examples/ss/` — legacy example data (pleasant/)
- **Updated** `.claude/CLAUDE.md` — removed `### ss/ Directory` section
- **Updated** `.claude/PRD.md` §8.5 — marked as resolved
- **Updated** `.claude/PRD.md` §9 — removed `ss/` tech debt row

### Verification
- `uv run ruff check .` passes
- `uv run pytest` passes
- No imports of ss/ found in active codebase

### Commit Message
```
Phase 1.1: Remove ss/ legacy code

- Delete src/rapid_gwm_build/ss/ directory (17 files, ~2k lines)
- Delete src/rapid_gwm_build/nodes/ss_node_types.py
- Delete examples/ss/ directory
- Update CLAUDE.md and PRD.md to reflect removal
```

---

## Phase 1.2 — Dependency Cleanup

### Changes
- **Removed** from core dependencies: cerberus, modflow-setup, netcdf4, setuptools, pyemu, pyshp, scikit-learn
- **Moved** to optional groups: debugpy → `[debug]`, dvc → `[data]`, ipykernel → `[notebook]`
- **Widened** flopy version pin: `flopy==3.9.2` → `flopy>=3.9.2`
- **Removed** HACK/TODO comments from pyproject.toml dependency lines

### Verification
- `uv sync` succeeds
- `uv run pytest` passes

### Commit Message
```
Phase 1.2: Clean up dependencies

- Remove 7 unused dependencies (cerberus, modflow-setup, netcdf4, setuptools, pyemu, pyshp, scikit-learn)
- Move debugpy, dvc, ipykernel to optional dependency groups
- Widen flopy version pin from ==3.9.2 to >=3.9.2
- Remove HACK/TODO comments from dependency lines
```

---

## Phase 1.3 — Bug Fixes & Small Debt

### Changes
- **Fixed** yorigin bug in `mf6_template.yaml:158` — changed `input: 'xorigin'` to `input: 'yorigin'`
- **Added** `slow` pytest marker to `pyproject.toml`
- **Fixed** Windows paths in `examples/simple_freyburg/freyburg_1lyr_stress.yaml` — made relative
- **Fixed** Windows paths in `examples/pakipaki02/national_test.yaml` — made relative, forward slashes
- **Cleaned** TODO/HACK comments in active code files
- **Removed** empty `# TODO` block at top of `mf6_template.yaml`
- **Cleaned** `#TODO utils?` comment in `node_parser.py:241`
- **Cleaned** `# Validate builtin pipelines #TODO` comment in `node_schemas.py:379`

### Verification
- `uv run ruff check .` passes
- `uv run pytest` passes

### Commit Message
```
Phase 1.3: Fix bugs and clean up tech debt

- Fix yorigin copy-paste bug in mf6_template.yaml (was using xorigin)
- Add missing 'slow' pytest marker to pyproject.toml
- Fix Windows-hardcoded paths in example YAMLs (make relative/portable)
- Clean up TODO/HACK comments in active codebase
```

---

## Phase 1.4 — CI/CD Setup

### Changes
- **Created** `.github/workflows/ci.yml` — GitHub Actions CI workflow
  - Triggers on push to `develop`/`master` and PRs
  - lint job: `uv sync --group dev && uv run ruff check .`
  - test job: `uv sync && uv run pytest`
  - Python 3.12, uses `astral-sh/setup-uv` action

### Commit Message
```
Phase 1.4: Add GitHub Actions CI

- Create .github/workflows/ci.yml
- Lint job (ruff check) and test job (pytest)
- Triggers on push to develop/master and PRs
- Python 3.12 with uv package manager
```

---

## PRD/Program of Work Updates

After all sub-phases:
- Updated `program_of_work.md` — marked Phase 1 tasks as complete
- Updated `PRD.md` — resolved relevant open questions and tech debt entries
- Updated `dev_log.md` with summary of Phase 1 work
