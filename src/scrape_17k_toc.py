"""Utilities for fetching and persisting 17k.com chapter metadata.

This module provides a small CLI that downloads a novel's table of
contents (TOC), extracts chapter level metadata, and stores the results
in a local SQLite database (and optionally a JSON file).  The script is
intended to be polite by identifying itself with clear headers and by
respecting a configurable rate limit between HTTP requests.

Example usage::

    python -m src.scrape_17k_toc \
        https://www.17k.com/list/493239.html \
        --db data/17k_chapters.db \
        --json data/17k_chapters.json

The scraper supports incremental updates: chapters that already exist in
the SQLite database are skipped, allowing repeated executions to append
only new material.
"""
from __future__ import annotations

import argparse
import json
import logging
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional
from urllib.parse import urljoin, urlparse
import re

import requests
from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)

# 17k.com requests appear to work best when the client looks like a regular
# browser.  The headers below mimic a common desktop browser while still
# identifying the script via the From header.
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.8",
    "Connection": "close",
    "From": "opensource-bot@example.com",
}


@dataclass
class Chapter:
    """Represents a single chapter from the TOC."""

    identifier: str
    title: str
    url: str
    publication_date: Optional[str]


class RateLimiter:
    """Simple rate limiter that enforces a minimum delay between calls."""

    def __init__(self, min_interval: float) -> None:
        self.min_interval = max(0.0, float(min_interval))
        self._last_called = 0.0

    def wait(self) -> None:
        """Sleep just enough to respect the configured interval."""

        if self.min_interval <= 0:
            return
        now = time.monotonic()
        elapsed = now - self._last_called
        remaining = self.min_interval - elapsed
        if remaining > 0:
            time.sleep(remaining)
        self._last_called = time.monotonic()


def fetch_html(url: str, session: requests.Session, limiter: RateLimiter) -> str:
    """Download and return the HTML for *url* using *session*.

    The function enforces polite crawling by applying the provided
    ``RateLimiter`` before dispatching the request.
    """

    logger.info("Fetching %s", url)
    limiter.wait()
    response = session.get(url, timeout=30)
    response.raise_for_status()
    return response.text


def parse_toc(html: str, base_url: str) -> List[Chapter]:
    """Parse a 17k.com TOC page and return chapter metadata.

    Parameters
    ----------
    html:
        Raw HTML of the TOC page.
    base_url:
        The URL used to retrieve the HTML.  This is necessary so that
        relative chapter hyperlinks can be resolved into absolute URLs.

    Notes
    -----
    The 17k.com TOC uses ``<dl class="Volume">`` containers with ``<dd>``
    entries for each chapter.  The parser is intentionally defensive and
    accepts a handful of alternative tag/class combinations to remain
    resilient to minor layout updates.
    """

    soup = BeautifulSoup(html, "lxml")
    chapters: List[Chapter] = []
    # Candidate containers that hold chapter listings.
    containers = soup.select("dl.Volume, dl.volume, div.volume, div.Volume")
    if not containers:
        # Some pages nest the TOC within a dedicated element.
        chapter_list = soup.select_one("#chapterList, .chapter-list")
        if chapter_list:
            containers = chapter_list.select("dl, div") or [chapter_list]
        else:
            containers = [soup]

    for container in containers:
        for dd in container.find_all(["dd", "li", "div"]):
            link = dd.find("a", href=True)
            if not link:
                continue
            chapter_url = urljoin(base_url, link["href"])
            chapter_id = extract_chapter_id(chapter_url)
            title = link.get_text(strip=True)
            if not title:
                continue

            date_node = (
                dd.find("time")
                or dd.find("span", class_=lambda c: c and "update" in c)
                or dd.find("em")
                or dd.find("span")
            )
            publication_date = None
            if date_node:
                publication_date = date_node.get_text(strip=True) or None

            chapters.append(
                Chapter(
                    identifier=chapter_id,
                    title=title,
                    url=chapter_url,
                    publication_date=publication_date,
                )
            )

    # Remove duplicates that may result from overlapping selectors.
    unique: dict[str, Chapter] = {}
    for chapter in chapters:
        unique.setdefault(chapter.identifier, chapter)
    return list(unique.values())


_CHAPTER_ID_REGEX = re.compile(r"/(\d+)(?:\.html)?$")


def extract_chapter_id(url: str) -> str:
    """Extract a stable identifier from a chapter URL.

    17k chapter URLs typically look like ``/chapter/12345/67890.html``.
    The final numeric component uniquely identifies the chapter, so we
    prefer that.  As a fallback, the function returns the entire path.
    """

    path = urlparse(url).path.rstrip("/")
    match = _CHAPTER_ID_REGEX.search(path)
    if match:
        return match.group(1)
    # Fallback to the last path component for resiliency.
    return path.rsplit("/", 1)[-1]


def ensure_schema(connection: sqlite3.Connection) -> None:
    """Create the chapters table if it does not already exist."""

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS chapters (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            publication_date TEXT
        )
        """
    )
    connection.commit()


def load_existing_ids(connection: sqlite3.Connection) -> set[str]:
    """Return a set containing the identifiers already stored."""

    cursor = connection.execute("SELECT id FROM chapters")
    return {row[0] for row in cursor.fetchall()}


def persist_chapters(
    connection: sqlite3.Connection, chapters: Iterable[Chapter]
) -> int:
    """Insert unseen chapters into the database.

    Returns the number of newly inserted chapters.  Existing rows are
    ignored so repeated runs only append fresh data.
    """

    ensure_schema(connection)
    existing = load_existing_ids(connection)
    inserted = 0
    for chapter in chapters:
        if chapter.identifier in existing:
            logger.debug("Skipping already stored chapter %s", chapter.identifier)
            continue
        connection.execute(
            "INSERT INTO chapters (id, title, url, publication_date) VALUES (?, ?, ?, ?)",
            (chapter.identifier, chapter.title, chapter.url, chapter.publication_date),
        )
        existing.add(chapter.identifier)
        inserted += 1
    connection.commit()
    return inserted


def dump_to_json(chapters: Iterable[Chapter], path: Path) -> None:
    """Serialize chapters into a JSON array at *path*."""

    payload = [
        {
            "id": chapter.identifier,
            "title": chapter.title,
            "url": chapter.url,
            "publication_date": chapter.publication_date,
        }
        for chapter in chapters
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "toc_url",
        help="Full URL to a 17k.com list/ page containing the chapter table of contents.",
    )
    parser.add_argument(
        "--db",
        default="data/17k_chapters.db",
        help="Path to the SQLite database used for caching chapter metadata.",
    )
    parser.add_argument(
        "--json",
        help="Optional path to a JSON file that will receive the extracted chapter metadata.",
    )
    parser.add_argument(
        "--rate",
        type=float,
        default=1.0,
        help="Minimum delay (in seconds) between HTTP requests. Default: 1.0",
    )
    parser.add_argument(
        "--html-cache",
        help=(
            "Path to an HTML file to use instead of making a network request. "
            "Useful for offline debugging."
        ),
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging for debugging purposes.",
    )

    args = parser.parse_args(argv)
    configure_logging(args.verbose)

    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)
    limiter = RateLimiter(args.rate)

    if args.html_cache:
        html_path = Path(args.html_cache)
        logger.info("Loading HTML from %s", html_path)
        html = html_path.read_text(encoding="utf-8")
        base_url = args.toc_url
    else:
        html = fetch_html(args.toc_url, session, limiter)
        base_url = args.toc_url

    chapters = parse_toc(html, base_url)
    logger.info("Parsed %d chapters from the TOC", len(chapters))

    db_path = Path(args.db)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as connection:
        inserted = persist_chapters(connection, chapters)
    logger.info("Inserted %d new chapters into %s", inserted, db_path)

    if args.json:
        json_path = Path(args.json)
        dump_to_json(chapters, json_path)
        logger.info("Wrote JSON payload to %s", json_path)


if __name__ == "__main__":
    main()
