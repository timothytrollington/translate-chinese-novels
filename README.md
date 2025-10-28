# Translate Chinese Novels Automation

This repository provides an automated pipeline that discovers newly released
chapters for a Chinese web novel, translates them, and keeps a changelog of
updates. The workflow can be executed locally or on a schedule via GitHub
Actions.

## Features

- Periodic job discovers new chapters from a JSON table of contents.
- Only chapters that have not been processed previously are downloaded.
- Translated chapters are saved to `data/output/` and tracked in
  `data/metadata/chapters.json`.
- A changelog is maintained automatically, and notifications are written to
  `data/notifications.log` (with optional email support).

## Running locally

```bash
python -m pip install -e .
./scripts/update_translations.py --log-level INFO
```

Environment variables can adjust the behaviour:

- `TOC_SOURCE`: Path or URL to the table-of-contents JSON.
- `OUTPUT_DIR`: Where translated chapters are stored.
- `METADATA_PATH`: File that stores processed chapter metadata.
- `CHANGELOG_PATH`: Location of the changelog.
- `TRANSLATION_ENGINE`: Use `noop` (default) or `mock`.
- `NOTIFY_ENABLED`: Set to `0` to disable notifications.
- `NOTIFY_EMAILS`: Comma-separated list of recipients.
- `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`,
  `SMTP_USE_TLS`: Email delivery configuration.

## GitHub Actions schedule

A GitHub Actions workflow is included to execute the update script every day at
midnight UTC. Secrets such as API keys or SMTP credentials should be stored in
the repository settings and referenced via environment variables.
