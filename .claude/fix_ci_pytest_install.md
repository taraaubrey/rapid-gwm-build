# Fix CI: pytest not installed in test job

## Problem
CI test job fails with `Failed to spawn: pytest` because `uv sync` only installs core dependencies, and `pytest` is declared under `[project.optional-dependencies] test`.

## Change
**File:** `.github/workflows/ci.yml` (line 33)

```diff
- - run: uv sync
+ - run: uv sync --extra test
```

## Verification
Push to `develop` and confirm CI test job finds and runs pytest successfully.
