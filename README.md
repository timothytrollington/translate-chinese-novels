# Translate Chinese Novels

This repository organizes tooling for collecting, translating, and curating Chinese web novels for personal study. Follow the instructions below to set up your environment, run the translation workflow, and keep your tools up to date.

## Project Structure

```
.
├── data/
│   ├── raw_cn/           # Original Chinese text sources (never commit scraped data)
│   └── en_translated/    # Generated English translations for personal study
├── logs/                 # Runtime logs, audit trails, and debugging output
├── notebooks/            # Optional exploration notebooks
├── src/
│   └── translate_chinese_novels/
│       ├── __init__.py
│       ├── config.py
│       └── pipeline.py
└── README.md
```

Create any additional domain-specific modules or notebooks under `src/` or `notebooks/` as needed. Keep scraped or translated data out of version control.

## Setup

1. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies (update `requirements.txt` as the project grows):

   ```bash
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and fill in API keys or credentials if needed by your translation provider.

## Translation Workflow

1. Place the original chapters (UTF-8 encoded) inside `data/raw_cn/`.
2. Configure translation options in `src/translate_chinese_novels/config.py` (e.g., batch size, API endpoints, rate limits).
3. Run the translation pipeline:

   ```bash
   python -m translate_chinese_novels.pipeline translate --input data/raw_cn --output data/en_translated
   ```

4. Inspect the generated English chapters in `data/en_translated/` and keep only the files you need for personal study.

5. Check logs under `logs/` for error messages, retries, or throttling notices.

## Updating and Maintenance

* Update dependencies regularly:

  ```bash
  pip install --upgrade -r requirements.txt
  ```

* Refresh cached translations or rerun chapters with improved prompts:

  ```bash
  python -m translate_chinese_novels.pipeline refresh --input data/raw_cn --output data/en_translated
  ```

* Keep notebooks synchronized:

  ```bash
  jupyter lab
  ```

## Responsible Use

* Scrape or download content only in full compliance with the source site's terms of service.
* Respect robots.txt, rate limits, and any explicit usage policies.
* Limit all translated material to personal study and do not redistribute without permission.

## Roadmap & Desired Enhancements

* Reader UI with chapter bookmarking and synchronized bilingual view.
* Full-text search across translated chapters with metadata filters.
* Experimentation with fine-tuned translation or summarization models tailored to specific authors.
* Automated QA checks for terminology consistency and honorific handling.

Contributions are welcome via pull requests that adhere to the responsible use guidelines above.
