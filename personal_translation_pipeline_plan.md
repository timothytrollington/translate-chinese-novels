# Martial God Asura Personal Translation Pipeline Plan

## Phase 1. Environment Setup and Repository Structure
1. **Tasks**
   - Install Python 3.11+, Node.js (optional for alternative tooling), and Git on macOS/Windows/Linux.
   - Create a dedicated virtual environment (`python -m venv .venv`) and install core packages: `requests`, `httpx`, `beautifulsoup4`, `lxml`, `playwright` (for scripted browsing), `pydantic`, `sqlalchemy`, `datasets`, `typer`, `rich`.
   - Add translation tooling dependencies: `openai`, `transformers`, `accelerate`, `sentencepiece`, `sacremoses`, `spacy`, `language-tool-python`, `pandas`, `numpy`.
   - Initialize directory layout:
     ```
     project_root/
       data/
         raw/
         translated/
         metadata/
       src/
         scraper/
         translator/
         quality/
         utils/
       configs/
       notebooks/
     ```
   - Configure `.env` for API keys (OpenAI, DeepL, Azure, etc.) using `python-dotenv`.
2. **Recommended Tools/Libraries**: Python, `pip-tools` or `poetry` for dependency management, VS Code or PyCharm, `pre-commit` for linting, `ruff`/`black`.
3. **Success Criteria**: Reproducible environment created; project skeleton committed to Git; dependencies install without errors; `.env.example` documented.

## Phase 2. Site Reconnaissance and Access Strategy
1. **Tasks**
   - Inspect 17k.com site structure manually and with developer tools to identify chapter listing API/HTML patterns (e.g., chapter list pagination, AJAX endpoints).
   - Use `playwright` scripted session to determine if login is required; capture cookies if necessary with session storage; respect robots.txt and TOS for personal use.
   - Determine rate limiting by timing manual requests; plan 1–2 req/sec throttle with exponential backoff.
   - Map chapter metadata schema: chapter id, number, title, volume, release datetime, word count, URLs.
2. **Recommended Tools**: Browser dev tools, `playwright codegen`, `httpx.AsyncClient`, `tenacity` for retry logic.
3. **Success Criteria**: Documented endpoints and necessary headers/cookies; defined metadata schema; confirmed access without triggering anti-bot measures.

## Phase 3. Metadata and Content Fetching Pipeline
1. **Tasks**
   - Implement `src/scraper/client.py` using `httpx.AsyncClient` with rotating headers, optional cookie injection, and rate limiter via `asyncio.Semaphore`.
   - Build `ChapterIndexFetcher` to crawl volume/chapter lists, storing metadata in `data/metadata/chapters.parquet`.
   - Implement `ChapterContentFetcher` to retrieve HTML for each chapter, parse with `BeautifulSoup`/`lxml`, extract title, author notes, body paragraphs, and inline images.
   - Normalize whitespace, convert `<br>` to paragraph separators, and store raw Chinese text in JSONL: `{id, title, volume, published_at, url, body_paragraphs}`.
   - Persist HTML snapshots for traceability (`data/raw/html/{chapter_id}.html`).
2. **Recommended Tools**: `asyncio`, `sqlalchemy` or DuckDB for metadata, `pandas`.
3. **Success Criteria**: All chapters from 1..current scraped and saved; rerun yields no duplicates; logging traces rate limiting events.

## Phase 4. Data Storage and Versioning
1. **Tasks**
   - Choose storage backend: local SQLite/DuckDB for metadata, file-based JSONL/Parquet for text; optionally integrate with `datasets.Dataset`.
   - Implement `src/utils/storage.py` with CRUD helpers and hashing to detect changes.
   - Version raw data using DVC or Git LFS for large files; maintain `data/README.md` documenting formats.
2. **Recommended Tools**: DuckDB, DVC, Git LFS, `pydantic` models for validation.
3. **Success Criteria**: Raw text and metadata queryable; integrity checks pass; hash-based deduping prevents duplicate chapters.

## Phase 5. Translation Engine Integration
1. **Tasks**
   - Evaluate translation providers: OpenAI GPT-4.1, GPT-4o, Claude 3 Opus/Sonnet via API, DeepL, or local models (`Helsinki-NLP/opus-mt-zh-en`, `Qwen2-7B` fine-tuned) via `transformers` + GPU.
   - Implement modular translator interface (`src/translator/base.py`) with pluggable backends and rate limit handling.
   - Design batching: group paragraphs into <=2,000 Chinese characters; stream results; include context (previous paragraph) in prompt template for coherence.
   - Craft prompt template for LLMs highlighting requirements: faithful translation, preserve names, maintain paragraph alignment, mark sound effects.
   - Add glossary support via JSON dictionary applied pre/post translation.
   - Cache translations using SQLite (`translations.db`) keyed by chapter+paragraph hash.
2. **Recommended Tools**: `asyncio`, `openai` SDK, `anthropic`, `litellm` for unified API, `backoff` for retries.
3. **Success Criteria**: Batch translation pipeline translates all stored Chinese text; outputs stored in `data/translated/{chapter_id}.json`; caching prevents retranslation on reruns.

## Phase 6. Formatting and Post-processing
1. **Tasks**
   - Preserve paragraph boundaries; convert dialogue markers to English quotation style; handle ellipses and em dashes.
   - Reconstruct chapters into Markdown/EPUB-friendly format with metadata header.
   - Normalize punctuation via custom rules (e.g., replace full-width punctuation) and run language quality checks with `language-tool-python`.
   - Align author notes and footnotes; embed inline images or provide references.
2. **Recommended Tools**: `markdown-it-py`, `ebooklib` (for EPUB), custom regex utilities.
3. **Success Criteria**: Translated files readable in Markdown/EPUB; formatting matches original paragraph structure; QA scripts show minimal grammatical warnings.

## Phase 7. Quality Evaluation and Iterative Refinement
1. **Tasks**
   - Sample chapters for bilingual review; compare with community translations if available for benchmarking.
   - Implement automatic metrics: BLEU with reference snippets, COMET (requires references), or cross-lingual consistency checks.
   - Collect reviewer feedback, update glossary, adjust prompt instructions (e.g., tone guidance, honorific handling).
   - Maintain `notebooks/qa.ipynb` for experiments evaluating different prompts/models.
2. **Recommended Tools**: `sacrebleu`, `comet-ml`, `spacy` NER for name consistency, `typer` CLI for prompt experimentation.
3. **Success Criteria**: Documented QA findings; iterative improvements increase subjective and metric-based quality; glossary and prompt versions tracked in Git.

## Phase 8. Update Automation
1. **Tasks**
   - Implement `src/scraper/update_checker.py` to poll chapter index daily/weekly; compare latest chapter id/timestamp with stored metadata.
   - Schedule job via OS scheduler (`cron`, Windows Task Scheduler) or Python daemon using `APScheduler`.
   - Automatically fetch new chapters, translate, and append to datasets; send desktop/email notification upon completion.
   - Ensure idempotency by hashing raw content; skip if unchanged.
2. **Recommended Tools**: `APScheduler`, `typer` CLI command `python -m cli update`.
3. **Success Criteria**: Running update command only processes new chapters; log records of updates stored; notifications confirmed.

## Phase 9. Documentation and Personal-Use Safeguards
1. **Tasks**
   - Document personal-use policy reminders in `docs/legal.md`; include notes on not redistributing raw or translated text.
   - Provide `README` with usage instructions, environment setup, and update workflow.
   - Log API usage costs in `data/metadata/api_usage.csv`; set budget alerts.
2. **Recommended Tools**: Markdown documentation, cost trackers (OpenAI usage dashboard), `rich` logging.
3. **Success Criteria**: Documentation enables rerun by future self; compliance reminders explicit; cost monitoring in place.

## Phase 10. Optional Enhancements
1. **Glossary Management**: Build interface (streamlit app) to curate character/place names and enforce via preprocessing hook.
2. **Custom Model Fine-tuning**: Collect bilingual corpus and fine-tune `Qwen2` or `Mistral` using LoRA; evaluate improvements.
3. **Reading UI**: Develop Electron/Next.js or Streamlit reader with search, bookmarks, and side-by-side CN/EN.
4. **Audio Generation**: Integrate TTS (e.g., ElevenLabs, Azure) to produce narrated chapters for personal use.
5. **Version Diffing**: Implement diff viewer to compare translations across model iterations.

## Risk Assessment and Mitigations
- **Anti-scraping Defenses**: Use human-like headers, respect crawl delay, rotate between synchronous and asynchronous requests, and fall back to Playwright-controlled browser if HTML obfuscated.
- **Site Structure Changes**: Implement schema versioning; unit tests for parsers; monitor failed parse logs.
- **API Rate Limits/Costs**: Implement throttling; cache results; set daily quota caps; evaluate local models for bulk translation to reduce cost.
- **Data Loss**: Automate backups to encrypted external drive/cloud storage with client-side encryption (e.g., `rclone` + Crypt).
- **Translation Quality Drift**: Version prompts and models; keep QA benchmarks; schedule periodic re-evaluation.
- **Legal Considerations**: Restrict usage to personal use; secure data; avoid sharing translations publicly; respect site TOS.

## Milestone Timeline (Suggested)
1. **Week 1**: Complete Phases 1–3 (environment, scraping, raw storage).
2. **Week 2**: Finish Phases 4–6 (data storage, translation integration, formatting).
3. **Week 3**: Implement Phases 7–9 (QA, automation, documentation).
4. **Ongoing**: Apply optional enhancements and risk mitigation reviews quarterly.

