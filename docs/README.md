# rmb — Rapid Model Builder

`rmb` (`rapid-gwm-build`) is a Python package for building groundwater model input files from a user-defined YAML config.

It parses the config, constructs a directed acyclic graph (DAG) of processing nodes, and executes them in topological order to generate model files — currently MODFLOW 6 via flopy.

---

## How it works

1. Write a YAML config describing your simulation, mesh, and model packages.
2. `rmb` parses the config into a DAG of typed nodes.
3. Nodes are executed in dependency order, passing outputs between processors.
4. Model files are written to your specified output directory.

---

## Reference

- [YAML Schema](yaml_schema.md) — full field reference and use-case examples
