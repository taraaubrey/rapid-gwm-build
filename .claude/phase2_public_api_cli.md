# Phase 2 — Public API & CLI

## Summary

Replaced manual client code (6+ imports, ~30 lines of orchestration) with a clean Python API and CLI entrypoint.

## Changes

### New Files

| File | Purpose |
|---|---|
| `src/rapid_gwm_build/api.py` | Public functions: `build()`, `validate()`, `create_simulation()` |
| `src/rapid_gwm_build/simulation.py` | `Simulation` class — full pipeline orchestrator |
| `src/rapid_gwm_build/simulation_result.py` | `SimulationResult` dataclass |
| `src/rapid_gwm_build/errors.py` | Custom exceptions: `RMBError`, `ConfigError`, `BuildError`, `ValidationError` |
| `src/rapid_gwm_build/cli.py` | argparse CLI: `rmb build`, `rmb validate` |
| `examples/pakipaki02/debug_run.py` | Step-through debug runner with VS Code support |

### Modified Files

| File | Change |
|---|---|
| `__init__.py` | Export `build`, `create_simulation`, `validate` |
| `build_context.py` | Added `reset()` method (fixes bug: `clear_context` missed mesh state) |
| `rmb_runner.py` | Replaced `print()` with `logging.getLogger(__name__).info()` |
| `pyproject.toml` | Added `[project.scripts] rmb = "rapid_gwm_build.cli:main"` |
| `README.md` | Full rewrite: CLI reference, Python API, debugging guide |
| `examples/pakipaki02/client_code.py` | Simplified to 3-line API call |
| `examples/simple_freyburg/client_code.py` | Updated to use new API |

## Usage

### CLI
```bash
rmb build examples/pakipaki02/pakipaki02.yaml --verbose
rmb validate examples/pakipaki02/pakipaki02.yaml
rmb build model.yaml --dry-run
rmb build model.yaml --graph
```

### Python API
```python
from rapid_gwm_build import build
result = build("examples/pakipaki02/pakipaki02.yaml")

# Or interactive:
from rapid_gwm_build import create_simulation
sim = create_simulation("model.yaml")
sim.build()
sim.write()
```

### Debug
```bash
uv run python examples/pakipaki02/debug_run.py
uv run python -m debugpy --listen 5678 --wait-for-client examples/pakipaki02/debug_run.py
```

## Bug Fixes

- `BuildContext.clear_context()` did not reset `mesh_grid` or `mesh_id` — added `reset()` method that clears all state

## Commit Message

```
Phase 2: Public API & CLI

- Add Simulation class encapsulating full pipeline (parse → graph → build → write)
- Add public API: build(), validate(), create_simulation()
- Add CLI entrypoint: rmb build/validate with --ws, --no-cache, --verbose, --dry-run, --graph
- Add custom exceptions: RMBError, ConfigError, BuildError, ValidationError
- Add SimulationResult dataclass for build output
- Add debug runner (examples/pakipaki02/debug_run.py) with VS Code debugpy support
- Fix BuildContext.reset() to clear mesh state
- Replace print() with logging in RMBRunner
- Simplify example client code to use new API
- Rewrite README with CLI reference, Python API, and debugging guide
- Register console script in pyproject.toml
```
