"""Configuration helpers for the translation pipeline."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import json
import os


@dataclass
class NotificationConfig:
    """Settings that control how notifications are dispatched."""

    enabled: bool = True
    email_recipients: list[str] = field(default_factory=list)
    smtp_server: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    use_tls: bool = True
    log_path: Path = Path("data/notifications.log")


@dataclass
class PipelineConfig:
    """Runtime configuration for the scheduled pipeline."""

    toc_source: str = "data/source/toc.json"
    metadata_path: Path = Path("data/metadata/chapters.json")
    output_dir: Path = Path("data/output")
    changelog_path: Path = Path("data/changelog.md")
    translation_engine: str = "noop"
    request_timeout: int = 30
    max_workers: int = 4
    notification: NotificationConfig = field(default_factory=NotificationConfig)

    @classmethod
    def from_env(cls) -> "PipelineConfig":
        """Create a config instance from environment variables."""

        notification = NotificationConfig(
            enabled=_env_flag("NOTIFY_ENABLED", True),
            email_recipients=_split_env("NOTIFY_EMAILS"),
            smtp_server=os.getenv("SMTP_SERVER"),
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            smtp_username=os.getenv("SMTP_USERNAME"),
            smtp_password=os.getenv("SMTP_PASSWORD"),
            use_tls=_env_flag("SMTP_USE_TLS", True),
            log_path=Path(os.getenv("NOTIFY_LOG_PATH", "data/notifications.log")),
        )

        toc_source = os.getenv("TOC_SOURCE", "data/source/toc.json")
        metadata_path = Path(os.getenv("METADATA_PATH", "data/metadata/chapters.json"))
        output_dir = Path(os.getenv("OUTPUT_DIR", "data/output"))
        changelog_path = Path(os.getenv("CHANGELOG_PATH", "data/changelog.md"))

        translation_engine = os.getenv("TRANSLATION_ENGINE", "noop")
        request_timeout = int(os.getenv("REQUEST_TIMEOUT", "30"))
        max_workers = int(os.getenv("PIPELINE_MAX_WORKERS", "4"))

        return cls(
            toc_source=toc_source,
            metadata_path=metadata_path,
            output_dir=output_dir,
            changelog_path=changelog_path,
            translation_engine=translation_engine,
            request_timeout=request_timeout,
            max_workers=max_workers,
            notification=notification,
        )

    def ensure_directories(self) -> None:
        """Create directories that must exist before the pipeline runs."""

        self.metadata_path.parent.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.changelog_path.parent.mkdir(parents=True, exist_ok=True)
        self.notification.log_path.parent.mkdir(parents=True, exist_ok=True)


def _split_env(key: str) -> list[str]:
    value = os.getenv(key)
    if not value:
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


def _env_flag(key: str, default: bool) -> bool:
    value = os.getenv(key)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def load_config(path: Optional[Path] = None) -> PipelineConfig:
    """Load configuration from a JSON file if provided."""

    config = PipelineConfig.from_env()
    if path is None:
        return config

    if path.exists():
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        for key, value in data.items():
            if key == "notification":
                for notif_key, notif_value in value.items():
                    setattr(config.notification, notif_key, notif_value)
            else:
                setattr(config, key, value)
    return config
