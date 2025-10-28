"""Utilities for loading translation configuration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import yaml


@dataclass(frozen=True)
class RetryConfig:
    max_attempts: int
    backoff_seconds: float
    jitter_seconds: float


@dataclass(frozen=True)
class APIConfig:
    provider: str
    model: str
    temperature: float
    max_requests_per_minute: int
    max_tokens_per_minute: int
    max_tokens_per_request: int
    request_timeout_seconds: int
    retry: RetryConfig


@dataclass(frozen=True)
class LocalModelConfig:
    model_name: str
    device: str
    batch_size: int
    max_length: int
    half_precision: bool


@dataclass(frozen=True)
class BatchingConfig:
    batch_size: int
    max_characters_per_batch: int


@dataclass(frozen=True)
class PersistenceConfig:
    cache_translations: bool
    cache_backend: str
    cache_path: str


@dataclass(frozen=True)
class TranslationConfig:
    approach: str
    api: APIConfig
    local: LocalModelConfig
    batching: BatchingConfig
    persistence: PersistenceConfig


class ConfigError(RuntimeError):
    """Raised when the configuration file is invalid."""


def _load_yaml(path: Path) -> Dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as file:
            return yaml.safe_load(file)
    except FileNotFoundError as exc:
        raise ConfigError(f"Configuration file not found: {path}") from exc
    except yaml.YAMLError as exc:
        raise ConfigError(f"Invalid YAML configuration: {exc}") from exc


def load_config(path: Path) -> TranslationConfig:
    """Load the translation configuration from ``path``."""

    data = _load_yaml(path)

    def expect(section: str) -> Dict[str, Any]:
        if section not in data or not isinstance(data[section], dict):
            raise ConfigError(f"Missing or invalid section '{section}' in config")
        return data[section]

    api_data = expect("api")
    local_data = expect("local")
    batching_data = expect("batching")
    persistence_data = expect("persistence")

    retry_data = api_data.get("retry", {})
    try:
        retry_config = RetryConfig(
            max_attempts=int(retry_data.get("max_attempts", 3)),
            backoff_seconds=float(retry_data.get("backoff_seconds", 1.0)),
            jitter_seconds=float(retry_data.get("jitter_seconds", 0.1)),
        )

        api_config = APIConfig(
            provider=str(api_data["provider"]),
            model=str(api_data["model"]),
            temperature=float(api_data.get("temperature", 0.0)),
            max_requests_per_minute=int(api_data.get("max_requests_per_minute", 60)),
            max_tokens_per_minute=int(api_data.get("max_tokens_per_minute", 90000)),
            max_tokens_per_request=int(api_data.get("max_tokens_per_request", 4000)),
            request_timeout_seconds=int(api_data.get("request_timeout_seconds", 60)),
            retry=retry_config,
        )

        local_config = LocalModelConfig(
            model_name=str(local_data["model_name"]),
            device=str(local_data.get("device", "auto")),
            batch_size=int(local_data.get("batch_size", 8)),
            max_length=int(local_data.get("max_length", 512)),
            half_precision=bool(local_data.get("half_precision", False)),
        )

        batching_config = BatchingConfig(
            batch_size=int(batching_data.get("batch_size", 8)),
            max_characters_per_batch=int(batching_data.get("max_characters_per_batch", 2000)),
        )

        persistence_config = PersistenceConfig(
            cache_translations=bool(persistence_data.get("cache_translations", False)),
            cache_backend=str(persistence_data.get("cache_backend", "memory")),
            cache_path=str(persistence_data.get("cache_path", "")),
        )
    except KeyError as exc:
        raise ConfigError(f"Missing required configuration key: {exc}") from exc
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"Invalid value in configuration: {exc}") from exc

    approach = str(data.get("approach", "api"))
    if approach not in {"api", "local"}:
        raise ConfigError(f"Unsupported approach '{approach}'. Use 'api' or 'local'.")

    return TranslationConfig(
        approach=approach,
        api=api_config,
        local=local_config,
        batching=batching_config,
        persistence=persistence_config,
    )


__all__ = [
    "TranslationConfig",
    "APIConfig",
    "LocalModelConfig",
    "BatchingConfig",
    "PersistenceConfig",
    "RetryConfig",
    "ConfigError",
    "load_config",
]
