"""Translation and post-processing utilities."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import logging

import requests

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class ChapterContent:
    identifier: str
    title: str
    url: str
    text: str


class ChapterDownloadError(RuntimeError):
    """Raised when a chapter could not be downloaded."""


def download_chapter(url: str, timeout: int = 30) -> str:
    if url.startswith("http://") or url.startswith("https://"):
        response = requests.get(url, timeout=timeout)
        if response.status_code >= 400:
            raise ChapterDownloadError(
                f"Failed to download chapter from {url}: {response.status_code}"
            )
        return response.text

    path = Path(url)
    if not path.exists():
        raise ChapterDownloadError(f"Chapter file not found: {path}")
    with path.open("r", encoding="utf-8") as fh:
        return fh.read()


def translate_text(text: str, engine: str = "noop") -> str:
    """Translate the provided text using the configured engine.

    The default ``noop`` engine simply echoes back the original text, which keeps
    the pipeline runnable in environments without API keys. A ``mock`` engine is
    also provided for tests to simulate a translation step.
    """

    if engine == "noop":
        return text
    if engine == "mock":
        return f"[translated]\n{text}"

    raise ValueError(
        f"Unsupported translation engine: {engine}. Configure TRANSLATION_ENGINE"
    )


def post_process(text: str) -> str:
    """Apply simple clean-up to translated text."""

    cleaned = text.strip().replace("\r\n", "\n")
    return cleaned + "\n"


def persist_translation(
    directory: Path,
    chapter: ChapterContent,
    translated_text: str,
    extension: str = ".md",
) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    filename = f"{chapter.identifier}_{slugify(chapter.title)}{extension}"
    destination = directory / filename
    with destination.open("w", encoding="utf-8") as fh:
        fh.write(f"# {chapter.title}\n\n")
        fh.write(translated_text)
    return destination


def slugify(value: str) -> str:
    return "".join(char.lower() if char.isalnum() else "-" for char in value).strip("-")


def translate_chapter(
    identifier: str,
    title: str,
    url: str,
    output_dir: Path,
    engine: str = "noop",
    timeout: int = 30,
) -> tuple[Path, str]:
    """Download, translate, post-process, and persist a chapter."""

    LOGGER.info("Translating %s - %s", identifier, title)
    raw_text = download_chapter(url, timeout=timeout)
    translated = translate_text(raw_text, engine=engine)
    cleaned = post_process(translated)
    output_path = persist_translation(
        directory=output_dir,
        chapter=ChapterContent(identifier, title, url, raw_text),
        translated_text=cleaned,
    )
    return output_path, cleaned


def metadata_entry(
    identifier: str,
    title: str,
    url: str,
    output_path: Path,
) -> dict:
    return {
        "identifier": identifier,
        "title": title,
        "url": url,
        "output_path": str(output_path),
        "translated_at": datetime.now(timezone.utc).isoformat(),
    }
