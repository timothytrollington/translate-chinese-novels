from __future__ import annotations

import argparse
from pathlib import Path

from .translator import translate_dataframe


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Translate a CSV file of Chinese text")
    parser.add_argument("--input", required=True, type=Path, help="Path to the input CSV file")
    parser.add_argument("--output", required=True, type=Path, help="Path to write the translated CSV")
    parser.add_argument(
        "--config",
        default=Path("config/translation_config.yaml"),
        type=Path,
        help="Path to the translation configuration file",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    translate_dataframe(args.input, args.output, args.config)


if __name__ == "__main__":
    main()
