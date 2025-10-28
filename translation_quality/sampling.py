"""Sampling utilities for manual review of chapters."""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Iterable, List, Dict, Any


@dataclass
class SampledParagraph:
    """Paragraph selected for manual inspection."""

    chapter: str
    paragraph_index: int
    source: str
    translation: str


def sample_chapters(
    entries: Iterable[Dict[str, Any]],
    *,
    sample_size: int = 5,
    seed: int | None = None,
) -> List[SampledParagraph]:
    """Return a stable random sample of paragraphs for manual review."""

    entries_list = [
        SampledParagraph(
            chapter=str(entry.get("chapter", "")),
            paragraph_index=int(entry.get("paragraph_index", -1)),
            source=str(entry.get("source", "")),
            translation=str(entry.get("translation", "")),
        )
        for entry in entries
    ]
    if not entries_list:
        return []
    rng = random.Random(seed)
    sample_size = min(sample_size, len(entries_list))
    return rng.sample(entries_list, sample_size)


__all__ = ["sample_chapters", "SampledParagraph"]
