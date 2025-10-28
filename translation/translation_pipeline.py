"""Translation pipeline for Chinese novel chapters."""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from .logging_utils import MetadataLogger
from .model_client import TranslationMetadata, TranslationModel
from .prompt_templates import DEFAULT_PROMPT_TEMPLATE, PromptTemplate
from .segmenter import Segment, Segmenter


@dataclass
class TranslationPipeline:
    """High level orchestrator for translating Chinese novel chapters."""

    model: TranslationModel
    prompt_template: PromptTemplate = DEFAULT_PROMPT_TEMPLATE
    segmenter: Segmenter = field(default_factory=Segmenter)
    logger: Optional[MetadataLogger] = None

    def translate_file(
        self,
        source_path: str | Path,
        output_dir: str | Path,
        *,
        batch_size: int = 5,
        prompt_metadata: Optional[Dict[str, str]] = None,
    ) -> Path:
        """Translate a single file and return the path to the English output."""

        source_path = Path(source_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        raw_text = source_path.read_text(encoding="utf-8")
        segments = self.segmenter.segment(raw_text)
        prompt_metadata = prompt_metadata or {}

        translated_segments, cost = self._translate_segments(segments, batch_size, prompt_metadata)
        english_text = self._recombine(translated_segments)
        output_path = output_dir / f"{source_path.stem}_en{source_path.suffix or '.txt'}"
        self._write_outputs(output_path, english_text, raw_text)

        metadata = TranslationMetadata(
            model_name=self.model.model_name,
            timestamp=dt.datetime.utcnow(),
            cost=cost,
            source_path=str(source_path),
            output_path=str(output_path),
            segment_count=len(segments),
        )
        if self.logger:
            self.logger.append(metadata)
        return output_path

    def _translate_segments(
        self,
        segments: List[Segment],
        batch_size: int,
        prompt_metadata: Dict[str, str],
    ) -> tuple[List[tuple[Segment, str]], float]:
        translated: List[tuple[Segment, str]] = []
        total_cost = 0.0
        for batch in self.segmenter.batch(segments, batch_size):
            prompts = [
                self.prompt_template.render(
                    source_text=segment.text,
                    metadata={**prompt_metadata, "paragraph": str(segment.paragraph_index + 1)},
                )
                for segment in batch
            ]
            translations = self.model.translate_batch(prompts)
            translated.extend(zip(batch, translations, strict=True))
            total_cost += self.model.estimate_cost(prompts)
        return translated, total_cost

    @staticmethod
    def _recombine(translated_segments: List[tuple[Segment, str]]) -> str:
        paragraphs: Dict[int, List[tuple[int, str]]] = {}
        for segment, translation in translated_segments:
            paragraphs.setdefault(segment.paragraph_index, []).append((segment.fragment_index, translation))
        ordered_paragraphs: List[str] = []
        for para_index in sorted(paragraphs):
            fragments = sorted(paragraphs[para_index])
            ordered_paragraphs.append("".join(fragment for _, fragment in fragments))
        return "\n\n".join(ordered_paragraphs)

    @staticmethod
    def _write_outputs(output_path: Path, english_text: str, original_text: str) -> None:
        combined = (
            "# Original Chinese\n" + original_text.strip() + "\n\n" + "# English Translation\n" + english_text.strip() + "\n"
        )
        output_path.write_text(combined, encoding="utf-8")
