"""Utilities for splitting Chinese chapters into manageable segments."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, List


_SENTENCE_BOUNDARY = re.compile(r"(?<=[。！？?!])")


@dataclass
class Segment:
    """A single translation segment and its provenance."""

    text: str
    paragraph_index: int
    fragment_index: int


def _split_sentences(text: str) -> List[str]:
    sentences: List[str] = []
    buffer: List[str] = []
    for fragment in _SENTENCE_BOUNDARY.split(text):
        fragment = fragment.strip()
        if not fragment:
            continue
        buffer.append(fragment)
        if _SENTENCE_BOUNDARY.match(fragment[-1]):
            sentences.append("".join(buffer))
            buffer.clear()
    if buffer:
        sentences.append("".join(buffer))
    return sentences if sentences else [text]


@dataclass
class Segmenter:
    """Segments long passages by paragraphs and sentences."""

    max_chars: int = 1500

    def segment(self, text: str) -> List[Segment]:
        """Return a list of manageable translation segments."""

        paragraphs = [p for p in text.split("\n\n") if p.strip()]
        segments: List[Segment] = []
        for para_index, paragraph in enumerate(paragraphs):
            normalized = "\n".join(line.strip() for line in paragraph.splitlines() if line.strip())
            if not normalized:
                continue
            if len(normalized) <= self.max_chars:
                segments.append(Segment(normalized, para_index, 0))
                continue

            sentences = _split_sentences(normalized)
            current: List[str] = []
            current_len = 0
            fragment_index = 0
            for sentence in sentences:
                if current and current_len + len(sentence) > self.max_chars:
                    segments.append(Segment("".join(current), para_index, fragment_index))
                    fragment_index += 1
                    current = [sentence]
                    current_len = len(sentence)
                else:
                    current.append(sentence)
                    current_len += len(sentence)
            if current:
                segments.append(Segment("".join(current), para_index, fragment_index))
        return segments

    def batch(self, segments: Iterable[Segment], batch_size: int) -> Iterable[List[Segment]]:
        """Yield fixed-size batches from the sequence of segments."""

        batch: List[Segment] = []
        for segment in segments:
            batch.append(segment)
            if len(batch) == batch_size:
                yield batch
                batch = []
        if batch:
            yield batch
