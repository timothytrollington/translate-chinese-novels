#!/usr/bin/env python3
"""CLI entrypoint that runs the translation pipeline."""
from __future__ import annotations

import argparse
import logging
from pathlib import Path

from translate_novels.config import load_config
from translate_novels.pipeline import run_pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Update translated chapters")
    parser.add_argument(
        "--config",
        type=Path,
        help="Optional path to a JSON file with pipeline configuration",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (DEBUG, INFO, WARNING, ERROR)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))

    config = load_config(args.config)
    result = run_pipeline(config)

    logging.info(
        "Processed %d new chapter(s); skipped %d entries", len(result.processed), result.skipped
    )


if __name__ == "__main__":
    main()
