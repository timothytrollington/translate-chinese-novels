"""Utilities for retrieving and parsing table-of-contents information."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List
import json
import logging

import requests

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class ChapterListing:
    """A lightweight description of a chapter from the TOC."""

    identifier: str
    title: str
    url: str


class TocRetrievalError(RuntimeError):
    """Raised when the TOC could not be retrieved."""


def fetch_toc(source: str, timeout: int = 30) -> List[ChapterListing]:
    """Fetch the table of contents from the configured source.

    The function understands local JSON files (helpful for testing) as well as
    HTTP(S) endpoints that return JSON payloads in the form
    ``[{"id": "1", "title": "Chapter 1", "url": "..."}, ...]``.
    """

    if source.startswith("http://") or source.startswith("https://"):
        LOGGER.info("Fetching TOC from %s", source)
        response = requests.get(source, timeout=timeout)
        if response.status_code >= 400:
            raise TocRetrievalError(
                f"Failed to fetch TOC from {source}: {response.status_code}"
            )
        payload = response.json()
    else:
        path = Path(source)
        if not path.exists():
            raise TocRetrievalError(f"TOC file not found: {path}")
        with path.open("r", encoding="utf-8") as fh:
            payload = json.load(fh)

    return _parse_payload(payload)


def _parse_payload(payload: Iterable[dict]) -> List[ChapterListing]:
    chapters: List[ChapterListing] = []
    for entry in payload:
        identifier = str(entry.get("id")) if entry.get("id") is not None else None
        title = entry.get("title")
        url = entry.get("url")

        if not identifier or not title or not url:
            LOGGER.debug("Skipping malformed TOC entry: %s", entry)
            continue

        chapters.append(ChapterListing(identifier=identifier, title=title, url=url))
    return chapters
