"""Configuration helpers for the translation pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class TranslationConfig:
    """Runtime options for the translation pipeline."""

    input_dir: Path
    output_dir: Path
    log_dir: Path = Path("logs")
    batch_size: int = 5
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    retry_attempts: int = 3


DEFAULT_CONFIG = TranslationConfig(
    input_dir=Path("data/raw_cn"),
    output_dir=Path("data/en_translated"),
)


def ensure_directories(config: TranslationConfig) -> None:
    """Create required directories for the translation workflow."""

    config.input_dir.mkdir(parents=True, exist_ok=True)
    config.output_dir.mkdir(parents=True, exist_ok=True)
    config.log_dir.mkdir(parents=True, exist_ok=True)
