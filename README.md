# Translate Chinese Novels

This project bootstraps a translation workflow that can use either hosted APIs or local models. The default configuration targets the OpenAI Responses API, but you can swap in alternatives by editing `config/translation_config.yaml`.

## 1. Choose translation approach

Set the `approach` key in `config/translation_config.yaml` to either `api` or `local`.

```yaml
approach: api  # options: api, local
```

The file also defines:

- API providers (OpenAI or DeepL) and model metadata
- Local model information (default: `Helsinki-NLP/opus-mt-zh-en`)
- Batch sizes and character limits
- Rate-limiting and retry behaviour
- Caching backend and persistence options

## 2. Create a Python virtual environment

Use the helper script to create and populate a virtual environment with the required dependencies:

```bash
./scripts/create_venv.sh
```

The script installs:

- `transformers`
- `sentencepiece`
- `pandas`
- `python-dotenv`
- `openai`
- `requests`
- `PyYAML`

## 3. Store API keys securely

Copy `.env.example` to `.env` and populate the environment variables with your credentials. The application loads them with `python-dotenv` at runtime.

```bash
cp .env.example .env
# edit .env with your API keys
```

Alternatively, export the variables directly in your shell or rely on a secret manager; the code checks `os.environ` first.

## 4. Run translations via configuration

The `Translator` class in `src/translator.py` reads the configuration and chooses between API-based or local translation automatically. For example, to translate a CSV file with a `text` column:

```bash
python -m src.translator \
  --input data/source.csv \
  --output data/translated.csv \
  --config config/translation_config.yaml
```

You can also import `Translator` in your own scripts:

```python
from pathlib import Path
from src.translator import Translator

translator = Translator.from_config_path(Path("config/translation_config.yaml"))
translations = translator.translate(["待翻译的文本"])
```

Remember to respect the rate limits defined in the configuration file when orchestrating batch jobs.
