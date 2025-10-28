"""Command line entry point for the translation pipeline."""
from __future__ import annotations

import argparse
from pathlib import Path

from .logging_utils import MetadataLogger
from .model_client import MockTranslationModel
from .translation_pipeline import TranslationPipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Translate Chinese novel chapters to English.")
    parser.add_argument("source", type=Path, help="Path to the Chinese source text file")
    parser.add_argument("output", type=Path, help="Directory to place the translated output")
    parser.add_argument("--log", type=Path, help="Optional path to a JSONL metadata log file")
    parser.add_argument("--batch-size", type=int, default=5, help="Number of segments per API request")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    logger = MetadataLogger(args.log) if args.log else None
    model = MockTranslationModel()
    pipeline = TranslationPipeline(model=model, logger=logger)
    pipeline.translate_file(args.source, args.output, batch_size=args.batch_size)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
