# Phase 3.2: Lightweight Node Context for Processor Debugging

**Status:** Complete
**Date:** 2026-03-25

## Problem

When a processor fails during DAG execution, error messages and log output don't indicate *which node* triggered the failure. Debugging requires manually tracing the graph to find the offending node.

## Solution

Two small changes to `RMBRunner._compile_graph_node_data` in `rmb_runner.py`:

### 1. Pre-build log line (line 58)

```python
logger.info("Building node: %s [%s]", node_id, ntype)
```

Logs node ID and type *before* each build, so the last log entry before any crash identifies the node.

### 2. Error wrapping with node context (lines 60-66)

```python
try:
    if CONFIG.get('cache_nodes', True):
        result = execute_node_build(builder, node)
    else:
        result = builder.build(node)
except Exception as exc:
    raise type(exc)(f"[{node_id}] {exc}") from exc
```

Re-raises any exception with the node ID prepended, preserving the original exception type and traceback chain.

## What this gives you

- **Normal run:** log shows `Building node: modules.rcha-rf.data.recharge [pipe]` before each node
- **On error:** exception message is prefixed with `[modules.rcha-rf.data.recharge]`
- **Zero changes** to processors, builders, or NodeData — fully non-invasive

## Files modified

- `src/rapid_gwm_build/rmb_runner.py` — 2 changes (pre-build log + try/except wrapper)

## Verification

- 28/28 tests pass (2 pre-existing failures in `test_node_schema.py` unrelated)
- ruff lint clean
