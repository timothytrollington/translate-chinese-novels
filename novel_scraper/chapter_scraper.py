"""Chapter scraping utilities with caching, retry, and metadata support."""
from __future__ import annotations

import hashlib
import json
import logging
import re
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


@dataclass
class Chapter:
    """Metadata required to fetch and archive a chapter."""

    number: str
    url: str
    title: Optional[str] = None
    container_selector: Optional[str] = None

    def filename(self, extension: str = ".md") -> str:
        """Return a safe filename for the chapter based on its number."""
        number = self.number
        try:
            number_int = int(str(number).strip())
        except (TypeError, ValueError):
            safe = re.sub(r"[^0-9A-Za-z_-]+", "_", str(number))
            safe = safe.strip("._") or "chapter"
            return f"chapter_{safe}{extension}"
        else:
            return f"chapter_{number_int:04d}{extension}"


class ChapterScraper:
    """Scrape novel chapters into structured Markdown or plain text files."""

    def __init__(
        self,
        output_dir: Path,
        *,
        metadata_path: Optional[Path] = None,
        default_container_selector: Optional[str] = None,
        text_format: str = "md",
        encoding: str = "utf-8",
        cache_dir: Optional[Path] = None,
        max_retries: int = 5,
        backoff_factor: float = 1.5,
        timeout: int = 20,
        session: Optional[requests.Session] = None,
        headers: Optional[dict[str, str]] = None,
        refresh_cache: bool = False,
    ) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_path = metadata_path or (self.output_dir / "metadata.json")
        self.metadata_path.parent.mkdir(parents=True, exist_ok=True)
        self.default_container_selector = default_container_selector
        self.text_format = text_format.lower()
        if self.text_format not in {"md", "txt"}:
            raise ValueError("text_format must be either 'md' or 'txt'")
        self.extension = f".{self.text_format}"
        self.encoding = encoding
        self.cache_dir = Path(cache_dir) if cache_dir else None
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_retries = max(1, int(max_retries))
        self.backoff_factor = max(0.0, backoff_factor)
        self.timeout = timeout
        self.session = session or requests.Session()
        self.session.headers.setdefault(
            "User-Agent",
            (
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
        )
        if headers:
            self.session.headers.update(headers)
        self.refresh_cache = refresh_cache
        self._metadata = self._load_metadata()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def fetch_chapters(self, chapters: Iterable[Chapter]) -> List[Path]:
        """Fetch and archive all provided chapters."""
        saved_paths: List[Path] = []
        for chapter in chapters:
            logger.info("Fetching chapter %s", chapter.number)
            saved_paths.append(self.fetch_chapter(chapter))
        self._write_metadata()
        return saved_paths

    def fetch_chapter(self, chapter: Chapter) -> Path:
        """Fetch, parse, and save a single chapter."""
        html = self._get_html(chapter.url)
        soup = BeautifulSoup(html, "html.parser")
        container = self._select_container(soup, chapter)
        if container is None:
            raise ValueError(
                "Could not locate the main text container. "
                "Consider providing a CSS selector via Chapter.container_selector "
                "or default_container_selector."
            )

        title = chapter.title or self._extract_title(soup, container)
        paragraphs = self._extract_paragraphs(container)
        if not paragraphs:
            raise ValueError("No text content could be extracted for chapter")

        content_lines: List[str] = []
        if title:
            heading = title.strip()
            if self.text_format == "md" and not heading.startswith("#"):
                content_lines.append(f"# {heading}")
            else:
                content_lines.append(heading)
            content_lines.append("")

        content_lines.extend(paragraphs)
        content = "\n\n".join(content_lines).strip() + "\n"

        file_path = self.output_dir / chapter.filename(self.extension)
        file_path.write_text(content, encoding=self.encoding)

        metadata_entry = {
            "number": chapter.number,
            "url": chapter.url,
            "title": title,
            "file": str(file_path.relative_to(self.metadata_path.parent)),
            "format": self.text_format,
            "fetched_at": datetime.utcnow().isoformat() + "Z",
        }
        self._metadata[str(chapter.number)] = metadata_entry
        self._write_metadata()
        return file_path

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _get_html(self, url: str) -> str:
        if self.cache_dir and not self.refresh_cache:
            cached = self._read_cache(url)
            if cached is not None:
                return cached

        response = self._request_with_retry(url)
        response.encoding = response.encoding or self.encoding
        text = response.text

        if self.cache_dir:
            self._write_cache(url, text)
        return text

    def _request_with_retry(self, url: str) -> requests.Response:
        last_error: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.session.get(url, timeout=self.timeout)
                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    delay = self._compute_delay(attempt, retry_after)
                    logger.warning(
                        "Received 429 for %s. Sleeping for %.1f seconds before retry %d/%d",
                        url,
                        delay,
                        attempt,
                        self.max_retries,
                    )
                    time.sleep(delay)
                    continue
                response.raise_for_status()
                return response
            except requests.RequestException as exc:  # includes HTTPError
                last_error = exc
                if attempt >= self.max_retries:
                    break
                delay = self._compute_delay(attempt)
                logger.warning(
                    "Request to %s failed (attempt %d/%d): %s. Retrying in %.1f seconds",
                    url,
                    attempt,
                    self.max_retries,
                    exc,
                    delay,
                )
                time.sleep(delay)
        assert last_error is not None
        raise last_error

    def _compute_delay(self, attempt: int, retry_after: Optional[str] = None) -> float:
        if retry_after:
            try:
                return float(retry_after)
            except ValueError:
                pass
        return max(self.backoff_factor, 0.1) * (2 ** (attempt - 1))

    def _select_container(self, soup: BeautifulSoup, chapter: Chapter):
        selector = chapter.container_selector or self.default_container_selector
        container = None
        if selector:
            container = soup.select_one(selector)
        if container is None:
            container = soup.find("article")
        if container is None:
            container = soup.find(id=re.compile("content|chapter", re.I))
        if container is None:
            container = soup.find(class_=re.compile("content|chapter", re.I))
        return container

    def _extract_title(self, soup: BeautifulSoup, container) -> Optional[str]:
        heading = container.find(["h1", "h2", "h3"])
        if heading and heading.get_text(strip=True):
            return heading.get_text(strip=True)
        doc_heading = soup.find("h1")
        if doc_heading and doc_heading.get_text(strip=True):
            return doc_heading.get_text(strip=True)
        return None

    def _extract_paragraphs(self, container) -> List[str]:
        text = container.get_text(separator="\n", strip=True)
        chunks = [chunk for chunk in re.split(r"\n{2,}", text) if chunk.strip()]
        paragraphs: List[str] = []
        for chunk in chunks:
            lines = [self._normalize_whitespace(line) for line in chunk.split("\n")]
            merged = " ".join(line for line in lines if line)
            if merged:
                paragraphs.append(merged)
        if not paragraphs:
            normalized = self._normalize_whitespace(text)
            if normalized:
                paragraphs = [normalized]
        return paragraphs

    @staticmethod
    def _normalize_whitespace(text: str) -> str:
        text = text.replace("\u00a0", " ")
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _load_metadata(self) -> dict[str, dict]:
        if self.metadata_path.exists():
            with self.metadata_path.open("r", encoding=self.encoding) as fh:
                try:
                    data = json.load(fh)
                except json.JSONDecodeError:
                    logger.warning("Metadata file %s is invalid JSON; starting fresh", self.metadata_path)
                    return {}
                if isinstance(data, dict):
                    chapters = data.get("chapters")
                    if isinstance(chapters, list):
                        return {
                            str(item.get("number")): item
                            for item in chapters
                            if isinstance(item, dict) and item.get("number") is not None
                        }
                    return {
                        str(key): value
                        for key, value in data.items()
                        if isinstance(value, dict) and value.get("number") is not None
                    }
                if isinstance(data, list):
                    return {
                        str(item.get("number")): item
                        for item in data
                        if isinstance(item, dict) and item.get("number") is not None
                    }
        return {}

    def _write_metadata(self) -> None:
        serialized = {"chapters": list(sorted(self._metadata.values(), key=self._chapter_sort_key))}
        with self.metadata_path.open("w", encoding=self.encoding) as fh:
            json.dump(serialized, fh, ensure_ascii=False, indent=2)

    @staticmethod
    def _chapter_sort_key(item: dict) -> Tuple[int, str]:
        number = item.get("number")
        try:
            number_int = int(str(number).strip())
        except (TypeError, ValueError):
            return (1, str(number))
        return (0, f"{number_int:08d}")

    # ------------------------------------------------------------------
    # Cache helpers
    # ------------------------------------------------------------------
    def _cache_key(self, url: str) -> str:
        digest = hashlib.sha256(url.encode("utf-8")).hexdigest()
        return f"{digest}.html"

    def _read_cache(self, url: str) -> Optional[str]:
        if not self.cache_dir:
            return None
        cache_file = self.cache_dir / self._cache_key(url)
        if cache_file.exists():
            return cache_file.read_text(encoding=self.encoding)
        return None

    def _write_cache(self, url: str, content: str) -> None:
        if not self.cache_dir:
            return
        cache_file = self.cache_dir / self._cache_key(url)
        cache_file.write_text(content, encoding=self.encoding)


__all__ = ["Chapter", "ChapterScraper"]
