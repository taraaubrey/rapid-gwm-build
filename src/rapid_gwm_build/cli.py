"""CLI entrypoint for rmb — rapid groundwater model builder."""

import argparse
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def main(argv=None):
    """Main CLI entrypoint."""
    parser = argparse.ArgumentParser(
        prog="rmb",
        description="Rapid groundwater model builder — build MODFLOW 6 models from YAML configs.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- rmb build ---
    build_parser = subparsers.add_parser(
        "build",
        help="Build model from YAML config",
    )
    build_parser.add_argument(
        "yaml_path",
        type=Path,
        help="Path to the YAML config file",
    )
    build_parser.add_argument(
        "--ws",
        type=Path,
        default=None,
        help="Override workspace directory",
    )
    build_parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable node caching",
    )
    build_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output",
    )
    build_parser.add_argument(
        "--input",
        action="append",
        dest="extra_inputs",
        metavar="FILE",
        help="Additional YAML input file(s) to merge (can be repeated)",
    )
    build_parser.add_argument(
        "--input-ext",
        metavar="EXT",
        help="Load all files with this extension from the config directory (e.g. .yaml)",
    )
    build_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and build graph without executing the build",
    )
    build_parser.add_argument(
        "--graph",
        action="store_true",
        help="Visualize the DAG and exit",
    )

    # --- rmb validate ---
    val_parser = subparsers.add_parser(
        "validate",
        help="Validate YAML config without building",
    )
    val_parser.add_argument(
        "yaml_path",
        type=Path,
        help="Path to the YAML config file",
    )
    val_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output",
    )

    args = parser.parse_args(argv)
    _configure_logging(getattr(args, "verbose", False))

    if args.command == "build":
        return _handle_build(args)
    elif args.command == "validate":
        return _handle_validate(args)


def _configure_logging(verbose: bool):
    """Set up logging for CLI use."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(levelname)s: %(message)s",
    )
    # Suppress noisy third-party loggers
    for name in ("matplotlib", "rasterio", "fiona", "gridit"):
        logging.getLogger(name).setLevel(logging.WARNING)


def _collect_extra_inputs(args) -> list[Path] | None:
    """Collect extra input files from --input and --input-ext flags."""
    extras = list(args.extra_inputs or [])

    if args.input_ext:
        ext = args.input_ext if args.input_ext.startswith(".") else f".{args.input_ext}"
        config_dir = args.yaml_path.parent
        for f in sorted(config_dir.glob(f"*{ext}")):
            if f.resolve() != args.yaml_path.resolve() and f not in extras:
                extras.append(f)

    return extras if extras else None


def _handle_build(args) -> int:
    """Handle the 'rmb build' command."""
    from .api import build, create_simulation
    from .errors import BuildError, ConfigError

    yaml_path = args.yaml_path
    if not yaml_path.exists():
        logger.error("Config file not found: %s", yaml_path)
        return 1

    extra_inputs = _collect_extra_inputs(args)

    try:
        if args.dry_run or args.graph:
            sim = create_simulation(
                yaml_path,
                ws=args.ws,
                cache=not args.no_cache,
                extra_inputs=extra_inputs,
            )
            info = sim.validate()
            logger.info("Validation passed: %d nodes, %d edges", info["node_count"], info["edge_count"])
            for ntype, count in info["node_types"].items():
                logger.info("  %s: %d", ntype, count)

            if args.graph:
                sim.visualize_graph(subgraph=True)

            return 0

        result = build(
            yaml_path,
            ws=args.ws,
            cache=not args.no_cache,
            extra_inputs=extra_inputs,
        )

        if result.success:
            logger.info("Build successful — %d nodes built", len(result.built_nodes))
            logger.info("Output: %s", result.workspace)
            return 0
        else:
            logger.error("Build completed with errors:")
            for err in result.errors:
                logger.error("  %s", err)
            return 1

    except ConfigError as exc:
        logger.error("Configuration error: %s", exc)
        return 1
    except BuildError as exc:
        logger.error("Build error: %s", exc)
        return 1
    except Exception as exc:
        logger.error("Unexpected error: %s", exc)
        if getattr(args, "verbose", False):
            import traceback
            traceback.print_exc()
        return 1


def _handle_validate(args) -> int:
    """Handle the 'rmb validate' command."""
    from .api import validate
    from .errors import ConfigError, ValidationError

    yaml_path = args.yaml_path
    if not yaml_path.exists():
        logger.error("Config file not found: %s", yaml_path)
        return 1

    try:
        info = validate(yaml_path)
        logger.info("Validation passed")
        logger.info("  Nodes: %d", info["node_count"])
        logger.info("  Edges: %d", info["edge_count"])
        logger.info("  Workspace: %s", info["workspace"])
        for ntype, count in info["node_types"].items():
            logger.info("  %s: %d", ntype, count)
        return 0
    except (ConfigError, ValidationError) as exc:
        logger.error("Validation failed: %s", exc)
        return 1
    except Exception as exc:
        logger.error("Unexpected error: %s", exc)
        if getattr(args, "verbose", False):
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
