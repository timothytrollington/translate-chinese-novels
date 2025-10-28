"""Helpers for loading and persisting metadata for processed chapters."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Protocol
import json


@dataclass
class ChapterMetadata:
    """Metadata recorded for each translated chapter."""

    identifier: str
    title: str
    url: str
    output_path: str
    translated_at: str


@dataclass
class PipelineMetadata:
    """Structure stored on disk to track processed chapters."""

    chapters: Dict[str, ChapterMetadata] = field(default_factory=dict)
    last_run_at: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "chapters": {key: vars(value) for key, value in self.chapters.items()},
            "last_run_at": self.last_run_at,
        }

    @classmethod
    def from_dict(cls, payload: dict) -> "PipelineMetadata":
        chapters = {
            identifier: ChapterMetadata(**data)
            for identifier, data in payload.get("chapters", {}).items()
        }
        return cls(chapters=chapters, last_run_at=payload.get("last_run_at"))


def load_metadata(path: Path) -> PipelineMetadata:
    if not path.exists():
        return PipelineMetadata()

    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    return PipelineMetadata.from_dict(data)


def save_metadata(path: Path, metadata: PipelineMetadata) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = metadata.to_dict()
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)


def mark_chapters_processed(
    metadata: PipelineMetadata, entries: Iterable[ChapterMetadata]
) -> None:
    for entry in entries:
        metadata.chapters[entry.identifier] = entry
    metadata.last_run_at = datetime.now(timezone.utc).isoformat()


def existing_ids(metadata: PipelineMetadata) -> set[str]:
    return set(metadata.chapters.keys())


class ChapterLike(Protocol):
    identifier: str


def new_chapters(
    metadata: PipelineMetadata, toc_entries: Iterable[ChapterLike]
) -> List[ChapterLike]:
    present = existing_ids(metadata)
    return [entry for entry in toc_entries if entry.identifier not in present]
