"""Notification helpers for the translation pipeline."""
from __future__ import annotations

from email.message import EmailMessage
from pathlib import Path
from typing import Iterable
import logging
import smtplib

from .config import NotificationConfig

LOGGER = logging.getLogger(__name__)


def notify_updates(
    config: NotificationConfig,
    messages: Iterable[str],
) -> None:
    """Persist notifications locally and optionally send emails."""

    messages = list(messages)
    if not messages:
        LOGGER.info("No new chapters to notify about")
        return

    if config.enabled:
        _write_log(config.log_path, messages)
        if config.email_recipients and config.smtp_server:
            _send_email(config, messages)
    else:
        LOGGER.debug("Notifications disabled; skipping log and email")


def _write_log(path: Path, messages: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        for message in messages:
            fh.write(message + "\n")
    LOGGER.info("Wrote %d notification(s) to %s", len(messages), path)


def _send_email(config: NotificationConfig, messages: list[str]) -> None:
    email = EmailMessage()
    email["Subject"] = "New translated chapters available"
    email["From"] = config.smtp_username or "translator@localhost"
    email["To"] = ", ".join(config.email_recipients)
    email.set_content("\n".join(messages))

    try:
        if config.use_tls:
            with smtplib.SMTP(config.smtp_server, config.smtp_port) as server:
                server.starttls()
                if config.smtp_username and config.smtp_password:
                    server.login(config.smtp_username, config.smtp_password)
                server.send_message(email)
        else:
            with smtplib.SMTP(config.smtp_server, config.smtp_port) as server:
                if config.smtp_username and config.smtp_password:
                    server.login(config.smtp_username, config.smtp_password)
                server.send_message(email)
        LOGGER.info("Sent notification email to %s", config.email_recipients)
    except Exception as exc:  # pragma: no cover - log and continue
        LOGGER.warning("Failed to send notification email: %s", exc)
