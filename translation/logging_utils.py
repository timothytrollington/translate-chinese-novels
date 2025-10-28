"""Logging helpers for translation metadata."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from .model_client import TranslationMetadata


class MetadataLogger:
    """Append translation metadata entries to a JSONL log file."""

    def __init__(self, log_path: str | Path) -> None:
        self._log_path = Path(log_path)
        self._log_path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, metadata: TranslationMetadata) -> None:
        record = json.dumps(metadata.as_dict(), ensure_ascii=False)
        with self._log_path.open("a", encoding="utf-8") as fh:
            fh.write(record + "\n")

    def dump_many(self, metadatas: Iterable[TranslationMetadata]) -> None:
        for metadata in metadatas:
            self.append(metadata)
