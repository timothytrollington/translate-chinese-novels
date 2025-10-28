"""Pipeline entrypoint for updating translations."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List
import logging

from .config import PipelineConfig
from .notifications import notify_updates
from .storage import (
    ChapterMetadata,
    load_metadata,
    mark_chapters_processed,
    new_chapters,
    save_metadata,
)
from .toc import ChapterListing, fetch_toc
from .translator import metadata_entry, translate_chapter

LOGGER = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    processed: List[ChapterMetadata]
    skipped: int


def run_pipeline(config: PipelineConfig) -> PipelineResult:
    """Execute the discovery, translation, and notification pipeline."""

    config.ensure_directories()
    metadata = load_metadata(config.metadata_path)

    toc_entries = fetch_toc(config.toc_source, timeout=config.request_timeout)
    if not toc_entries:
        LOGGER.warning("TOC did not return any chapters")
        return PipelineResult(processed=[], skipped=0)

    LOGGER.info("Loaded %d entries from TOC", len(toc_entries))
    entries_to_process = new_chapters(metadata, toc_entries)

    if not entries_to_process:
        LOGGER.info("No new chapters detected")
        return PipelineResult(processed=[], skipped=len(toc_entries))

    processed_entries = _process_entries(
        entries_to_process,
        config=config,
    )

    mark_chapters_processed(metadata, processed_entries)
    save_metadata(config.metadata_path, metadata)

    _update_changelog(config.changelog_path, processed_entries)
    _notify(processed_entries, config)

    return PipelineResult(processed=processed_entries, skipped=len(toc_entries) - len(processed_entries))


def _process_entries(
    entries: Iterable[ChapterListing],
    config: PipelineConfig,
) -> List[ChapterMetadata]:
    results: List[ChapterMetadata] = []

    with ThreadPoolExecutor(max_workers=config.max_workers) as executor:
        future_map = {
            executor.submit(
                translate_chapter,
                entry.identifier,
                entry.title,
                entry.url,
                config.output_dir,
                engine=config.translation_engine,
                timeout=config.request_timeout,
            ): entry
            for entry in entries
        }

        for future in as_completed(future_map):
            entry = future_map[future]
            try:
                output_path, _ = future.result()
            except Exception as exc:
                LOGGER.error("Failed to process chapter %s: %s", entry.identifier, exc)
                continue

            chapter_meta = ChapterMetadata(**metadata_entry(
                identifier=entry.identifier,
                title=entry.title,
                url=entry.url,
                output_path=output_path,
            ))
            results.append(chapter_meta)

    results.sort(key=lambda item: item.identifier)
    return results


def _update_changelog(path: Path, entries: Iterable[ChapterMetadata]) -> None:
    entries = list(entries)
    if not entries:
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        for entry in entries:
            fh.write(
                f"- {entry.translated_at}: Added {entry.title} ({entry.identifier}) → {entry.output_path}\n"
            )


def _notify(entries: Iterable[ChapterMetadata], config: PipelineConfig) -> None:
    messages = [
        f"New chapter translated: {entry.title} ({entry.identifier}) → {entry.output_path}"
        for entry in entries
    ]
    notify_updates(config.notification, messages)
