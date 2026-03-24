"""Debug runner for pakipaki02 — step through each pipeline stage.

Usage:
    - Run directly:  uv run python examples/pakipaki02/debug_run.py
    - With debugpy:  uv run python -m debugpy --listen 5678 --wait-for-client examples/pakipaki02/debug_run.py
    - In VS Code:    Use the launch.json config below, then set breakpoints anywhere.

VS Code launch.json snippet:
{
    "name": "Debug pakipaki02",
    "type": "debugpy",
    "request": "launch",
    "program": "${workspaceFolder}/examples/pakipaki02/debug_run.py",
    "cwd": "${workspaceFolder}",
    "justMyCode": false
}
"""

import logging

from rapid_gwm_build.build_context import build_context
from rapid_gwm_build.build_registry import build_registry
from rapid_gwm_build.config import CONFIG
from rapid_gwm_build.graph_builder import GraphBuilder
from rapid_gwm_build.node_engine import NodeBuildEngine
from rapid_gwm_build.nodes.parse.node_parser import NodeParser
from rapid_gwm_build.parsers.config_parser import ConfigParser
from rapid_gwm_build.registries import BUILDER_REGISTRY
from rapid_gwm_build.rmb_runner import RMBRunner

# Configure logging — DEBUG level so you see everything
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("debug_run.log"),
    ],
)
# Suppress noisy third-party loggers
for _name in ("matplotlib", "rasterio", "fiona", "gridit"):
    logging.getLogger(_name).setLevel(logging.WARNING)


def main():
    # ---- Settings ----
    input_yaml = "examples/pakipaki02/pakipaki02.yaml"
    CONFIG["cache_enabled"] = False
    CONFIG["cache_nodes"] = False

    # ---- Stage 1: Parse config ----
    # Set a breakpoint here to inspect the raw config
    config = ConfigParser.parse(input_yaml)
    template = config.get("template", {})
    sim_cfg = config.get("simulation", {}).copy()
    setup = sim_cfg.pop("setup", {})
    print(f"Setup: {setup}")

    # ---- Stage 2: Parse nodes ----
    # Set a breakpoint here to inspect individual node parsing
    parser = NodeParser(sim_template=template)
    for key, val in sim_cfg.items():
        print(f"Parsing: {key}")
        parser.parse_node(node_type=key, config=val)

    all_nodes = parser.get_all_nodes()
    print(f"Total nodes: {len(all_nodes)}")

    # ---- Stage 3: Build graph ----
    # Set a breakpoint here to inspect the DAG
    graph_builder = GraphBuilder(all_nodes)
    G = graph_builder.build()
    module_graph = graph_builder.get_subgraph(ntype="module")
    mesh_graph = graph_builder.get_subgraph(ntype="mesh_config")
    print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    print(f"Module subgraph: {module_graph.number_of_nodes()} nodes")
    print(f"Mesh subgraph: {mesh_graph.number_of_nodes()} nodes")

    # ---- Stage 4: Execute build ----
    # Set a breakpoint here to step through node builds
    build_registry.clear_all()
    build_context.reset()

    engine = NodeBuildEngine(registry=BUILDER_REGISTRY)
    runner = RMBRunner(graph=module_graph, mesh_graph=mesh_graph, engine=engine)
    runner.run()

    # ---- Stage 5: Inspect results ----
    # Set a breakpoint here to inspect build results
    for node_id in build_registry.list_built_nodes():
        result = build_registry.result_from_id(node_id)
        print(f"  {node_id}: success={result.success}, type={type(result.data).__name__}")

    print("Done.")


if __name__ == "__main__":
    main()
