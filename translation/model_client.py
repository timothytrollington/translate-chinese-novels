"""Client abstractions for translation models or APIs."""
from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass
from typing import Iterable, List, Protocol


class TranslationModel(Protocol):
    """Protocol describing a client capable of translating text batches."""

    model_name: str

    def translate_batch(self, prompts: Iterable[dict]) -> List[str]:
        """Translate a batch of prompts into English."""

    def estimate_cost(self, prompts: Iterable[dict]) -> float:
        """Estimate monetary cost for translating the prompts."""


@dataclass
class MockTranslationModel:
    """A mock translation model used for testing the pipeline."""

    model_name: str = "mock-translator-v1"
    cost_per_1k_chars: float = 0.01

    def translate_batch(self, prompts: Iterable[dict]) -> List[str]:
        translations = []
        for prompt in prompts:
            source = prompt.get("user", "")
            if "<Source>" in source and "</Source>" in source:
                start = source.index("<Source>") + len("<Source>")
                end = source.index("</Source>", start)
                source = source[start:end]
            translations.append(f"[Translated] {source.strip()}")
        return translations

    def estimate_cost(self, prompts: Iterable[dict]) -> float:
        total_chars = 0
        for prompt in prompts:
            total_chars += len(prompt.get("user", "")) + len(prompt.get("system", ""))
        return (total_chars / 1000) * self.cost_per_1k_chars


@dataclass
class TranslationMetadata:
    """Metadata captured for each translation run."""

    model_name: str
    timestamp: _dt.datetime
    cost: float
    source_path: str
    output_path: str
    segment_count: int

    def as_dict(self) -> dict:
        return {
            "model_name": self.model_name,
            "timestamp": self.timestamp.isoformat(),
            "cost": self.cost,
            "source_path": self.source_path,
            "output_path": self.output_path,
            "segment_count": self.segment_count,
        }
