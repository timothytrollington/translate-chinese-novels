"""Command-line entry points for the translation workflow."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

from .config import DEFAULT_CONFIG, TranslationConfig, ensure_directories


def translate_directory(config: TranslationConfig) -> None:
    """Placeholder translation routine that copies files to the output directory.

    Replace this function with calls to your preferred translation provider.
    """

    ensure_directories(config)

    for source in _iter_chapter_files(config.input_dir):
        destination = config.output_dir / source.name
        destination.write_text(
            f"# TRANSLATED\n\n(This is a placeholder translation of {source.name}.)\n",
            encoding="utf-8",
        )


def refresh_directory(config: TranslationConfig) -> None:
    """Placeholder for re-running translations with updated settings."""

    translate_directory(config)


def _iter_chapter_files(directory: Path) -> Iterable[Path]:
    """Yield supported chapter files from ``directory``."""

    for path in sorted(directory.glob("*.txt")):
        if path.is_file():
            yield path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Translate Chinese novel chapters for personal study.")
    parser.add_argument("command", choices={"translate", "refresh"}, help="Pipeline action to perform.")
    parser.add_argument("--input", dest="input_dir", type=Path, default=DEFAULT_CONFIG.input_dir)
    parser.add_argument("--output", dest="output_dir", type=Path, default=DEFAULT_CONFIG.output_dir)
    parser.add_argument("--logs", dest="log_dir", type=Path, default=DEFAULT_CONFIG.log_dir)
    return parser


def main(argv: Iterable[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    config = TranslationConfig(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        log_dir=args.log_dir,
    )

    if args.command == "translate":
        translate_directory(config)
    elif args.command == "refresh":
        refresh_directory(config)
    else:
        parser.error(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    main()
