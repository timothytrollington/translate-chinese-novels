"""CLI for scraping Chinese novel chapters from a metadata file."""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Iterable, List

from novel_scraper import Chapter, ChapterScraper


def load_chapters(metadata_path: Path) -> List[Chapter]:
    with metadata_path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if isinstance(data, dict) and "chapters" in data:
        entries = data["chapters"]
    elif isinstance(data, list):
        entries = data
    else:
        raise ValueError("Input metadata must be a list or contain a 'chapters' key")

    chapters: List[Chapter] = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("Each chapter entry must be a mapping")
        try:
            number = entry["number"]
            url = entry["url"]
        except KeyError as exc:
            raise ValueError("Each chapter entry must include 'number' and 'url'") from exc
        chapters.append(
            Chapter(
                number=str(number),
                url=str(url),
                title=entry.get("title"),
                container_selector=entry.get("container_selector"),
            )
        )
    return chapters


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scrape novel chapters into local files.")
    parser.add_argument("input", type=Path, help="JSON file describing the chapters to download")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/chapters"),
        help="Directory where chapter files and metadata.json should be written.",
    )
    parser.add_argument(
        "--metadata",
        type=Path,
        default=None,
        help="Optional explicit metadata JSON path. Defaults to <output-dir>/metadata.json.",
    )
    parser.add_argument(
        "--selector",
        dest="default_container_selector",
        default=None,
        help="CSS selector identifying the main text container when a chapter entry does not override it.",
    )
    parser.add_argument(
        "--format",
        choices=["md", "txt"],
        default="md",
        help="Output file format (Markdown or plain text).",
    )
    parser.add_argument("--encoding", default="utf-8", help="Text encoding for saved files.")
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=None,
        help="If provided, responses will be cached in this directory to avoid repeated downloads.",
    )
    parser.add_argument(
        "--refresh-cache",
        action="store_true",
        help="Ignore any cached responses and fetch from the network.",
    )
    parser.add_argument("--max-retries", type=int, default=5, help="Maximum number of HTTP retries.")
    parser.add_argument(
        "--backoff",
        type=float,
        default=1.5,
        help="Base backoff (seconds) used for exponential retry delays.",
    )
    parser.add_argument("--timeout", type=int, default=20, help="HTTP request timeout in seconds.")
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (DEBUG, INFO, WARNING, ERROR).",
    )
    return parser.parse_args(argv)



def main(argv: Iterable[str] | None = None) -> None:
    args = parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))

    chapters = load_chapters(args.input)

    scraper = ChapterScraper(
        output_dir=args.output_dir,
        metadata_path=args.metadata or (args.output_dir / "metadata.json"),
        default_container_selector=args.default_container_selector,
        text_format=args.format,
        encoding=args.encoding,
        cache_dir=args.cache_dir,
        max_retries=args.max_retries,
        backoff_factor=args.backoff,
        timeout=args.timeout,
        refresh_cache=args.refresh_cache,
    )

    scraper.fetch_chapters(chapters)


if __name__ == "__main__":
    main()
